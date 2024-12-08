import os
from pathlib import Path
from datetime import datetime
from hashlib import md5
from gemini_chat import GeminiChat
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from tools import save_uploaded_files
import re
from urllib.parse import urlparse
# async keyword defines an asynchronous function that can be paused and resumed,
# allowing other code to run while waiting for I/O operations like network requests.
# This enables non-blocking concurrent execution of tasks. Similar to multithreading.


# Directory to store the URLs
URL_DIRECTORY = Path("C:/Users/User/Documents/George/lau/Fall 2024/LLM/Project/LLM_Project/LLM_Project/urls")


# Function to save the URL to a text file
def save_url_to_file(url):
    # Parse the URL to extract the domain and path for naming
    parsed_url = urlparse(url)
    # Use the netloc (domain) and path as part of the filename
    url_path = parsed_url.path.strip("/").replace("/", "_") or "root"
    domain = parsed_url.netloc.replace("www.", "")
    filename = f"{domain}_{url_path}.txt"
    
    # Ensure the directory exists
    URL_DIRECTORY.mkdir(parents=True, exist_ok=True)

    # Create the file path
    file_path = URL_DIRECTORY / filename
    
    # If the file already exists, remove it
    if file_path.exists():
        file_path.unlink()  # Delete the old file

    # Write the URL to the file
    with file_path.open("w", encoding="utf-8") as file:
        file.write(url)
    
    return file_path




async def streamlit_interface():
    st.title("Gemini Chat")
    st.write("Ask anything about the documents in the vector database")
    with st.sidebar:
        uploaded_files = st.file_uploader("Upload a document",
                                           type=["txt", "pdf", "docx"],
                                           accept_multiple_files=True)  

    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} file(s):")
        st.write(save_uploaded_files(uploaded_files))
        # for uploaded_file in uploaded_files:
        #     st.write(f"- {uploaded_file.name}")
            # if uploaded_file.type == "text/plain":
            #     # Read and display text file content
            #     content = uploaded_file.read().decode("utf-8")
            #     st.text_area(f"Content of {uploaded_file.name}", content, height=300)
            # elif uploaded_file.type == "application/pdf":
            #     st.write(f"PDF processing for {uploaded_file.name} is not implemented yet.")
            # elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            #     st.write(f"DOCX processing for {uploaded_file.name} is not implemented yet.")
        

    # Initialize LLM instance if not already in session state
    # This ensures the chat model persists across page refreshes
    # Also ensures that the LLM instance is created only once
    if "llm" not in st.session_state: # session state is a dictionary that stores the state of the application and does not get reset on page refresh
        st.session_state.llm = GeminiChat()
        
    # Initialize message history in session state if not already present
    # This stores the chat history between user and AI across page refreshes
    if "messages" not in st.session_state:
        st.session_state.messages = [] # Empty list to store message history

    # Display all previous messages from session state
    for message in st.session_state.messages:
        # Create chat message UI element with appropriate type (user/assistant) and display content

        # Handle AI message with content (regular response)
        if isinstance(message, AIMessage) and message.content:
            with st.chat_message("assistant"):
                st.markdown(message.content)

        # Handle AI message without content (tool call)

        # elif isinstance(message, AIMessage) and not message.content:
        #     with st.chat_message("assistant"):
        #         # Extract tool name and arguments from the tool call
        #         tool_name = message.tool_calls[0]['name']
        #         tool_args = str(message.tool_calls[0]['args'])
        #         # Display tool call details with status indicator
        #         with st.status(f"Tool call: {tool_name}"):
        #             st.markdown(tool_args)
        
        # Handle tool execution result message
        # elif isinstance(message, ToolMessage):
        #     with st.chat_message("assistant"):
        #         # Display tool execution result with status indicator
        #         with st.status("Tool result: "):
        #             st.markdown(message.content)

        # Handle user message
        elif isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.markdown(message.content)
    
    # Get user input from chat interface using Streamlit's chat_input widget
    # Returns None if no input is provided
    prompt = st.chat_input("Your message")

    # Get user input from chat interface. 
    if prompt:
        # Add user's message to session state history
        st.session_state.messages.append(HumanMessage(content=prompt))
        # Display user's message in chat UI
        with st.chat_message("user"):
            st.markdown(prompt)

        # Send message to LLM and get response messages (may include tool usage)
        messages = st.session_state.llm.send_message(prompt)
        
        # Add all new messages (including tool calls) to session state history
        st.session_state.messages.extend(messages)

        # Process response messages
        for message in messages:
            # Check if message is from AI (not a tool call) and has content
            # When it is a tool call, AIMessage object is created but it has no content
            # isinstance(message, AIMessage) will skip tool outputs
            if isinstance(message, AIMessage) and message.content:
                # Display AI's regular response message
                with st.chat_message("assistant"):
                    st.markdown(message.content)

            # elif isinstance(message, AIMessage) and not message.content:
            #     # Handle AI message that contains a tool call
            #     with st.chat_message("assistant"):
            #         # Extract tool name and arguments from the tool call
            #         tool_name = message.tool_calls[0]['name']
            #         tool_args = str(message.tool_calls[0]['args'])
            #         # Display tool call details with status indicator
            #         with st.status(f"Tool call: {tool_name}"):
            #             st.markdown(tool_args)

            # elif isinstance(message, ToolMessage):
            #     # Display the result returned from tool execution
            #     with st.chat_message("assistant"):
            #         with st.status("Tool result: "):
            #             st.markdown(message.content)

            elif isinstance(message, HumanMessage):
                # Display user's message
                with st.chat_message("user"):
                    st.markdown(message.content)

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None