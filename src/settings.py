import os
from dotenv import load_dotenv
import streamlit as st
from pymongo import MongoClient

load_dotenv()

def get_secret(key: str, default: str | None = None) -> str | None:
    """Busca primeiro nas variáveis de ambiente (.env) e depois nos segredos do Streamlit."""
    val = os.getenv(key)
    if val:
        return val
    
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
        
    return default

class AppSettings:
    def __init__(self):
        self.mistral_api_key: str | None = get_secret("MISTRAL_API_KEY")
        self.chat_model: str = get_secret("CHAT_MODEL", "mistral-small-latest")
        self.hf_token: str | None = get_secret("HF_TOKEN")
        self.mongodb_uri: str | None = get_secret("MONGODB_URI")

        MONGODB_DATABASE = "emporio_da_musica"
        client = MongoClient(self.mongodb_uri)
        db = client[MONGODB_DATABASE]
        self.MONGODB_COLLECTION = db["emporio_da_musica"]
        self.VECTOR_SEARCH_INDEX_NAME = "rag_politicas"

def missing_required_env(settings: AppSettings) -> bool:
    return not bool(settings.mistral_api_key)