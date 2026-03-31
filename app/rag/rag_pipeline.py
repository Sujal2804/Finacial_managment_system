from langchain_community.document_loaders import PyPDFLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).parent / ".env"
print("Looking for .env at:", env_path)
print(".env exists:", env_path.exists())

load_dotenv(dotenv_path=env_path)

key = os.getenv("GROQ_API_KEY")
print("Key loaded:", key)


model = SentenceTransformer('all-MiniLM-L6-v2')


client = QdrantClient(":memory:")

collection_name = "documents"


try:
    client.get_collection(collection_name)
except:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )



def process_document(file_path):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".csv"):
        loader = CSVLoader(file_path)
    else:
        raise ValueError("Unsupported file type")

    docs = loader.load()

    print("RAW DOCS:", docs[:1])  # 🔥 DEBUG

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(docs)

    print("CHUNKS:", chunks[:2])  # 🔥 DEBUG

    return chunks



def store_embeddings(chunks):
    texts = [c.page_content for c in chunks]

    if not texts:
        raise ValueError("No text found in document")

    embeddings = model.encode(texts)

    print("TEXTS:", texts[:2])  # 🔥 DEBUG
    print("EMBEDDINGS COUNT:", len(embeddings))

    points = []

    for i, vec in enumerate(embeddings):
        points.append(
            PointStruct(
                id=i,
                vector=vec.tolist(),  # ✅ VERY IMPORTANT
                payload={"text": texts[i]}
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points
    )


def search(query):
    print("QUERY:", query)

    query_vector = model.encode([query])[0]

    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=5
    )

    print("RAW RESULTS:", results)  # 🔥 DEBUG

    return [r.payload["text"] for r in results.points]