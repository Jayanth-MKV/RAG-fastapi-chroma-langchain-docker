# chat_service.py
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

class ChatInput(BaseModel):
    asset_id: str= Field(..., example="0b4737c2-1246-4099-87d2-baca0b20938d")

class MessageInput(BaseModel):
    chat_id: str= Field(..., example="cf7a10e6-1343-4d08-a522-a0e850634d01")
    message: str= Field(..., example="Hello, how can I assist you?")

class ChatService:
    def __init__(self, document_service):
        """
    Initialize the ChatService with a DocumentService instance.

    Args:
        document_service (DocumentService): The DocumentService instance used to interact with the document store.

    Attributes:
        router (APIRouter): The FastAPI router for the chat service endpoints.
        document_service (DocumentService): The DocumentService instance used to interact with the document store.
        llm (ChatGroq): The language model instance used for chat interactions.
        store (dict): A dictionary used to store chat session data.
    """
        self.router = APIRouter()
        self.document_service = document_service
        self.llm = ChatGroq(model="llama3-8b-8192")
        self.store = {}
        
        self.router.add_api_route("/api/chat/start", self.start_chat, methods=["POST"])
        self.router.add_api_route("/api/chat/message", self.chat_message, methods=["POST"])
        self.router.add_api_route("/api/chat/history", self.chat_history, methods=["GET"])

    def setup_rag_chain(self, asset_id):
        """
    Sets up a Retrieval-Augmented Generation (RAG) chain for the given asset_id.
    The RAG chain is used to generate responses to user messages in a chat session.
   
    Args:
        asset_id (str): The unique identifier for the asset to be used in the chat session.
        
    Returns:
        RunnableWithMessageHistory: A RunnableWithMessageHistory instance that can be used to generate responses to user messages in a chat session.
    """
        retriever = self.document_service.vector_store.as_retriever(
            search_kwargs={"k": 2, "filter": {"asset": {"$in": [asset_id]}}}
        )

        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        return RunnableWithMessageHistory(
            create_retrieval_chain(
                create_history_aware_retriever(
                    self.llm,
                    retriever,
                    contextualize_q_prompt
                ),
                create_stuff_documents_chain(self.llm, qa_prompt)
            ),
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """
    Retrieves the chat history for the specified session ID.

    Args:
        session_id (str): The unique identifier for the chat session.

    Returns:
        BaseChatMessageHistory: An instance of BaseChatMessageHistory containing the chat history for the specified session ID.

    Raises:
        KeyError: If the specified session ID is not found in the store.
    """
        if session_id not in self.store:
            self.store[session_id] = {"history": ChatMessageHistory()}
        return self.store[session_id]["history"]

    async def start_chat(self, chat_input: ChatInput):
        try:
            chat_id = str(uuid.uuid4())
            self.store[chat_id] = {
                "asset_id": chat_input.asset_id,
                "history": ChatMessageHistory(),
                "rag_chain": self.setup_rag_chain(chat_input.asset_id)
            }
            return {"chat_id": chat_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start chat: {str(e)}")

    async def chat_message(self, message_input: MessageInput):
        """
    Processes a user message in a chat session and generates a response.

    Args:
        message_input (MessageInput): A dictionary containing the chat ID and the user message.

    Returns:
        StreamingResponse: A StreamingResponse object that streams the generated response to the client. The response is formatted as text/event-stream and contains chunks of the response.

    Raises:
        HTTPException: If the specified chat ID is invalid.
    """
        if message_input.chat_id not in self.store:
            raise HTTPException(status_code=400, detail="Invalid chat ID")
        
        print(message_input)
        chat_data = self.store[message_input.chat_id]
        
        async def generate_response():
            try:
                async for chunk in self.stream_generator(chat_data["rag_chain"], message_input):
                    # print(chunk)
                    yield chunk
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

        return StreamingResponse(generate_response(), media_type="text/event-stream")

    async def stream_generator(self, rag_chain: any, message_input):
        """
    Generates a stream of responses to user messages in a chat session.

    Args:
        rag_chain (any): A RunnableWithMessageHistory instance that can be used to generate responses to user messages in a chat session.
        message_input (MessageInput): A dictionary containing the chat ID and the user message.

    Yields:
        bytes: A chunk of the generated response, encoded as bytes.

    Raises:
        Exception: If the specified chat ID is invalid.

    Note:
    The `stream_generator` function is an asynchronous generator that yields chunks of the generated response as bytes. It uses the `rag_chain` instance to generate responses to user messages and the `message_input` dictionary to provide the chat ID and user message. The function ensures that the answer chunk is converted to bytes before yielding it.
    """
        try:
            for chunk in rag_chain.stream(
                {"input": message_input.message},
                config={"configurable": {"session_id": message_input.chat_id}},
            ):
                # Ensure chunk is converted to bytes
                if chunk.get('answer'):
                    yield chunk.get('answer').encode('utf-8') 
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")


    async def chat_history(self, chat_id: str):
        """
    Retrieves the chat history for the specified session ID.

    Args:
        chat_id (str): The unique identifier for the chat session.

    Returns:
        dict: A dictionary containing the chat history for the specified session ID. The dictionary has a single key, "history", which is a list of strings representing the chat messages.

    Raises:
        HTTPException: If the specified chat ID is invalid.
    """
        if chat_id not in self.store:
            raise HTTPException(status_code=400, detail="Invalid chat ID")
        
        try:
            history = self.store[chat_id]["history"].messages
            return {"history": [str(msg) for msg in history]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")