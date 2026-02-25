import os
import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

def get_vector_store():
    if "CHROMA_PERSIST_DIR" in st.secrets:
        persist_directory = st.secrets["CHROMA_PERSIST_DIR"]
    else:
        persist_directory = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
        
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY")),
        task_type="retrieval_document"
    )
    vector_store = Chroma(
        collection_name="pkaa_collection",
        embedding_function=embeddings,
        persist_directory=persist_directory
    )
    return vector_store

def delete_source(source_name: str):
    vector_store = get_vector_store()
    docs = vector_store.get(where={"source": source_name})
    if docs["ids"]:
        vector_store.delete(ids=docs["ids"])
    return len(docs["ids"])

def source_exists(source_name: str):
    vector_store = get_vector_store()
    docs = vector_store.get(where={"source": source_name}, limit=1)
    return len(docs["ids"]) > 0

def wipe_vector_store():
    vector_store = get_vector_store()
    vector_store.delete_collection()
    return True
