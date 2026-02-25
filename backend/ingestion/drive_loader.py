from googleapiclient.discovery import build
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
from backend.core.auth import get_google_credentials
from backend.core.vector_store import get_vector_store
import io
import os
from googleapiclient.http import MediaIoBaseDownload

def fetch_drive_files():
    creds = get_google_credentials()
    service = build('drive', 'v3', credentials=creds)
    
    results = service.files().list(
        pageSize=10, 
        fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
        q="mimeType = 'application/vnd.google-apps.document' or mimeType = 'application/pdf'"
    ).execute()
    files = results.get('files', [])
    
    docs = []
    for file in files:
        file_id = file['id']
        name = file['name']
        mime_type = file['mimeType']
        
        content = ""
        try:
            if mime_type == 'application/vnd.google-apps.document':
                request = service.files().export_media(fileId=file_id, mimeType='text/plain')
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                content = fh.getvalue().decode('utf-8')
                if content:
                    metadata = {
                        "drive_file_id": file_id,
                        "filename": name,
                        "last_modified": file['modifiedTime'],
                        "source": f"Drive: {name}",
                        "source_type": "drive",
                        "ingestion_timestamp": datetime.now().isoformat()
                    }
                    docs.append(Document(page_content=content, metadata=metadata))
            elif mime_type == 'application/pdf':
                from backend.ingestion.pdf_loader import process_pdf
                
                request = service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                os.makedirs("temp_uploads", exist_ok=True)
                temp_path = f"temp_uploads/drive_{file_id}.pdf"
                with open(temp_path, "wb") as f:
                    f.write(fh.getbuffer())
                
                try:
                    process_pdf(temp_path, name)
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        except Exception as e:
            pass
            
    return docs

def process_drive():
    docs = fetch_drive_files()
    if not docs:
        return 0
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(docs)
    
    vector_store = get_vector_store()
    vector_store.add_documents(splits)
    
    return len(docs)
