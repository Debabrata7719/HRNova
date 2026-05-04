"""
Policy Embedder
Load NovaHR Company Policy PDF into ChromaDB with metadata
"""

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# Get base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF_PATH = os.path.join(BASE_DIR, "data", "NovaHR_Company_Policy_Notebook.pdf")
DB_DIRECTORY = os.path.join(BASE_DIR, "data", "chroma_db")
COLLECTION_NAME = "novahr_policy"


def extract_sections_from_pdf(text: str) -> list[tuple[str, dict]]:
    """
    Extract sections from PDF text and return chunks with metadata.
    This is a simple version - can be enhanced with better parsing.
    """
    sections = []

    # Define section patterns and their metadata
    section_mapping = {
        "ATTENDANCE": {
            "section": "Attendance & Work Timing",
            "sub_section": "General",
            "policy_number": "01",
            "policy_name": "Attendance Policy",
            "audience": "both",
        },
        "SHIFT": {
            "section": "Attendance & Work Timing",
            "sub_section": "Shift Timing",
            "policy_number": "01",
            "policy_name": "Attendance Policy",
            "audience": "both",
        },
        "LEAVE": {
            "section": "Leave Policy",
            "sub_section": "General",
            "policy_number": "04",
            "policy_name": "Leave Policy",
            "audience": "both",
        },
        "EARNED LEAVE": {
            "section": "Leave Policy",
            "sub_section": "Earned Leave",
            "policy_number": "04",
            "policy_name": "Leave Policy",
            "audience": "both",
        },
        "CASUAL LEAVE": {
            "section": "Leave Policy",
            "sub_section": "Casual Leave",
            "policy_number": "04",
            "policy_name": "Leave Policy",
            "audience": "both",
        },
        "SICK LEAVE": {
            "section": "Leave Policy",
            "sub_section": "Sick Leave",
            "policy_number": "04",
            "policy_name": "Leave Policy",
            "audience": "both",
        },
        "MATERNITY": {
            "section": "Leave Policy",
            "sub_section": "Maternity Leave",
            "policy_number": "04",
            "policy_name": "Leave Policy",
            "audience": "female",
        },
        "PATERNITY": {
            "section": "Leave Policy",
            "sub_section": "Paternity Leave",
            "policy_number": "04",
            "policy_name": "Leave Policy",
            "audience": "male",
        },
        "HOLIDAY": {
            "section": "Holidays",
            "sub_section": "General",
            "policy_number": "05",
            "policy_name": "Holidays Policy",
            "audience": "both",
        },
        "PROVIDENT": {
            "section": "Benefits",
            "sub_section": "Provident Fund",
            "policy_number": "06",
            "policy_name": "Benefits Policy",
            "audience": "both",
        },
        "ESIC": {
            "section": "Benefits",
            "sub_section": "ESIC",
            "policy_number": "06",
            "policy_name": "Benefits Policy",
            "audience": "both",
        },
        "TERMINATION": {
            "section": "Termination",
            "sub_section": "General",
            "policy_number": "10",
            "policy_name": "Termination Policy",
            "audience": "both",
        },
        "PERFORMANCE": {
            "section": "Performance Review",
            "sub_section": "General",
            "policy_number": "09",
            "policy_name": "Performance Review Policy",
            "audience": "both",
        },
    }

    # Simple text parsing - split by common delimiters
    lines = text.split("\n")
    current_section = "General"
    current_policy = {
        "section": "General",
        "sub_section": "General",
        "policy_number": "00",
        "policy_name": "General",
        "audience": "both",
    }
    content_buffer = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line is a section header
        for key, metadata in section_mapping.items():
            if key.lower() in line.lower():
                # Save previous section if exists
                if content_buffer:
                    content = " ".join(content_buffer)
                    if len(content) > 50:  # Only save non-trivial content
                        sections.append((content, current_policy.copy()))
                    content_buffer = []
                current_policy = metadata.copy()
                break

        content_buffer.append(line)

    # Save last section
    if content_buffer:
        content = " ".join(content_buffer)
        if len(content) > 50:
            sections.append((content, current_policy.copy()))

    return sections


def embed_policy():
    """Load PDF and embed into ChromaDB"""
    print("Loading PDF...")

    if not os.path.exists(PDF_PATH):
        print(f"Error: {PDF_PATH} not found")
        return

    # Load PDF
    loader = PyPDFLoader(PDF_PATH)
    pages = loader.load()

    print(f"Loaded {len(pages)} pages")

    # Combine all text
    full_text = "\n".join([page.page_content for page in pages])
    print(f"Total characters: {len(full_text)}")

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ". ", " "]
    )

    chunks = text_splitter.split_text(full_text)
    print(f"Created {len(chunks)} chunks")

    # Create metadata for each chunk
    metadatas = []
    for chunk in chunks:
        # Simple metadata assignment based on content
        metadata = {
            "policy_number": "04",
            "policy_name": "Leave Policy",
            "section": "Leave Policy",
            "sub_section": "General",
            "audience": "both",
            "source": "NovaHR_Company_Policy_Notebook.pdf",
        }

        # Refine metadata based on chunk content
        chunk_lower = chunk.lower()
        if "earned leave" in chunk_lower or "el" in chunk_lower:
            metadata["sub_section"] = "Earned Leave"
            metadata["policy_number"] = "04"
        elif "casual leave" in chunk_lower or "cl" in chunk_lower:
            metadata["sub_section"] = "Casual Leave"
            metadata["policy_number"] = "04"
        elif "sick leave" in chunk_lower or "sl" in chunk_lower:
            metadata["sub_section"] = "Sick Leave"
            metadata["policy_number"] = "04"
        elif "maternity" in chunk_lower:
            metadata["sub_section"] = "Maternity Leave"
            metadata["policy_number"] = "04"
            metadata["audience"] = "female"
        elif "paternity" in chunk_lower:
            metadata["sub_section"] = "Paternity Leave"
            metadata["policy_number"] = "04"
            metadata["audience"] = "male"
        elif "shift" in chunk_lower or "timing" in chunk_lower:
            metadata["section"] = "Attendance & Work Timing"
            metadata["sub_section"] = "Shift Timing"
            metadata["policy_number"] = "01"
        elif "holiday" in chunk_lower:
            metadata["section"] = "Holidays"
            metadata["sub_section"] = "General"
            metadata["policy_number"] = "05"
        elif "provident" in chunk_lower or "pf" in chunk_lower:
            metadata["section"] = "Benefits"
            metadata["sub_section"] = "Provident Fund"
            metadata["policy_number"] = "06"
        elif "esic" in chunk_lower:
            metadata["section"] = "Benefits"
            metadata["sub_section"] = "ESIC"
            metadata["policy_number"] = "06"
        elif "termination" in chunk_lower:
            metadata["section"] = "Termination"
            metadata["sub_section"] = "General"
            metadata["policy_number"] = "10"
        elif "performance" in chunk_lower:
            metadata["section"] = "Performance Review"
            metadata["sub_section"] = "General"
            metadata["policy_number"] = "09"

        metadatas.append(metadata)

    # Create embeddings
    print("Creating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Create chroma_db directory if not exists
    os.makedirs(DB_DIRECTORY, exist_ok=True)

    # Store in ChromaDB (persistent in data directory)
    print("Storing in ChromaDB...")
    db = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
        collection_name=COLLECTION_NAME,
        persist_directory=DB_DIRECTORY,
    )

    print(f"Successfully embedded {len(chunks)} chunks into ChromaDB")
    print(f"Collection: {COLLECTION_NAME}")

    # Test retrieval
    print("\nTesting retrieval...")
    test_query = "casual leave"
    results = db.similarity_search(test_query, k=2)
    print(f"Query: '{test_query}'")
    for i, doc in enumerate(results):
        content = doc.page_content[:100].encode("ascii", "replace").decode("ascii")
        print(f"  {i + 1}. {content}...")
        print(f"      Metadata: {doc.metadata}")

    return db


if __name__ == "__main__":
    embed_policy()
