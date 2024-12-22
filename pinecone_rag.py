from dotenv import load_dotenv
load_dotenv()

import os

from langchain_community.vectorstores import Pinecone
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME')

def ask_question(question: str, filter: dict[str, str]={}, max_docs:int=None) -> str:
    vectorstore = Pinecone.from_existing_index(PINECONE_INDEX_NAME,
        OpenAIEmbeddings(api_key=os.getenv('OPENAI_EMBEDDING_API_KEY'), model=os.getenv('OPENAI_EMBEDDING_MODEL'), base_url=os.getenv('OPENAI_EMBEDDING_BASE_URL')))
    search_kwargs = {'filter': filter} if filter else {}
    if max_docs:
        search_kwargs['k'] = max_docs # else default 4
    retriever = vectorstore.as_retriever(search_type='similarity', search_kwargs=search_kwargs)

    # define the RAG prompt
    template = '''Answer the question based only on the following context:
    {context}
    Question: {question}

    NOTE: If the answer is not found in the context or cannot be inferred from it, say "Sorry I can't find the answer. Please try asking another question."

    In your answer do not give an introduction which has no useful information. Jump directly to the information in your answer without repeating the user's question.

    Do not use long or run-on sentences. Break up your answer into readable, medium length sentences while keeping all relevant details from the context.

    Your answer is for an end user (a health care professional) so do not mention the AI/ML jargon word "context".

    However, do include the "title", "published_at", and "src" metadata fields from the context in your answer using labels "Title", "Published", and "Source" respectively, *BUT ONLY WITH A URL*.
    Put these as footnotes (numbered starting from 1) at the end of your answer so as not to clutter the answer itself. In each footnote put each field on a separate line.
    In the body of your answer you *MUST* refer to an *EXISTING* footnote using the number in square brackets like "[1]". Do not repeat the metadata fields from the footnote in the body of your answer.
    If the footnote does NOT exist, obviously do not refer to it, just mention the title.

    Make "Published" as granular as possible, preferably "YYYY-MM-DD". Reference documents in descending order of publication so that the user reads the latest info first.

    If the "Source" is not a complete URL, you must omit the entire "Source" field. Do not use "Not available".
    References are only needed where an URL is available for the user to click.
   '''

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
