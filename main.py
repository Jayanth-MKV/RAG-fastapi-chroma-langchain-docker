# main.py
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from document_service import DocumentService
from chat_service import ChatService
from dotenv import load_dotenv

load_dotenv()

app = FastAPI( title="RAG FASTAPI",
    description="This is the API documentation for RAG FASTAPI, which provides api for processing and chatting documents.",
    version="1.0.0"
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_service = DocumentService()
chat_service = ChatService(document_service)

# Include routers
app.include_router(document_service.router)
app.include_router(chat_service.router)

@app.get("/api/documents")
async def list_documents():
    """
    Retrieves a list of all available documents.

    This function retrieves a list of all available documents from the document service.

    Parameters:
    No parameters are required for this function.

    Returns:
    A list of all available documents.
    """
    return document_service.list_documents()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)