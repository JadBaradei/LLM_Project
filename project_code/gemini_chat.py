# Main chat class that uses Gemini LLM
from langchain_google_genai import ChatGoogleGenerativeAI # Google's LLM
from langchain_core.messages import HumanMessage  # Message types for chat
from langgraph.prebuilt import create_react_agent  # For creating an agent that can use tools
from get_key import get_api_key
from tools import search_vector_db, search_google_scholar

class GeminiChat:
    def __init__(self, model_name: str = "gemini-pro", temperature: float = 0.0):
        """
        Initialize GeminiChat with a language model.

        Args:
            model_name (str): The model to use. Default is "gemini-pro".
            temperature (float): The temperature to use. Default is 0.0.
        """
        # Store API key
        
        self.api_key=get_api_key()
        
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=self.api_key, 
            temperature=temperature
        )
        
        # Create agent with both tools available
        self.agent = create_react_agent(self.llm, tools=[search_vector_db, search_google_scholar])
        
        # Initialize conversation history
        self.messages = []
        
    def send_message(self, message: str) -> str:
        """
        Send a message and get response from the model.
        
        Args:
            message (str): The message to send
            
        Returns:
            str: The model's response content
        """
        # Add user message to history
        self.messages.append(HumanMessage(content=message))
        
        # Store current history length to identify new messages later
        history_length = len(self.messages)
        
        # Get response from agent, including any tool usage
        self.messages = self.agent.invoke({"messages": self.messages})["messages"]
        
        # Extract only the new messages from this interaction
        new_messages = self.messages[history_length:]

        return new_messages 
    