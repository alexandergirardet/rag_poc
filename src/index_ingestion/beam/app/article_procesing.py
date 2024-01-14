from apache_beam.io.mongodbio import ReadFromMongoDB, WriteToMongoDB

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import logging
from sklearn.neighbors import BallTree
import pandas as pd
import math
import numpy as np
import datetime
from math import radians

MONGO_DB_URL = "mongodb://mongodb:27017/"

BATCH_SIZE = 50
COLLECTION = "articles"
DATABASE = "unstructured_data_store"
class ProcessElement(beam.DoFn):
    def setup(self):
        pass
    def process(self, element):
        pass

def run():
    with beam.Pipeline(options=PipelineOptions()) as pipeline:
        (pipeline | "Read from Mongo" >> ReadFromMongoDB(uri=MONGO_DB_URL,
                           db=DATABASE,
                           coll=COLLECTION) # Only return the id and the location
        | 'Batch Elements' >> beam.BatchElements(min_batch_size=BATCH_SIZE, max_batch_size=BATCH_SIZE)
        | 'Process each element' >> beam.ParDo(ProcessElement())
        | 'Write to MongoDB' >> WriteToMongoDB(uri=MONGO_DB_URL) # Create a Write to Chroma transformation
         )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()