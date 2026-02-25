from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
import uuid
import os
from backend.core.vector_store import get_vector_store, source_exists

def process_pdf(file_path: str, filename: str):
    if source_exists(filename):
        return "already_indexed"
        
    loader = PyMuPDFLoader(file_path)
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(docs)
    
    doc_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    for split in splits:
        split.metadata.update({
            "source": filename,
            "filename": filename,
            "upload_timestamp": timestamp,
            "document_id": doc_id,
            "source_type": "pdf"
        })
        
    vector_store = get_vector_store()
    vector_store.add_documents(splits)
    
    return doc_id
