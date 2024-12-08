import os
from langchain.tools import tool  # Decorator to create tools
from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Google's embeddings
from langchain_chroma import Chroma  # Vector database
from langchain_community.document_loaders import PyPDFLoader  # Loads and parses PDF files
from get_key import get_api_key
from docx import Document as DocxDocument
from langchain.schema import Document
import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from difflib import SequenceMatcher


# TODO: fix the caching of documents for uploaded where only the newly uploaded files are scanned
# TODO: check if we want to merge the 2 vector dbs where we only allow the search of files uploaded to the bot

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




@tool
def search_vector_uploaded(query: str) -> str:
    """
    Search the uploaded files vector database for documents similar to the query.
    Args:
        query (str): The search query string to find relevant documents
    Returns:
        str: A concatenated string of the top 5 most similar document contents found in the vector database
    """
    
    # Variable holding the List[Document] to add to the vectordb
    added_documents = []

    # Initialize embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=get_api_key())

    vector_store = Chroma(
        collection_name = "embeddings",
        embedding_function = embeddings,
        persist_directory = "./vector_added",
        collection_metadata = {"hnsw:space": "cosine"}  # Use cosine similarity
    ) 
      
    directory_path = os.path.join(os.path.dirname(__file__), '../', 'added')
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
            added_documents.extend(documents)
            
        # Check if the file is a Word document
        elif filename.endswith('.docx'):
            file_path = os.path.join(directory_path, filename)
            docx_file = DocxDocument(file_path)
            print(docx_file.paragraphs)
            # Extract text and create Document objects for each paragraph
            documents = [
                Document(
                    page_content=para.text,
                    metadata={"source": file_path}
                )
                for para in docx_file.paragraphs if para.text.strip()  # Ignore empty paragraphs
            ]
            added_documents.extend(documents)

        # Check if the file is a plain text file
        elif filename.endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            # Create a single Document object for the entire file content
            documents = [
                Document(
                    page_content=content,
                    metadata={"source": file_path}
                )
            ]
            added_documents.extend(documents)

        # Add the cached documents to the vector store with their embeddings
        vector_store.add_documents(added_documents)
    
    # Debug print
    print("Searching the ADDED vector database for: ", query)
    
    # Perform similarity search and get top 5 results
    result = vector_store.similarity_search(query = query, k = 5)
    # Combine all document contents into single string
    result_str = "\n".join([doc.page_content for doc in result])
    
    return result_str

# The role of this function is to save the added files in the 'added' folder
def save_uploaded_files(uploaded_files) -> str:
    
    directory_path = os.path.join(os.path.dirname(__file__), '../', 'added')
    # Check if the folder exists, create it if not
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

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

@tool
def scrape_latest_url(url: str) -> str:
    """
    Finds the latest uploaded URL, and webscrapes/scrapes/summarizes its content and displays the info. 

    Args:
        url (str): The url of the website that is needed to scrape.

    Returns:
        str: Scraped content from the latest URL given, and do not let the content displayed or asked for more that 500 words.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        # Validate the URL
        if not url.startswith("http://") and not url.startswith("https://"):
            return "Invalid URL. Please provide a valid URL starting with http:// or https://."

        # Send GET request to the URL
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"Failed to fetch the URL. HTTP status code: {response.status_code}."

        # Parse the webpage content with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        # Initialize content string to store the scraped data
        content = ""
        
        # Handle all h2 tags and paragraphs/divs after them
        h2_tags = soup.find_all('h2')

        for h2 in h2_tags:
            content += f"**{h2.text.strip()}**\n\n"
            
            # Find all elements following this h2 and stop at the next h2
            next_elements = h2.find_all_next()

            for element in next_elements:
                if element.name == 'h2':  # Stop once we reach the next h2 tag
                    break
                if element.name in ['p']:  # Check for both p and div tags
                    # Only add the content of the element if it's not empty
                    if element.text.strip(): 
                        content += f"{element.text.strip()}\n\n"
            
            content += "-" * 40 + "\n\n"
        
        return content

    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching the URL: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"



# @tool
# def compare_url_with_document(url: str, document: str) -> str:
#     """
#     Compare the content of a URL, by webscraping and summarizing the content, with the content of the uploaded document and correct discrepancies in the document, and say the incorrect info if present.
    
#     Args:
#         url (str): The URL to scrape for reference content.
#         document (str): The search query string to find relevant documents
 
#     Returns:
#         str: Corrected content for the document.
#     """

#     try:
#         # Initialize variables and load embedding model
#         embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=get_api_key())
#         vector_store = Chroma(
#             collection_name="embeddings",
#             embedding_function=embeddings,
#             persist_directory="./vector_added",
#             collection_metadata={"hnsw:space": "cosine"}
#         )
        
#         added_documents = []
#         directory_path = os.path.join(os.path.dirname(__file__), '../', 'added')
#         # Load and parse documents
#         for filename in os.listdir(directory_path):
#             file_path = os.path.join(directory_path, filename)
#             if filename.endswith('.pdf'):
#                 documents = PyPDFLoader(file_path).load()
#             elif filename.endswith('.docx'):
#                 docx_file = DocxDocument(file_path)
#                 documents = [
#                     Document(page_content=para.text, metadata={"source": file_path})
#                     for para in docx_file.paragraphs if para.text.strip()
#                 ]
#             elif filename.endswith('.txt'):
#                 with open(file_path, 'r', encoding='utf-8') as file:
#                     content = file.read()
#                 documents = [Document(page_content=content, metadata={"source": file_path})]
#             else:
#                 continue
#             added_documents.extend(documents)
#         vector_store.add_documents(added_documents)

#         # Validate and fetch URL content
#         if not url.startswith("http://") and not url.startswith("https://"):
#             return "Invalid URL. Please provide a valid URL starting with http:// or https://."
#         response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
#         if response.status_code != 200:
#             return f"Failed to fetch the URL. HTTP status code: {response.status_code}."
#         soup = BeautifulSoup(response.content, "html.parser")
        
#         # Extract content from webpage
#         content = ""
#         for h2 in soup.find_all('h2'):
#             content += f"**{h2.text.strip()}**\n\n"
#             for elem in h2.find_all_next(['p'], limit=10):  # Limit to 10 elements for simplicity
#                 if elem.name == 'h2':
#                     break
#                 content += f"{elem.text.strip()}\n\n"

#         # Correct discrepancies
#         corrected_document = []
#         for doc in added_documents:
#             text = doc.page_content
#             similarity_scores = [SequenceMatcher(None, text, section).ratio() for section in content.split('\n\n')]
#             max_similarity = max(similarity_scores, default=0)
#             if max_similarity > 0.85:
#                 corrected_document.append(text)
#             else:
#                 best_match = content.split('\n\n')[similarity_scores.index(max_similarity)] if similarity_scores else ""
#                 corrected_document.append(f"[UPDATED] {best_match}")

#         return "\n".join(corrected_document)

#     except Exception as e:
#         return f"An error occurred: {e}"