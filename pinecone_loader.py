from dotenv import load_dotenv
load_dotenv()

import os
import json
import threading

from pinecone import Pinecone
from unidecode import unidecode
from unstructured.chunking.basic import chunk_elements
from unstructured.embed.openai import OpenAIEmbeddingConfig, OpenAIEmbeddingEncoder
from unstructured.partition.text import partition_text

DATA_FILE = 'data/research_pubs.jsonl'
UTF_8_ENCODING = 'utf-8'
MIN_YEAR = 2021

embedding_encoder = OpenAIEmbeddingEncoder(config=
    OpenAIEmbeddingConfig(api_key=os.getenv('OPENAI_EMBEDDING_API_KEY'), model_name=os.getenv('OPENAI_EMBEDDING_MODEL')))

pc = Pinecone()
index = pc.Index(host=os.getenv('PINECONE_HOST'))
index_stats_response = index.describe_index_stats()
print(f'index stats: {index_stats_response}')

def load_to_vector_store(title: str, src: str, published_at: str, text: str) -> None:
    elements = partition_text(text=unidecode(text))
    chunks = chunk_elements(elements, max_characters=40_000) # avoid exceed max metadata size 40960 bytes per vector & max message size 4194304 bytes

    if not _invoke_embedding_in_thread(chunks):
        print('Retry embedding...')
        _invoke_embedding_in_thread(chunks, abort=True)

    total_embeddings = sum(len(chunk.embeddings) for chunk in chunks)
    print(f'Extracted {len(chunks)} chunks, {total_embeddings=} for {src=}')
    _add_to_pinecone(title, src, published_at, chunks)

def _invoke_embedding_in_thread(chunks, abort=False, timeout=120) -> bool:
    success = False

    def target():
        nonlocal success
        try:
            embedding_encoder.embed_documents(chunks)
            success = True

        except Exception as e:
            print(f'Error embedding chunks: {e}')

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        err = f'Error: embedding timed out after {timeout} seconds.'
        print(err)
        # thread probably will be orphaned now
        if abort:
            raise Exception(err)

    return success

def _add_to_pinecone(title: str, src: str, published_at: str, chunks: list) -> None:
    vectors = [
        {
            'id': f'{src}|{i}',
            'values': chunk.embeddings,
            'metadata': {
                'title': title,
                'src': src,
                'published_at': published_at if published_at else str(MIN_YEAR),
                'text': chunk.text
            }
        } for i, chunk in enumerate(chunks, start=1)
    ]

    try:
        rsp = index.upsert(vectors=vectors)
        print(f'index: {rsp}')

    except Exception as e:
        print(f'Error upserting vectors to index: {e}')

        if 'exceeds the maximum supported size' in str(e): # request max size 2MB
            print('Split vectors and retry...')
            mid = len(vectors) // 2
            rsp = index.upsert(vectors=vectors[:mid])
            print(f'index: {rsp}')
            rsp = index.upsert(vectors=vectors[mid:])
            print(f'index: {rsp}')

        elif 'exceeds the limit of 40960 bytes per vector' in str(e): # metadata max size 40960 bytes per vector
            print('Upsert vectors one by one...')
            for i, vector in enumerate(vectors):
                try:
                    rsp = index.upsert(vectors=[vector])
                    print(f'index: {rsp}')
                except Exception as e:
                    print(f'Error upserting vector[{i}] of total {len(vectors)} to index: {e}')
                    print(f"Error vector: {vector['id']=} {vector['metadata']=}")
                    raise

        else:
            raise

if __name__ == '__main__':
    START_LINE = 1

    with open(DATA_FILE, 'r', encoding=UTF_8_ENCODING) as data_file:
        for i, line in enumerate(data_file, start=1):
            if i < START_LINE:
                continue
            print(f'Processing line {i} ...')

            jsonl: dict = json.loads(line)
            url: str = jsonl['url']
            published_at: str = jsonl.get('published_at')
            title: str = jsonl['title']
            contents: str = jsonl['contents']
            load_to_vector_store(title, url, published_at, contents)
