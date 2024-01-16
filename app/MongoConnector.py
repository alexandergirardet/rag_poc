import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm
from Models import NewsArticle


class MongoConnector:
    def __init__(self, db_uri, db_name, collection_name, data_path):
        """Initializes the MongoConnector with MongoDB URI, database name, collection name, and data path."""
        self.db_uri = db_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.data_path = data_path

        self.client = None
        self.db = None
        self.collection = None

    def connect_to_database(self):
        """Connects to the MongoDB database."""
        try:
            self.client = MongoClient(self.db_uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
        except Exception as e:
            print(f"An error occurred while connecting to the database: {e}")

    def load_data(self):
        """Loads data from the CSV file and processes it."""
        try:
            articles = pd.read_csv(self.data_path, encoding='ISO-8859-1')
            articles['Date'] = pd.to_datetime(articles['Date'])  # In-flight data processing.
            return articles.to_dict(orient="records")
        except FileNotFoundError:
            print("The data file was not found.")
            return []
        except Exception as e:
            print(f"An error occurred while loading data: {e}")
            return []

    def insert_articles(self, article_batches):
        """Inserts articles into the MongoDB collection."""
        for article_json in tqdm(article_batches):
            try:
                article = NewsArticle(**article_json)
                article_processed_json = article.model_dump()
                self.collection.insert_one(article_processed_json)
            except Exception as e:
                print(f"An error occurred while inserting an article: {e}")

    def run(self):
        """Runs the data processing and insertion routine."""
        # See if data has been loaded.
        self.connect_to_database()
        num_docs = self.collection.count_documents({})
        if num_docs > 0:
            print(f"Data has already been loaded. {num_docs} documents found.")
            return
        # Otherwise Load Data
        article_batches = self.load_data()
        if article_batches:
            self.insert_articles(article_batches)


if __name__ == "__main__":
    connector = MongoConnector(
        "mongodb://localhost:27017/",
        "unstructured_data_store",
        "articles",
        "../data/Articles.csv"
    )
    connector.run()

