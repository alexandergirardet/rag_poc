import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from llama_index import SimpleDirectoryReader
import chromadb
from pymongo import MongoClient
from llama_index import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext

from llama_index import (
    VectorStoreIndex,
    get_response_synthesizer,
)

from llama_index.retrievers import VectorIndexRetriever
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.postprocessor import SimilarityPostprocessor

from dotenv import load_dotenv
import os
import logging

# Path to your .env file
env_path = '/Users/alexander.girardet/Code/Personal/projects/rag_poc/.env'

# Load the environment variables
load_dotenv(dotenv_path=env_path)

# openai.api_key = st.secrets.openai_key
st.header("Fetch your relevant articles")

if "messages" not in st.session_state.keys(): # Initialize the chat message history
    st.session_state.messages = [
        {"role": "assistant", "content": "Find your relevant articles!"}
    ]

@st.cache_resource(show_spinner=True)
def load_data(chroma_collection_name = "articles"):
    with st.spinner(text="Loading and indexing the LiveScore docs – hang tight! This should take 1-2 minutes."):

        # initialize client, setting path to save data
        remote_db = chromadb.HttpClient()
        chroma_collection = remote_db.get_or_create_collection(chroma_collection_name)

        # assign chroma as the vector_store to the context
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # load your index from stored vectors
        index = VectorStoreIndex.from_vector_store(
            vector_store, storage_context=storage_context
        )  # This will get your index without re-creating the embeddings and just use the data from persistent storage

        st.write("Index loaded!")
        return index

def get_retriever(index):
    """
    This function creates a query engine from an index. Pass it an index.
    :param index:
    :return:
    """
    # configure retriever
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=10,
    )

    return retriever

def connect_to_client(port=27017, host="localhost", db_name="unstructured_data_store", collection="articles"):
    client = MongoClient(f"mongodb://{host}:{port}/")  # Hosted with Docker

    try:
        db = client[db_name]
    except:
        logging.error("Could not connect to MongoDB, please set a valid database name")

    # Access collection
    try:
        collection = db[collection]
    except:
        logging.error("Could not connect to MongoDB, please set a valid collection name")

    return client, db, collection

mongo_collection = connect_to_client()

def fetch_article(article_number=None, collection=None):
    if article_number:
        document = collection.find_one({"articleId": article_number})
        st.write(f"User has sent the following prompt: {document['Article']}")
        return document
    else:
        return None

index = load_data(chroma_collection_name="articles")
retriever = get_retriever(index)

prompt = st.chat_input("Say something")

if prompt:
    st.write(f"User has sent the following prompt: {prompt}")
    nodes = retriever.retrieve(prompt)

    node_ids = [node.metadata["articleId"] for node in nodes]

with st.sidebar:
    st.write("Source Documents info:")
    if nodes:
        for node in nodes:  # I need to add links here.
            title = node.metadata["Date"]
            id = node.metadata["articleId"]
            text = node.text

            container = st.container(border=True)
            container.write(f"Article Title: {title}")
            container.write(f"Article ID: {id}")
            container.write(f"Source text: {text}")
            container.write(f"Relevance score: {node.score}")

with st.form(key='number_form'):
    selected_number = st.selectbox('Choose which article is most relevant', list(set(node_ids)))

    # # article = fetch_article(selected_number, mongo_collection)
    #
    # st.write(f"User has selected the following article: {article['Article']}")

    # Submit button for the form
    submit_button = st.form_submit_button(label='Submit', on_click=fetch_article,
                                          kwargs={
                                              "article_number": selected_number,
                                              "collection": mongo_collection})


if submit_button:
    # The form was submitted; perform actions based on the selection
    st.write(f'You selected: {selected_number}')




