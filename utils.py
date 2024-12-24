UTF8_ENCODING = 'utf-8'

def load_prompt(prompt_file: str) -> str:
    with open(f'prompts/{prompt_file}', 'r', encoding=UTF8_ENCODING) as f:
        return f.read()

from dotenv import load_dotenv
load_dotenv()

import os

DUMMY_IP_ADDRESS = os.getenv('DUMMY_IP_ADDRESS')

def get_ip_address(request) -> str:
    headers = request.headers
    print(f'{headers}')
    ip_address: str = headers.get('x-forwarded-for', DUMMY_IP_ADDRESS)
    return ip_address
