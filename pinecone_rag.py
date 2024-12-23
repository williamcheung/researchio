from dotenv import load_dotenv
load_dotenv()

import os

from langchain_community.vectorstores import Pinecone
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from utils import load_prompt

PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME')

def ask_question(question: str, filter: dict[str, str]={}, max_docs: int=None) -> str:
    return ask_question_with_prompt_file('question.prompt.txt', question, filter, max_docs)

def ask_question_with_prompt_file(prompt_file: str, question: str, filter: dict[str, str], max_docs: int) -> str:
    vectorstore = Pinecone.from_existing_index(PINECONE_INDEX_NAME,
        OpenAIEmbeddings(api_key=os.getenv('OPENAI_EMBEDDING_API_KEY'), model=os.getenv('OPENAI_EMBEDDING_MODEL'), base_url=os.getenv('OPENAI_EMBEDDING_BASE_URL')))
    search_kwargs = {'filter': filter} if filter else {}
    if max_docs:
        search_kwargs['k'] = max_docs # else default 4
    retriever = vectorstore.as_retriever(search_type='similarity', search_kwargs=search_kwargs)

    # define the RAG prompt
    template = load_prompt(prompt_file)
    prompt = ChatPromptTemplate.from_template(template)

    # define the RAG model
    model = ChatOpenAI(temperature=0, api_key=os.getenv('OPENAI_API_KEY2'),
                       model=os.getenv('OPENAI_MODEL2'), base_url=os.getenv('OPENAI_BASE_URL2'),
                       max_tokens=int(os.getenv('MAX_TOKENS2')))
    chain = _create_rag_chain(retriever, prompt, model)

    print(f'PINECONE RAG Q: {question}')
    try:
        answer = chain.invoke(question)
    except Exception as e:
        print(f'Error: {e}')
        print('Trying other model ...')
        model = ChatOpenAI(temperature=0, api_key=os.getenv('OPENAI_API_KEY'),
                           model=os.getenv('OPENAI_MODEL'), base_url=os.getenv('OPENAI_BASE_URL'),
                           max_tokens=int(os.getenv('MAX_TOKENS')))
        chain = _create_rag_chain(retriever, prompt, model)
        try:
            answer = chain.invoke(question)
        except Exception as e:
            print(f'Error: {e}')
            answer = "Sorry I can't find the answer. Please try asking another question."

    print(f'A: {answer}')
    return answer

def _create_rag_chain(retriever, prompt, model):
    chain = (
        RunnableParallel({'context': retriever, 'question': RunnablePassthrough()})
        | prompt
        | model
        | StrOutputParser()
    )
    chain = chain.with_types(input_type=str)
    return chain

if __name__ == '__main__':
    # test usage
    questions = [
       'Summarize research findings on heart failure.',
       'What are current research findings on heart failure?',
       'What are the latest treatments for COVID-19?',
       'What treatments are there for osteoporosis?',
       'Describe in detail the research in osteoporosis treatments.'
    ]

    for question in questions:
        answer = ask_question(question)
