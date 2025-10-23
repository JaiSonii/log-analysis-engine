from langchain_openai import ChatOpenAI
from typing_extensions import Optional
import os

from dotenv import load_dotenv
load_dotenv()
print(os.environ['OPENROUTER_API_KEY'])

def create_open_chat() -> Optional[ChatOpenAI]:
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError('provide OPENROUTER_API_KEY in the environment vairables')
    return ChatOpenAI(
    model='openrouter/andromeda-alpha',
    api_key=lambda: api_key,
    base_url='https://openrouter.ai/api/v1',
    temperature=0.0
)