import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()

async def clarify_and_store(query):
    questions = await manager.get_clarifying_questions(query)
    return gr.update(choices=questions, visible=True), query

async def run_full_research(user_answers, original_query):
    refined_query = manager.refine_query_with_answers(original_query, user_answers)
    chunks = []
    async for chunk in manager.run(refined_query):
        chunks.append(chunk)
    return "\n\n".join(chunks)

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research Tool with Clarification")

    query_textbox = gr.Textbox(label="What topic would you like to research?")
    clarify_button = gr.Button("Clarify Query", variant="secondary")
    clarification_box = gr.CheckboxGroup(label="Please answer the following questions:", choices=[], visible=False)
    original_query_state = gr.State()

    run_button = gr.Button("Run Full Research", variant="primary")
    report_output = gr.Markdown(label="Research Report")

    clarify_button.click(
        clarify_and_store,
        inputs=query_textbox,
        outputs=[clarification_box, original_query_state],
    )

    run_button.click(
        run_full_research,
        inputs=[clarification_box, original_query_state],
        outputs=report_output
    )

ui.launch(inbrowser=True)
