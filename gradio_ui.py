import gradio as gr
import json
import re

from pinecone_rag import ask_question
from typing import Generator

APP_NAME = 'Researchio'
TITLE = f'{APP_NAME} Bot'

MIN_YEAR = 2021
ALL_TITLES_INDICATOR = '[All]'

# load titles
file_path = 'db/articles.jsonl'

def _extract_titles() -> list[str]:
    def generate_unique_titles() -> Generator[str, None, None]:
        '''
        Generates unique, cleaned titles from the articles JSONL file, yielding one title at a time.

        Yields:
            Unique, cleaned titles, one at a time (str).

            Receives:
                None. The generator does not accept sent values.

            Returns:
                None. The generator does not return a specific value upon completion.
        '''
        seen_titles = set()
        with open(file_path, 'r', encoding='UTF-8') as f:
            for line in f:
                data = json.loads(line)
                original_title = data['title']
                cleaned_title = re.sub(r'^[^a-zA-Z]+', '', original_title).strip().replace('\n', ' ')

                if cleaned_title not in seen_titles:
                    seen_titles.add(cleaned_title)
                    yield cleaned_title

    titles = list(generate_unique_titles())
    titles.insert(0, ALL_TITLES_INDICATOR)
    titles.sort(key=str.lower)
    return titles

titles = _extract_titles()
num_titles = len(titles)-1

bulletpt = '\u2022'
nbsp = '\u00A0'

GREETING = \
f'''
Welcome to 🩺❤️ <b>{APP_NAME}!</b> ❤️🩺

Ask any question about the {num_titles:,} medical research articles in my AI database retrieved from these curated public sites:
{bulletpt} [MDPI](https://www.mdpi.com){nbsp}{nbsp}{nbsp}{bulletpt} [Dove Medical Press](https://www.dovepress.com){nbsp}{nbsp}{nbsp}{bulletpt} [Taylor & Francis](https://www.tandfonline.com){nbsp}{nbsp}{nbsp}{bulletpt} [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc)

You can also ask about a specific article by choosing a <i>title</i> from the list. All articles are from {MIN_YEAR} to this year. Enjoy researching! 🍎📅
'''.strip()

# send_button click handler
def submit_message(message: str, title: str, history: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    if message:
        print(f'[title]: {title} [question]: {message}')

        filter = {}
        if title and title != ALL_TITLES_INDICATOR:
            filter = {'title': title}

        answer = ask_question(message, filter)
        history.append((message, answer))
    return history, '' # '' clears the input text box

# retry_button click handler
def retry_message(title: str, history: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    if history:
        last_message: str = history[-1][0]
        return submit_message(last_message, title, history[:-1] if len(history) > 1 else history)
    return history, ''

# undo_message click handler
def undo_message(history: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    if history:
        return history[:-1] if len(history) > 1 else history, ''
    return history, ''

# clear_button click handler
def clear_messages() -> tuple[list[tuple[str, str]], str, str]:
    return [(None, GREETING)], '', None

with gr.Blocks(title=TITLE, theme='ocean', css='''
    footer {visibility: hidden}

    /* for dropdown icon: increase size, make colour stronger */
    .wrap-inner .icon-wrap svg {
        width: 48px !important;
        height: 48px !important;
        fill: #0077b6 !important;
    }

    /* remove clear button in chatbot */
    button[aria-label="Clear"] {
        display: none !important;
    }
            ''') as demo:
    gr.Markdown(F'<h1 style="text-align:center;">{TITLE}</h1>')

    chatbot = gr.Chatbot(
        label='R.Bot',
        height='65vh',
        show_copy_button=True,
        value=[(None, GREETING)]
    )

    with gr.Row(variant='panel'):
        with gr.Column(scale=6):
            msg = gr.Textbox(autofocus=True, label='Question?', lines=4)
        with gr.Column(scale=2):
            title_dropdown = gr.Dropdown(label=f'Title {nbsp}{nbsp}{nbsp}(type-ahead supported :)', choices=titles)
            send_button = gr.Button('Research It! 📚')

    with gr.Row():
        retry_button = gr.Button('Retry')
        undo_button = gr.Button('Undo')
        clear_button = gr.Button('Clear')

    gr.HTML(
        '''
        <div id='app-footer' style='text-align: center;'>
            Powered by <a href="https://www.pinecone.io/">Pinecone</a>, <a href="https://platform.openai.com/docs/models#embeddings">OpenAI Embedding</a>, and <a href="https://lambdalabs.com/inference">Llama 3.1 on Lambda Cloud</a>
        </div>
        '''
    )

    send_button.click(submit_message, inputs=[msg, title_dropdown, chatbot], outputs=[chatbot, msg])
    retry_button.click(retry_message, inputs=[title_dropdown, chatbot], outputs=[chatbot, msg])
    undo_button.click(undo_message, inputs=[chatbot], outputs=[chatbot, msg])
    clear_button.click(clear_messages, outputs=[chatbot, msg, title_dropdown])

demo.launch(server_name='0.0.0.0')
