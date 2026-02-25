from googleapiclient.discovery import build
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
from backend.core.auth import get_google_credentials
from backend.core.vector_store import get_vector_store
import base64

def fetch_gmail_emails(max_results=10):
    creds = get_google_credentials()
    service = build('gmail', 'v1', credentials=creds)
    
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    
    docs = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = msg_data.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
        else:
            data = payload.get('body', {}).get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        if body:
            metadata = {
                "email_id": msg['id'],
                "subject": subject,
                "sender": sender,
                "date": date,
                "source": f"Gmail: {subject}",
                "source_type": "gmail",
                "ingestion_timestamp": datetime.now().isoformat()
            }
            docs.append(Document(page_content=body, metadata=metadata))
            
    return docs

def process_gmail(max_results=10):
    docs = fetch_gmail_emails(max_results)
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
