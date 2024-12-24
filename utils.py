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

from datetime import datetime, timezone

def format_timestamp(time_seconds: float) -> str:
    tz = timezone.utc
    dt = datetime.fromtimestamp(time_seconds, tz=tz)
    formatted_time = dt.strftime('%Y-%m-%d %I:%M %p')
    return f'{formatted_time} {tz.tzname(dt)}'