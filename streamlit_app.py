import streamlit as st
import os
import sys
import importlib.metadata
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

try:
    import langchain
    import langchain_google_genai
    import langchain_community
    import langchain_core
except ImportError as e:
    st.error(f"Installation Error: {e}")
    st.info("Please try: Manage App > ... > Clear Cache and Deploy")
    st.stop()

from backend.core.rag_chain import query_rag
from backend.core.vector_store import delete_source
from backend.ingestion.pdf_loader import process_pdf
from backend.ingestion.web_loader import process_web_url
from backend.ingestion.gmail_loader import process_gmail
from backend.ingestion.drive_loader import process_drive

st.set_page_config(page_title="PKAA Portfolio Demo", layout="wide")

st.title("PKAA: Personal Knowledge AI Agent")
st.markdown("Connect your PDFs, websites, or Google services to build a private knowledge base.")

with st.sidebar:
    st.header("Ingestion Dashboard")
    
    if st.checkbox("Show System Diagnostics"):
        st.write("---")
        st.write("**Package Versions:**")
        packages = ["streamlit", "langchain", "langchain-google-genai", "langchain-community", "langchain-core", "chromadb"]
        for p in packages:
            try:
                st.write(f"- {p}: {importlib.metadata.version(p)}")
            except:
                st.write(f"- {p}: Not found")
        
        api_key = st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
        if api_key:
            st.write(f"**API Key status:** Found (starts with {api_key[:5]}...)")
            
            if st.button("List Gemini Models"):
                try:
                    genai.configure(api_key=api_key)
                    models = genai.list_models()
                    st.write("**Available Models for your Key:**")
                    for m in models:
                        st.write(f"- `{m.name}`")
                except Exception as e:
                    st.error(f"Discovery Error: {str(e)}")
            
            if st.button("Test Embedding"):
                try:
                    from backend.core.vector_store import get_vector_store
                    vs = get_vector_store()
                    # Try both variants of attribute name
                    emb_fn = getattr(vs, "embedding_function", getattr(vs, "_embedding_function", None))
                    if emb_fn:
                        test_vec = emb_fn.embed_query("test")
                        st.success(f"Embedding successful! Vector size: {len(test_vec)}")
                    else:
                        st.error("Could not find embedding function in Chroma object.")
                except Exception as e:
                    st.error(f"Embedding Error: {str(e)}")

            st.write("---")
            st.write("**Vector Store Status:**")
            try:
                from backend.core.vector_store import get_vector_store, wipe_vector_store
                vs = get_vector_store()
                count = vs._collection.count()
                st.write(f"- Total documents in index: `{count}`")
                
                if st.button("Wipe Database", type="secondary"):
                    wipe_vector_store()
                    st.warning("Database wiped! Please re-index your files.")
                    st.rerun()
            except Exception as e:
                st.write(f"- Vector Store Error: {str(e)}")
        else:
            st.error("**API Key status:** NOT FOUND")
        st.write("---")

    st.subheader("Upload PDFs")
    uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True, type=['pdf'])
    if st.button("Index PDFs") and uploaded_files:
        with st.spinner("Indexing PDFs..."):
            os.makedirs("temp_uploads", exist_ok=True)
            for f in uploaded_files:
                temp_path = f"temp_uploads/{f.name}"
                with open(temp_path, "wb") as buffer:
                    buffer.write(f.getvalue())
                try:
                    result = process_pdf(temp_path, f.name)
                    if result == "already_indexed":
                        st.info(f"'{f.name}' is already indexed.")
                    else:
                        st.success(f"'{f.name}' indexed successfully!")
                except Exception as e:
                    st.error(f"Failed to index '{f.name}': {str(e)}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            st.rerun()

    st.divider()
    
    st.subheader("Web Ingestion")
    web_url = st.text_input("Enter URL")
    if st.button("Ingest Website") and web_url:
        with st.spinner("Ingesting website..."):
            num_chunks = process_web_url(web_url)
            if num_chunks > 0:
                st.success(f"Website indexed! ({num_chunks} chunks)")
            else:
                st.warning("Website already indexed or no content found.")

    st.divider()
    
    st.subheader("Google Services")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sync Gmail"):
            with st.spinner("Syncing Gmail..."):
                try:
                    num_emails = process_gmail()
                    st.success(f"Gmail synced! ({num_emails} emails)")
                except Exception as e:
                    st.error(f"Gmail sync failed: {str(e)}")
    with col2:
        if st.button("Sync Drive"):
            with st.spinner("Syncing Drive..."):
                try:
                    num_files = process_drive()
                    st.success(f"Drive synced! ({num_files} files)")
                except Exception as e:
                    st.error(f"Drive sync failed: {str(e)}")

st.header("Chat with your Knowledge Base")

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
        with st.spinner("Searching and thinking..."):
            try:
                response = query_rag(prompt)
                answer = response.get("answer", "No answer found.")
                sources = list(set([
                    doc.metadata.get("source", "Unknown")
                    for doc in response.get("source_documents", [])
                ]))
                
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
            except Exception as e:
                st.error(f"Error: {str(e)}")
