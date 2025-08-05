from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import datetime

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import pandas as pd
from collections import defaultdict

load_dotenv(override=True)

# Notification tools
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
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}
]

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Michael M"
        self.evaluation_log = []
        self.user_threads = defaultdict(list)

        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text

        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

        with open("me/articles.txt", "r", encoding="utf-8") as f:
            raw_articles = f.read()

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
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results

    def system_prompt(self, rag_context=""):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool."

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        if rag_context:
            system_prompt += f"\n## Additional Relevant Articles (RAG):\n{rag_context}\n"

        system_prompt += f"\nWith this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def log_evaluation(self, entry):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry["timestamp"] = timestamp
        self.evaluation_log.append(entry)
        with open("evaluation_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def chat(self, message, history, user_id="anonymous"):
        rag_context = self.retrieve_relevant_context(message)
        messages = [{"role": "system", "content": self.system_prompt(rag_context)}] + history + [{"role": "user", "content": message}]

        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            stream=False
        )

        finish_reason = response.choices[0].finish_reason
        full_response = response.choices[0].message.content or ""

        self.user_threads[user_id].append({"user": message, "bot": full_response})

        self.log_evaluation({
            "user_id": user_id,
            "question": message,
            "response": full_response,
            "context": rag_context
        })

        if finish_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls
            results = self.handle_tool_call(tool_calls)
            messages.append(response.choices[0].message)
            messages.extend(results)

        return full_response

def launch_dashboard():
    def load_logs():
        if not os.path.exists("evaluation_log.jsonl"):
            return pd.DataFrame(columns=["timestamp", "user_id", "question", "response", "context"])
        with open("evaluation_log.jsonl", "r", encoding="utf-8") as f:
            data = [json.loads(line) for line in f.readlines()]
        return pd.DataFrame(data)

    df = load_logs()
    return gr.Dataframe(df, label="Evaluation Log", interactive=True)

if __name__ == "__main__":
    me = Me()
    with gr.Blocks() as demo:
        gr.Markdown("# Michael M – Chat + Evaluation Log Dashboard")
        with gr.Row():
            user_id_input = gr.Textbox(label="User ID", value="anonymous")
        chat_ui = gr.ChatInterface(lambda msg, hist: me.chat(msg, hist, user_id_input.value), type="messages")
        with gr.Accordion("Evaluation Logs", open=False):
            launch_dashboard()
    demo.launch(ssr_mode=False)
