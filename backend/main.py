from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
import shutil
import os
from typing import List

load_dotenv()

from backend.core.rag_chain import query_rag
from backend.core.vector_store import delete_source
from backend.ingestion.pdf_loader import process_pdf
from backend.ingestion.web_loader import process_web_url
from backend.ingestion.gmail_loader import process_gmail
from backend.ingestion.drive_loader import process_drive

app = FastAPI(title="Personal Knowledge AI Agent API")

class ChatRequest(BaseModel):
    query: str

class WebIngestRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"status": "PKAA Backend is running"}

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    try:
        response = query_rag(request.query)
        
        answer = response.get("answer", "No answer found.")
        sources = []
        if "source_documents" in response:
            sources = list(set([
                 doc.metadata.get("source", "Unknown")
                 for doc in response["source_documents"]
            ]))
            
        return {"answer": answer, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/pdf")
async def ingest_pdf(files: List[UploadFile] = File(...)):
    results = []
    os.makedirs("temp_uploads", exist_ok=True)
    for file in files:
        temp_path = f"temp_uploads/{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            doc_id = process_pdf(temp_path, file.filename)
            results.append({"filename": file.filename, "status": "indexed", "id": doc_id})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    return {"results": results}

@app.post("/ingest/web")
def ingest_web(request: WebIngestRequest):
    try:
        num_chunks = process_web_url(request.url)
        return {"url": request.url, "status": "indexed", "chunks": num_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/gmail")
def sync_gmail(max_results: int = 10):
    try:
        num_emails = process_gmail(max_results)
        return {"status": "synced", "emails_processed": num_emails}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync/drive")
def sync_drive():
    try:
        num_files = process_drive()
        return {"status": "synced", "files_processed": num_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/docs")
def remove_source(source: str):
    """Remove a source (filename or URL) from the vector store."""
    try:
        num_deleted = delete_source(source)
        return {"source": source, "status": "deleted", "chunks_removed": num_deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
