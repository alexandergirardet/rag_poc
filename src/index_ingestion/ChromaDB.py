import chromadb
from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext
from MongoReader import SimpleMongoReader
from llama_index import SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from llama_index.text_splitter import SentenceSplitter
from llama_index import Document
import logging
from llama_index.embeddings import OpenAIEmbedding
from llama_index.text_splitter import SentenceSplitter
from llama_index.extractors import TitleExtractor
from llama_index.ingestion import IngestionPipeline, IngestionCache

from dotenv import load_dotenv

import os

logging.basicConfig(level=logging.INFO)

# VALUES TO PARAMETERIZE
chunk_size = 100
chunk_overlap = 0

# Path to your .env file
env_path = '/Users/alexander.girardet/Code/Personal/projects/rag_poc/.env'

# Load the environment variables, get API key
load_dotenv(dotenv_path=env_path)

def get_chroma_collection(chroma_collection = "articles"):
    remote_db = chromadb.HttpClient()
    chroma_collection = remote_db.get_or_create_collection(chroma_collection)

    return chroma_collection

def get_vector_store(chroma_collection):
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return vector_store

query_dict = {}
field_names = ["Article"]
reader = SimpleMongoReader(uri="mongodb://localhost:27017/")
documents = reader.load_data(
    "unstructured_data_store", "articles", metadata_names=["NewsType", "_id"], field_names=field_names
)

if __name__ == "__main__":
    chroma_collection = get_chroma_collection(chroma_collection="articles")
    vector_store = get_vector_store(chroma_collection=chroma_collection)

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    query_dict = {}
    field_names = ["Article"]
    reader = SimpleMongoReader(uri="mongodb://localhost:27017/")

    documents = reader.load_data(
        "unstructured_data_store", "articles", metadata_names=["NewsType", "articleId", "Date"],
        field_names=field_names, query_dict=query_dict
    )

    # create the pipeline with transformations
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
            OpenAIEmbedding(),  # Create Local Embedding model
        ]
    )

    nodes = pipeline.run(documents=documents[0:20]) # Single batch for testing

    logging.info(f"Indexing {len(nodes)} nodes")
    logging.info(f"Count of collection before: {chroma_collection.count()}")

    index = VectorStoreIndex(nodes, storage_context=storage_context)  # Data is loaded into chroma

    logging.info(f"Indexing complete, Count of collection after: {chroma_collection.count()}")





