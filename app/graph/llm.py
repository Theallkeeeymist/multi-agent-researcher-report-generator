import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()
critic_llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, api_key = os.getenv("GROQ_API_KEY"))
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=os.getenv("GROQ_API_KEY"))