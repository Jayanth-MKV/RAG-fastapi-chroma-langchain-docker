import streamlit as st
import requests
import time
import os
import json

# API base URL
API_BASE_URL = "http://localhost:8000"

# Streamlit app
st.title("RAG Chatbot")

# Session state initialization
if 'chats' not in st.session_state:
    st.session_state.chats = {}
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'uploaded_docs' not in st.session_state:
    st.session_state.uploaded_docs = {}
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False


# Sidebar for chat list
with st.sidebar:
    st.header("Chats")
    for chat_id in st.session_state.chats:
        if st.button(f"Chat {chat_id}"):
            st.session_state.current_chat_id = chat_id
            st.session_state.chat_started = True

    # File uploader
    uploaded_file = st.file_uploader("Upload a document", type=['pdf', 'txt', 'doc'])
    if uploaded_file is not None:
        # Process the uploaded file
        # Save the uploaded file temporarily
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

        response = requests.post(f"{API_BASE_URL}/api/documents/process", json={"file_path": uploaded_file.name})
        
        # Delete the temporary file
        os.remove(uploaded_file.name)

        if response.status_code == 200:
            asset_id = response.json()['asset_id']
            st.session_state.uploaded_docs[uploaded_file.name] = asset_id
            st.success(f"Document processed. Asset ID: {asset_id}")
        else:
            st.error("Error processing document")

    
    # Document selector
    if st.session_state.uploaded_docs:
        selected_doc = st.selectbox("Select a document", list(st.session_state.uploaded_docs.keys()))
        if st.button("Start New Chat"):
            asset_id = st.session_state.uploaded_docs[selected_doc]
            response = requests.post(f"{API_BASE_URL}/api/chat/start", json={'asset_id': asset_id})
            if response.status_code == 200:
                chat_id = response.json()['chat_id']
                st.session_state.chats[chat_id] = []
                st.session_state.current_chat_id = chat_id
                st.session_state.chat_started = True
                st.success(f"New chat started with ID: {chat_id}")
            else:
                st.error("Error starting new chat")

# Main chat area
if st.session_state.current_chat_id:
    st.header(f"Chat {st.session_state.current_chat_id}")

    # Display chat history
    for message in st.session_state.chats[st.session_state.current_chat_id]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    user_input = st.chat_input("Type your message here")
    if user_input:
        # Add user message to chat history
        st.session_state.chats[st.session_state.current_chat_id].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Send message to API and stream response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in requests.post(
                f"{API_BASE_URL}/api/chat/message",
                json={'chat_id': st.session_state.current_chat_id, 'message': user_input},
                stream=True
            ).iter_content(chunk_size=1024,decode_unicode=True):
                if response:
                    print(response)
                    full_response += response
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        # Add assistant response to chat history
        st.session_state.chats[st.session_state.current_chat_id].append({"role": "assistant", "content": full_response})

# Warning about data loss on reload
st.warning("Warning: All chat data will be lost if you reload the page.")

# JavaScript to show an alert when the page is about to be reloaded
st.markdown("""
<script>
window.onbeforeunload = function() {
    return "Are you sure you want to reload? All chat data will be lost.";
}
</script>
""", unsafe_allow_html=True)