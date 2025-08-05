# app.py

from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import gradio as gr
import datetime
import pandas as pd
from pypdf import PdfReader
from collections import defaultdict
import matplotlib.pyplot as plt

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv(override=True)

# ------------------- Tool Functions -------------------
def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"message": f"✅ Recorded user: {name} ({email}) 📬"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"message": f"🤖 I didn't know the answer, but I've saved this question: \"{question}\" 📝"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The user's email"},
            "name": {"type": "string", "description": "User's name"},
            "notes": {"type": "string", "description": "Any context"}
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record unknown questions",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Unanswered question"}
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}
]

# ------------------- Core Class -------------------
class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Michael M"
        self.evaluation_log = []
        self.user_threads = self.load_threads()

        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = "".join([page.extract_text() or "" for page in reader.pages])

        self.summary = open("me/summary.txt", "r", encoding="utf-8").read()
        raw_articles = open("me/articles.txt", "r", encoding="utf-8").read()

        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=20)
        docs = splitter.split_documents([Document(page_content=raw_articles)])
        embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.knowledge_base = Chroma.from_documents(docs, embedding)

    def retrieve_relevant_context(self, query):
        results = self.knowledge_base.similarity_search(query, k=4)
        return "\n---\n".join([r.page_content for r in results])

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            tool = globals().get(tool_name)
            result = tool(**args) if tool else {"message": "❌ Tool not found"}
            results.append({
                "role": "tool",
                "content": result["message"],
                "tool_call_id": tool_call.id
            })
        return results

    def system_prompt(self, rag_context=""):
        prompt = f"You are acting as {self.name}, representing his professional background. "\
                 f"Always stay in character. Use the following background:\n\n"\
                 f"## Summary:\n{self.summary}\n\n"\
                 f"## LinkedIn:\n{self.linkedin}\n"
        if rag_context:
            prompt += f"\n## Retrieved Articles:\n{rag_context}\n"
        return prompt

    def log_evaluation(self, entry):
        entry["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.evaluation_log.append(entry)
        with open("evaluation_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def save_threads(self):
        with open("threads.json", "w", encoding="utf-8") as f:
            json.dump(self.user_threads, f, ensure_ascii=False)

    def load_threads(self):
        if os.path.exists("threads.json"):
            with open("threads.json", "r", encoding="utf-8") as f:
                return defaultdict(list, json.load(f))
        return defaultdict(list)

    def chat(self, message, history, user_id="anonymous"):
        rag_context = self.retrieve_relevant_context(message)
        thread = self.user_threads[user_id]
        messages = [{"role": "system", "content": self.system_prompt(rag_context)}] + thread + [{"role": "user", "content": message}]

        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            stream=False
        )

        finish_reason = response.choices[0].finish_reason
        assistant_message = response.choices[0].message

        tool_responses = []
        if finish_reason == "tool_calls":
            tool_calls = assistant_message.tool_calls
            tool_responses = self.handle_tool_call(tool_calls)
            messages.append(assistant_message)
            messages.extend(tool_responses)

        reply = assistant_message.content
        if not reply:
            reply = "🤖 I'm not sure how to answer that yet, but I've saved your question for review. 👍"

        # Update persistent history
        self.user_threads[user_id].append({"role": "user", "content": message})
        self.user_threads[user_id].append({"role": "assistant", "content": reply})
        self.save_threads()

        self.log_evaluation({
            "user_id": user_id,
            "question": message,
            "response": reply,
            "context": rag_context
        })

        return reply

# ------------------- Dashboard -------------------
def launch_dashboard():
    def load_logs():
        if not os.path.exists("evaluation_log.jsonl"):
            return pd.DataFrame(columns=["timestamp", "user_id", "question", "response", "context"])
        with open("evaluation_log.jsonl", "r", encoding="utf-8") as f:
            return pd.DataFrame(json.loads(line) for line in f)

    def plot_question_volume(df):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        counts = df['timestamp'].dt.date.value_counts().sort_index()
        plt.figure(figsize=(8, 3))
        counts.plot(kind="bar")
        plt.title("📊 Questions per Day")
        plt.xlabel("Date")
        plt.ylabel("Count")
        plt.tight_layout()
        return plt

    df = load_logs()
    with gr.Column():
        gr.Markdown("### 📋 Evaluation Log")
        gr.Dataframe(df, interactive=True, label="Logs")
        if not df.empty:
            gr.Plot(plot_question_volume(df))

# ------------------- Launch UI -------------------
if __name__ == "__main__":
    me = Me()
    with gr.Blocks() as demo:
        gr.Markdown("# 🤖 Chat with Michael M\nA personal AI assistant powered by OpenAI + LangChain + Gradio")
        with gr.Row():
            user_id_input = gr.Textbox(label="User ID", value="anonymous")
        chat_ui = gr.ChatInterface(lambda msg, hist: me.chat(msg, hist, user_id_input.value), type="messages")
        with gr.Accordion("📈 Evaluation Logs", open=False):
            launch_dashboard()
    demo.launch()

