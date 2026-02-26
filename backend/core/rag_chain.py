import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from backend.core.vector_store import get_vector_store

system_template = """You are a personal knowledge AI assistant. Only answer using the retrieved context. If the answer is not present, say 'Information not found in your data.' Do not fabricate information.

Context: {context}"""

messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}")
]
qa_prompt = ChatPromptTemplate.from_messages(messages)

user_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

def get_rag_chain():
    api_key = st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY"))
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY")

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            google_api_key=api_key
        )
        vector_store = get_vector_store()
        
        retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 5})
        
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=user_memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            verbose=True
        )
        return chain
    except Exception as e:
        st.error(f"Failed to initialize RAG chain: {str(e)}")
        raise e

def query_rag(query: str):
    try:
        chain = get_rag_chain()
        response = chain.invoke({"question": query})
        return response
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            return {
                "answer": "⚠️ **Quota Exceeded:** You have reached the API limit for today (20 requests/day on the current tier). Please try again tomorrow or check your plan in Google AI Studio.",
                "source_documents": []
            }
        raise e
