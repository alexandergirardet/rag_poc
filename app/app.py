import chromadb
from typing import Optional
from dotenv import load_dotenv
# llama modules
from llama_index.llms import Ollama
from llama_index import VectorStoreIndex, ServiceContext#
from llama_index.storage.storage_context import StorageContext
from llama_index.vector_stores import ChromaVectorStore
# Custom Connector and Reader
from MongoConnector import MongoConnector
from MongoReader import MongoReader


class DataProcessingPipeline:
    def __init__(self, mongo_db_uri: str, mongo_db_name: str, mongo_collection_name: str, mongo_data_path: str,
                 chromadb_url: str):
        """Initializes the pipeline with MongoDB and ChromaDB configuration."""
        self.mongo_db_uri = mongo_db_uri
        self.mongo_db_name = mongo_db_name
        self.mongo_collection_name = mongo_collection_name
        self.mongo_data_path = mongo_data_path
        self.chromadb_url = chromadb_url
        # client
        self.chroma_client = None

    def load_data_to_mongo(self):
        """Loads data into MongoDB to mock Unstructured Data Source."""
        connector = MongoConnector(
            db_uri=self.mongo_db_uri,
            db_name=self.mongo_db_name,
            collection_name=self.mongo_collection_name,
            data_path=self.mongo_data_path
        )
        # Put data into MongoDB
        connector.run()

    def retrieve_data_from_mongo(self) -> Optional[list]:
        """Retrieves data from MongoDB."""
        try:
            loader = MongoReader(uri=self.mongo_db_uri)
            return loader.load_data(
                self.mongo_db_name, self.mongo_collection_name, metadata_names=None, field_names=["Article"]
            )
        except Exception as e:
            print(f"An error occurred while retrieving data: {e}")
            return None

    def process_data_with_chromadb(self, documents):
        """Processes data with ChromaDB."""
        try:
            # Create ChromoaDB client and store
            self.chroma_client = chromadb.HttpClient(self.chromadb_url)
            self.chroma_client.delete_collection("articles")
            chroma_collection = self.chroma_client.get_or_create_collection("articles")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            print("ChromaDB client and store created.")
            # Initialize Ollama and ServiceContext
            llm = Ollama(model="mixtral")
            service_context = ServiceContext.from_defaults(llm=llm, embed_model="local")
            # Create VectorStoreIndex in ChromaDB
            # The default chunk size is 1024, while the default chunk overlap is 20.
            VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                service_context=service_context,
                show_progress=True,
            )
        except Exception as e:
            print(f"An error occurred during processing: {e}")

    def query_index(self, query: str):
        llm = Ollama(model="mixtral", request_timeout=300.0)
        service_context = ServiceContext.from_defaults(llm=llm, embed_model="local")
        # Create VectorStoreIndex and query engine with a similarity threshold of 20
        chroma_collection = self.chroma_client.get_or_create_collection("articles")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store, service_context=service_context)
        query_engine = index.as_query_engine(similarity_top_k=20)
        response = query_engine.query(query)
        print(response)

    def run(self):
        """Runs the entire data processing pipeline."""
        self.load_data_to_mongo()
        documents = self.retrieve_data_from_mongo()
        documents = documents[:100]
        if documents:
            self.process_data_with_chromadb(documents)


if __name__ == "__main__":
    load_dotenv()

    pipeline = DataProcessingPipeline(
        mongo_db_uri="mongodb://localhost:27017/",
        mongo_db_name="unstructured_data_store",
        mongo_collection_name="articles",
        mongo_data_path="../data/Articles.csv",
        chromadb_url="http://localhost:8000"
    )
    pipeline.run()
    pipeline.query_index("Tell me about when Oil prices fell in Asia")

