import gradio as gr
import json
import re

from typing import Generator

from pinecone_rag import ask_question, get_quiz

APP_NAME = 'Researchio'
TITLE = f'{APP_NAME} Bot'

MIN_YEAR = 2021
ALL_TITLES_INDICATOR = '[All]'
UTF_8_ENCODING = 'UTF-8'

CORRECT_ANSWER_SOUND = 'assets/audio/mixkit-correct-answer-reward-952.wav'

# load titles

def _extract_titles() -> list[str]:
    file_path = 'db/articles.jsonl'

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
        with open(file_path, 'r', encoding=UTF_8_ENCODING) as f:
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

# load diseases

def _load_diseases() -> list[str]:
    file_path = 'db/diseases.txt' # should be comma separated list

    with open(file_path, 'r', encoding=UTF_8_ENCODING) as f:
        diseases: str = f.read()
    diseases = diseases.replace('\n', ',')
    diseases: list[str] = diseases.split(',')
    diseases = [d.strip().replace('diseases', 'disease').replace('disorders', 'disorder') for d in diseases if d.strip()]
    diseases.sort()

    unique_diseases: list[str] = ['']
    seen = set()
    for d in diseases:
        d_lower = d.lower()
        if d_lower not in seen:
            unique_diseases.append(d)
            seen.add(d_lower)

    return unique_diseases

diseases = _load_diseases()

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

# disease_dropdown change handler
def lookup_disease(disease: str, history: list[tuple[str, str]]) -> list[tuple[str, str]]:
    if disease:
        print(f'[disease]: {disease}')

        answer = ask_question(f'List all articles about {disease}. Only include articles which have a "src" field (URL). Articles should NOT be numbered.', max_docs=5)
        history.append((f'Quick lookup: **{disease}**', answer))
    return history

# retry_button click handler
def retry_message(title: str, history: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    if history:
        last_message: str = history[-1][0]
        return submit_message(last_message, title, history if len(history) > 1 else history)
    return history, ''

# undo_message click handler
def undo_message(history: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    if history:
        return history[:-1] if len(history) > 1 else history, ''
    return history, ''

# clear_button click handler
def clear() -> tuple[list[tuple[str, str]], str, str, str, dict, dict]:
    return [(None, GREETING)], '', ALL_TITLES_INDICATOR, '', gr.update(visible=False, value=None), {}

# quiz_button click handler
def show_quiz(title: str, history: list[tuple[str, str]], old_quiz: dict) -> tuple[dict, dict, str, dict, list[tuple[str, str]]]:
    if not title or title == ALL_TITLES_INDICATOR:
        history.append(('Quiz me!', 'Please select the **title** of an article to quiz on👇'))
        return gr.update(visible=False), {}, None, None, history

    constraint = ''
    if old_quiz and old_quiz['title'] == title:
        constraint = f'''
You previously asked the reader the following question so try not to ask it again:
"{old_quiz['question']}"
-- But if you must ask it again since you have no other choice, then reword the question.
        '''.strip()

    new_quiz = get_quiz(title, constraint)
    return (gr.update(visible=True),
            new_quiz,
            new_quiz['question'],
            gr.update(choices=new_quiz['choices'], value=None),
            history
    )

# check_button click handler
def submit_answer(selected_choice: str, quiz: dict) -> tuple[dict, str|None]:
    if not selected_choice:
        return None

    orig_choices = quiz['choices']
    correct_answer = quiz['answer']

    marked_choices = []
    marked_selection = selected_choice
    marked = False
    correct = False
    for choice in orig_choices:
        if choice == selected_choice and choice == correct_answer:
            marked_selection = f'☑️{choice}'
            marked_choices.append(marked_selection)
            marked = True
            correct = True
        elif choice == selected_choice and choice != correct_answer:
            marked_selection = f'❌{choice}'
            marked_choices.append(marked_selection)
            marked = True
        else:
            marked_choices.append(choice)

    sound_to_play = CORRECT_ANSWER_SOUND if correct else None

    return (gr.update(choices=marked_choices if marked else orig_choices,
                      value=marked_selection if marked else None),
            sound_to_play
    )

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
        height='55vh',
        show_copy_button=True,
        value=[(None, GREETING)]
    )

    quiz_state = gr.State({})
    correct_sound = gr.Audio(visible=False, autoplay=True)

    with gr.Row(variant='panel'):
        with gr.Column(scale=6):
            msg = gr.Textbox(autofocus=True, label='Question?', lines=7)
        with gr.Column(scale=2):
            title_dropdown = gr.Dropdown(label=f'Title {nbsp}{nbsp}{nbsp}(type-ahead supported :)', choices=titles)
            disease_dropdown = gr.Dropdown(label=f'Quick Lookup {bulletpt} Disease', choices=diseases, interactive=True)
            with gr.Row():
                send_button = gr.Button('Research It! 📚')
                quiz_button = gr.Button('Quiz Me! 🤔')

    with gr.Row(variant='panel', visible=False) as quiz_row:
        with gr.Column(scale=2):
            quiz_question = gr.Textbox(label='Multiple Choice Question', interactive=False, lines=4)
        with gr.Column(scale=6):
            answer_choices = gr.Radio(label='Choices', interactive=True)
            check_button = gr.Button('Submit Answer')

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
    clear_button.click(clear, outputs=[chatbot, msg, title_dropdown, disease_dropdown, quiz_row, quiz_state])

    disease_dropdown.change(
        lookup_disease,
        inputs=[disease_dropdown, chatbot],
        outputs=chatbot
    )

    quiz_button.click(
        show_quiz,
        inputs=[title_dropdown, chatbot, quiz_state],
        outputs=[quiz_row, quiz_state, quiz_question, answer_choices, chatbot]
    )

    check_button.click(
        submit_answer,
        inputs=[answer_choices, quiz_state],
        outputs=[answer_choices, correct_sound]
    )

demo.launch(server_name='0.0.0.0')
