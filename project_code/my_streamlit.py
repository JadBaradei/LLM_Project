from gemini_chat import GeminiChat
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage  # Message types for chat
from tools import save_uploaded_files, set_plot_type, get_plotted_figure

# async keyword defines an asynchronous function that can be paused and resumed,
# allowing other code to run while waiting for I/O operations like network requests.
# This enables non-blocking concurrent execution of tasks. Similar to multithreading.
async def streamlit_interface():
    st.title("LLM Project Chat")
    with st.sidebar:
        uploaded_files = st.file_uploader("Upload a document",
                                           type=["txt", "pdf", "docx", "xlsx"],
                                           accept_multiple_files=True)
        set_plot_type(st.selectbox("Select plot type", ["bar", "line", "scatter"]))
    
    if uploaded_files:
        st.write(f"Uploaded {len(uploaded_files)} file(s):")
        st.write(save_uploaded_files(uploaded_files))
        
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
        if isinstance(message, AIMessage):
                if message.content:
                    # Display AI's regular response message
                    with st.chat_message("assistant"):
                        st.markdown(message.content)
                else:
                    # Handle the tool call for plotting
                    tool_name = message.tool_calls[0]['name']
                    if tool_name == "plot_excel_sheet":
                        st.pyplot(get_plotted_figure())

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
            if isinstance(message, AIMessage):
                if message.content:
                    # Display AI's regular response message
                    with st.chat_message("assistant"):
                        st.markdown(message.content)
                else:
                    # Handle the tool call for plotting
                    tool_name = message.tool_calls[0]['name']
                    if tool_name == "plot_excel_sheet":
                        st.pyplot(get_plotted_figure())

            elif isinstance(message, HumanMessage):
                # Display user's message
                with st.chat_message("user"):
                    st.markdown(message.content)
