from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
from backend.core.vector_store import get_vector_store, source_exists

def process_web_url(url: str):
    if source_exists(url):
        return 0
        
    loader = WebBaseLoader(url)
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(docs)
    
    timestamp = datetime.now().isoformat()
    
    for split in splits:
        split.metadata.update({
            "source": url,
            "url": url,
            "ingestion_timestamp": timestamp,
            "source_type": "web"
        })
        
    vector_store = get_vector_store()
    vector_store.add_documents(splits)
    
    return len(splits)
