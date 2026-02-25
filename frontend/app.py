import streamlit as st
import requests
import os


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="PKAA - Personal Knowledge AI Agent", layout="wide")

st.title(" PKAA: Personal Knowledge AI Agent")
st.markdown("Your private, persistent AI second brain.")


with st.sidebar:
    st.header(" Ingestion Dashboard")
    
    
    st.subheader(" Upload PDFs")
    uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True, type=['pdf'])
    if st.button("Index PDFs") and uploaded_files:
        with st.spinner("Indexing PDFs..."):
            files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files]
            response = requests.post(f"{BACKEND_URL}/ingest/pdf", files=files)
            if response.status_code == 200:
                st.success("PDFs indexed successfully!")
            else:
                st.error("Failed to index PDFs.")

    st.divider()
    
    
    st.subheader(" Web Ingestion")
    web_url = st.text_input("Enter URL")
    if st.button("Ingest Website") and web_url:
        with st.spinner("Ingesting website..."):
            response = requests.post(f"{BACKEND_URL}/ingest/web", json={"url": web_url})
            if response.status_code == 200:
                st.success("Website indexed!")
            else:
                st.error("Failed to index website.")

    st.divider()
    
    
    st.subheader(" Google Services")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sync Gmail"):
            with st.spinner("Syncing Gmail..."):
                response = requests.post(f"{BACKEND_URL}/sync/gmail")
                if response.status_code == 200:
                    st.success(f"Gmail synced! ({response.json()['emails_processed']} emails)")
                else:
                    st.error("Failed to sync Gmail.")
    with col2:
        if st.button("Sync Drive"):
            with st.spinner("Syncing Drive..."):
                response = requests.post(f"{BACKEND_URL}/sync/drive")
                if response.status_code == 200:
                    st.success(f"Drive synced! ({response.json()['files_processed']} files)")
                else:
                    st.error("Failed to sync Drive.")


st.header(" Chat with your Knowledge Base")

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
             with st.expander("Sources"):
                for source in message["sources"]:
                    st.write(f"- {source}")


if prompt := st.chat_input("Ask me anything about your data..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = requests.post(f"{BACKEND_URL}/chat", json={"query": prompt})
            if response.status_code == 200:
                data = response.json()
                answer = data["answer"]
                sources = data["sources"]
                
                st.markdown(answer)
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.write(f"- {source}")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })
            else:
                st.error("Communication error with backend.")
