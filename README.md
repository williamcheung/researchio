# Researchio Deployment Guide

## Create the `.env` file

- Copy the `.env.sample` file to a new file named `.env`.

- Edit the `.env` file and update the placeholder environment variable values ("xxx", etc.) with real values.

- Get the values below by signing up for Pinecone here:
    - https://app.pinecone.io
```env
PINECONE_API_KEY=xxx
PINECONE_HOST=xxx (host of the index you create to store the data, using 1536 as the index dimension, see `Load Dataset to Pinecone` below)
PINECONE_INDEX_NAME=xxx (part of PINECONE_HOST.)
```

- Get the values below by signing up for OpenAI here:
    - https://platform.openai.com
```env
OPENAI_EMBEDDING_API_KEY=xxx
OPENAI_API_KEY=xxx
```

- Get the value below by signing up for Lambda here:
    - https://lambdalabs.com
```env
OPENAI_API_KEY2=xxx
```

- Get the value below by signing up for MongoDB here:
    - https://www.mongodb.com/cloud/atlas/register
```env
MONGODB_ATLAS_CLUSTER_URI=mongodb+srv://xxx:yyy@zzz
```

- Save your changes to the `.env` file.

## Run the app

Install Python 3.12 or above.

Install the app dependencies:
```bash
pip install -r requirements.txt
```

Run the app:
```bash
python gradio_ui.py
```

## Dataset Prep

- Use a web scraping script to scrape the research articles you want to use as the dataset of the app.
- Output the scraped results to a JSONL file `research_pubs.jsonl` with each line having these properties:
    - url
    - published_at
    - title
    - contents
- Put `research_pubs.jsonl` in the project's `data` directory.

## Dataset Load to Pinecone

- In Pinecone create an index, using 1536 as the index dimension.
- Copy the host URL of the index and use it to set `PINECONE_HOST` and `PINECONE_INDEX_NAME` in the `.env` file.
- Load the dataset to the index by running:
```bash
python pinecone_loader.py
```

## Titles File Generation

Generate the titles file `db/articles.jsonl`, which is used to load the list of article titles in the UI, by running:
```bash
python build_title_db.py
```
