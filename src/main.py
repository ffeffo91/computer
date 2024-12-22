from langchain_openai import ChatOpenAI
from assistant import SmartAssistant
from tools import (
    add_shopping_list,
    leggi_oroscopo,
    read_shopping_list,
    search_tool
)
import os
from dotenv import load_dotenv

load_dotenv()

# create data folder if not exists
os.makedirs('data', exist_ok=True)
os.makedirs('artifacts', exist_ok=True)

model = ChatOpenAI(
    # api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4"
)

agent = SmartAssistant(
    model=model,
    tools=[add_shopping_list, leggi_oroscopo, read_shopping_list, search_tool],
    db_uri='data/checkpoint.db'
)

agent.run()