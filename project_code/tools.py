import os
from langchain.tools import tool  # Decorator to create tools
from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Google's embeddings
from langchain_chroma import Chroma  # Vector database
from langchain_community.document_loaders import PyPDFLoader  # Loads and parses PDF files
from get_key import get_api_key

_cached_documents = []

# Tool definition for searching vector database
@tool
def search_vector_db(query: str) -> str:
    """
    Search the vector database for documents similar to the query.
    Args:
        query (str): The search query string to find relevant documents
    Returns:
        str: A concatenated string of the top 5 most similar document contents found in the vector database
    """
    
    # Initialize embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=get_api_key())
    
    # Initialize/connect to vector database
    vector_store = Chroma(
        collection_name = "embeddings",
        embedding_function = embeddings,
        persist_directory = "./vector_db",
        collection_metadata = {"hnsw:space": "cosine"}  # Use cosine similarity
    )

    if not _cached_documents:
        directory_path = os.path.join(os.path.dirname(__file__), '../', 'db')
        # Loop through all PDF files in the directory
        for filename in os.listdir(directory_path):
        # Check if the file is a PDF
            if filename.endswith('.pdf'):
                # Create full file path by joining directory and filename
                file_path = os.path.join(directory_path, filename)
                # Create a PDF loader for the current file
                loader = PyPDFLoader(file_path)
                # Load and parse the PDF into documents
                documents = loader.load()
                _cached_documents.extend(documents)

        # Add the cached documents to the vector store with their embeddings
        vector_store.add_documents(_cached_documents)
    
    # Debug print
    print("Searching the vector database for: ", query)
    
    # Perform similarity search and get top 5 results
    result = vector_store.similarity_search(query = query, k = 5)
    # Combine all document contents into single string
    result_str = "\n".join([doc.page_content for doc in result])
    
    return result_str

# Tool definition for adding numbers
@tool
def add_two_numbers(a: int, b: int) -> str:
    """
    Adds two numbers together
    Args:
        a (int): The first number
        b (int): The second number
    Returns:
        str: The sum of the two numbers
    """
    # Convert result to string since LLM expects string output
    return str(a + b)
