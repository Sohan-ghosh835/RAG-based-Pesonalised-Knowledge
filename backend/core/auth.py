import streamlit as st
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def get_google_credentials():
    creds = None
    token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
    client_secret_path = os.getenv("GOOGLE_CLIENT_SECRET_PATH", "credentials.json")
    
    if not os.path.exists(client_secret_path) and "GOOGLE_CREDENTIALS" in st.secrets:
        with open(client_secret_path, "w") as f:
            json.dump(dict(st.secrets["GOOGLE_CREDENTIALS"]), f)

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secret_path):
                raise FileNotFoundError(f"Missing {client_secret_path}")
            
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, "w") as token:
            token.write(creds.to_json())
            
    return creds
