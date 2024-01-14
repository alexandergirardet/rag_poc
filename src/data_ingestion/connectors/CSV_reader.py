from typing import Any, Dict, List, Optional
import os
import dotenv
import logging

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from tqdm import tqdm
from pymongo import MongoClient
import pandas as pd


def read_csv(data_path: str) -> pd.DataFrame:
    return pd.read_csv(data_path, encoding='ISO-8859-1')

def process_csv(data_path: str) -> pd.DataFrame:
    df = read_csv(data_path)
    return df


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

class NewsArticle(BaseModel): # Allows us to specify any preprocessing steps
    Article: str
    Heading: str
    Date: str
    NewsType: str
    articleId: int

def df_to_dict(df: pd.DataFrame) -> List[Dict[str, Any]]:
    return df.to_dict('records')

def validate_data(data: List[Dict[str, Any]]) -> List[NewsArticle]:
    validated_data = []
    for item in tqdm(data):
        article = NewsArticle(**item)
        validated_data.append(article)
    return validated_data

if __name__ == "__main__":
    data_path = "/Users/alexander.girardet/Code/Personal/projects/rag_poc/data/Articles.csv"
    df = process_csv(data_path)
    data = df_to_dict(df)

    # add a unique id to each article
    for i, item in enumerate(data):
        item['articleId'] = i

    validated_data = validate_data(data)

    for valid_data in validated_data:
        print(valid_data.dict())

    valid_data_json = [valid_data.dict() for valid_data in validated_data]

    client, db, collection = connect_to_client(db_name="unstructured_data_store", collection="articles")

    try:
        collection.insert_many(valid_data_json)
        logging.info("Successfully inserted data into MongoDB")
    except:
        logging.error("Could not insert data into MongoDB")

    # client, db, collection = connect_to_client()
    # collection.insert_many(data)
    # client.close()
    # print("Done!")
