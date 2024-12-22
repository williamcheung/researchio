import json
import os

from pinecone_loader import DATA_FILE, UTF_8_ENCODING

OUT_DIR = 'db'
OUT_FILE = f'{OUT_DIR}/articles.jsonl'

os.makedirs(OUT_DIR, exist_ok=True)

if __name__ == '__main__':

    with open(DATA_FILE, 'r', encoding=UTF_8_ENCODING) as data_file, open(OUT_FILE, 'w', encoding=UTF_8_ENCODING) as out_file:
        for i, line in enumerate(data_file, start=1):

            jsonl: dict = json.loads(line)
            url: str = jsonl['url']
            published_at: str = jsonl.get('published_at')
            title: str = jsonl['title']
            authors: str = jsonl['authors']

            out_file.write(json.dumps({
                'url': url,
                'published_at': published_at,
                'title': title,
                'authors': authors
            }, ensure_ascii=False))
            out_file.write('\n')
