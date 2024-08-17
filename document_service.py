# document_service.py
import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import  TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_chroma import Chroma
from langchain.schema import Document
from pydantic import BaseModel, Field


CHROMA_PATH = "chroma"


class FileInput(BaseModel):
    file_path: str = Field(..., example="./data/a2.pdf")

class DocumentService:
    def __init__(self):
        """
    Initialize the DocumentService class.

    Args:
    None

    Returns:
    None

    Raises:
    None
    """
        self.router = APIRouter()
        
        self.embeddings = HuggingFaceEmbeddings()
        self.vector_store = Chroma( collection_name="documents", embedding_function=self.embeddings,persist_directory=CHROMA_PATH)
        self.data_folder = "./data"  # Update this to the path of your data folder
        
        self.router.add_api_route("/api/documents/process", self.process_document, methods=["POST"])

    async def process_document(self, file_input: FileInput):
        """
    Process a document file and save it to the Chroma database.

    Args:
    file_input (FileInput): A Pydantic model containing the file path of the document to be processed.

    Returns:
    dict: A dictionary containing the asset ID of the processed document.

    Raises:
    HTTPException: If an exception occurs during the processing or saving of the document.
    """
        try:
            asset_id = str(uuid.uuid4())
            metadata = {"asset": asset_id, "source": file_input.file_path}
            texts = self._process_file(file_input.file_path,metadata)
            ids=[f"{asset_id}_{i}" for i in range(len(texts))]
            # print(texts[0])
            self.save_to_chroma(texts,ids)
            
            return {"asset_id": asset_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def _process_file(self, file_path,metadata):
        """
    Process a document file and split it into smaller chunks.

    Args:
    file_path (str): The path to the document file to be processed.
    metadata (dict): Additional metadata to be associated with the processed document.

    Returns:
    list[str]: A list of strings representing the processed text chunks.

    Raises:
    ValueError: If the file type is not supported.
    """
        _, file_extension = os.path.splitext(file_path)
        
        if file_extension == '.txt':
            loader = TextLoader(file_path)
        elif file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension in ['.doc', '.docx']:
            loader = Docx2txtLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        documents = loader.load()
        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        
        return texts
    

    def save_to_chroma(self,chunks: list[Document],uuids:list[str]):
        """
    Save the given list of Document objects to a Chroma database.

    Args:
    chunks (list[Document]): List of Document objects representing text chunks to save.

    Returns:
    None

    This function saves the provided list of Document objects to a Chroma database. It uses the OpenAI embeddings to create a new Chroma database from the documents and then persists the database to disk. The function does not return any value, but it prints a message indicating the number of chunks saved to the Chroma database.
    """

        # Create a new Chroma database from the documents using OpenAI embeddings
        self.vector_store.add_documents(documents=chunks, ids=uuids)

        # Persist the database to disk
        # self.db.persist()
        print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")

    def list_documents(self):
        """
    List all the document files present in the specified data folder.

    Args:
    self (DocumentService): An instance of the DocumentService class.

    Returns:
    dict: A dictionary containing a list of all the document files present in the specified data folder.

    The function lists all the document files present in the specified data folder and returns a dictionary containing a list of all the document files. The list of document files is obtained by iterating through the files in the data folder and filtering out the non-file entries. The dictionary returned by the function has a single key-value pair, where the key is "documents" and the value is a list of all the document files present in the specified data folder.
    """
        documents = [f for f in os.listdir(self.data_folder) if os.path.isfile(os.path.join(self.data_folder, f))]
        return {"documents": documents}
    
