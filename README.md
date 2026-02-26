# PKAA: Personal Knowledge AI Agent

Live Application: [PKAA Portfolio Demo](https://rag-based-pesonalised-knowledge-cb6mdbalkwud4bxs642zhp.streamlit.app/)

PKAA is a Retrieval-Augmented Generation (RAG) application that allows you to create a private knowledge base from various data sources and interact with it using Google Gemini models.

## Features

- PDF Ingestion: Upload and index PDF documents for targeted retrieval.
- Web Crawling: Extract and index content from public URLs.
- Google Workspace Integration: Sync data directly from Gmail and Google Drive.
- RAG Chat Interface: Natural language interactions with source document attribution.
- System Diagnostics: Built-in tools for API status verification and database maintenance.

## Tech Stack

- Frontend: Streamlit
- LLM: Google Gemini (gemini-flash-latest)
- Embeddings: Google Generative AI (gemini-embedding-001)
- Orchestration: LangChain
- Vector Store: ChromaDB

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Sohan-ghosh835/RAG-based-Pesonalised-Knowledge.git
   cd RAG-based-Pesonalised-Knowledge
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a .env file:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key
   CHROMA_PERSIST_DIR=./chroma_db
   ```

## Deployment on Streamlit Cloud

1. Push your code to a GitHub repository.
2. Connect the repository to Streamlit Community Cloud.
3. Add the following to your App Secrets (Advanced Settings):
   - GOOGLE_API_KEY
   - CHROMA_PERSIST_DIR
   - [GOOGLE_CREDENTIALS] (for Google Workspace integration)

## Maintenance

The application includes a Diagnostics section in the sidebar. Use these tools to:
- List available models for your API key.
- Test embedding generation.
- Wipe the vector database to resolve indexing issues or clear content.
