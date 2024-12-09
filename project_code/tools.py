import os
from langchain.tools import tool  # Decorator to create tools
from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Google's embeddings
from langchain_chroma import Chroma  # Vector database
from langchain_community.document_loaders import PyPDFLoader  # Loads and parses PDF files
from get_key import get_api_key
from docx import Document as DocxDocument
from langchain.schema import Document


# This function works as a search vector depending on what the user uploads. It has a cache mechanism as well where it will only scan the newly uploaded files 
# not all files everytime.
def search_vector_db(query: str) -> str:
    """
    Search the vector database for documents similar to the query.
    Args:
        query (str): The search query string to find relevant documents
    Returns:
        str: A concatenated string of the top 5 most similar document contents found in the vector database
    """
    
    # Variable holding the List[Document] to add to the vectordb
    added_documents = []

    # Initialize embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=get_api_key())
    
    # Initialize/connect to vector database
    vector_store = Chroma(
        collection_name = "embeddings",
        embedding_function = embeddings,
        persist_directory = "./vector_db",
        collection_metadata = {"hnsw:space": "cosine"}  # Use cosine similarity
    )

    directory_path = os.path.join(os.path.dirname(__file__), '../', 'db')
    directory_details_path = os.path.join(directory_path, 'db_details')

    # Load last scan timestamps from a file
    last_scan_file = os.path.join(directory_details_path, 'last_scan.txt')
    if os.path.exists(last_scan_file):
        with open(last_scan_file, 'r') as f:
            last_scan_times = eval(f.read())  # Read and parse stored times
    else:
        last_scan_times = {}

    current_scan_times = {}

    # Loop through all files in the directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            mod_time = os.path.getmtime(file_path)
            current_scan_times[filename] = mod_time
            
            # Check if the file was added/modified after the last scan
            if filename not in last_scan_times or last_scan_times[filename] < mod_time:
                #Debug print
                print(f"I am scanning the file: {filename}")
                if filename.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                    documents = loader.load()
                    added_documents.extend(documents)
                elif filename.endswith('.docx'):
                    docx_file = DocxDocument(file_path)
                    documents = [
                        Document(
                            page_content=para.text,
                            metadata={"source": file_path}
                        )
                        for para in docx_file.paragraphs if para.text.strip()
                    ]
                    added_documents.extend(documents)
                elif filename.endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    documents = [
                        Document(
                            page_content=content,
                            metadata={"source": file_path}
                        )
                    ]
                    added_documents.extend(documents)

    # Update last scan times
    with open(last_scan_file, 'w') as f:
        f.write(str(current_scan_times))

    # Add the cached documents to the vector store with their embeddings
    if(len(added_documents) > 0):
        vector_store.add_documents(added_documents)

    # Debug print
    print("Searching the vector database for: ", query)
    
    # Perform similarity search and get top 5 results
    result = vector_store.similarity_search(query=query, k=5)
    result_str = "\n".join([doc.page_content for doc in result])
    
    return result_str


# The role of this function is to save the added files in the 'added' folder1
def save_uploaded_files(uploaded_files) -> str:
    
    # The db folder
    directory_path = os.path.join(os.path.dirname(__file__), '../', 'db')
    # The caching folder
    db_details_path = os.path.join(directory_path, 'db_details')
    # Check if the folder exists, create it if not
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        os.makedirs(db_details_path)

    saved_files = []  # List to store paths of saved files

    # Loop through the uploaded files and save them
    for uploaded_file in uploaded_files:
        # Get the file name
        file_name = uploaded_file.name
        # Create the full file path
        file_path = os.path.join(directory_path, file_name)
        
        # Check if the file already exists in the directory
        if os.path.exists(file_path):
            saved_files.append(f"- File '{file_name}' skipped, it already exists")
            continue  # Skip this file if it already exists

        # Write the file to the specified folder
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())  # Save file content

        # Add the file path to the list of saved files
        saved_files.append(f"- {file_name}")

    return "\n".join(saved_files)


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