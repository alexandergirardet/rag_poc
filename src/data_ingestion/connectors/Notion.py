from typing import Any, Dict, List, Optional
import requests
import os
from notion_client import Client
import dotenv

dotenv.load_dotenv()

notion_integration_token = os.environ.get("NOTION_INTEGRATION_TOKEN")


class Note:
    object: str = None
    notion_id: str = None
    created_time: str = None
    last_edited_time: str = None
    title: str = None
    page_url: str = None
    page_type: str = None
    text: str = None

    headers: Dict[str, str]
    metadata: Dict[str, str]

    def __init__(self, metadata: Dict, headers: Dict = None):
        self.metadata = metadata
        self.set_metadata(metadata)

    def set_metadata(self, metadata: Dict):
        self.object = metadata.get("object_type")
        self.notion_id = metadata.get("page_id")
        self.created_time = metadata.get("created_time")
        self.last_edited_time = metadata.get("last_edited_time")
        # self.title = metadata.get("title")
        self.page_url = metadata.get("page_url")
        self.page_type = metadata.get("page_type")

    def set_text(self, text):
        if self.text is None:
            self.text = text
        return self.text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object": self.object,
            "notion_id": self.notion_id,
            "created_time": self.created_time,
            "last_edited_time": self.last_edited_time,
            # "title": self.title,
            "page_url": self.page_url,
            "page_type": self.page_type,
            "text": self.text,
            "metadata": self.metadata
        }


class NotionReader:
    BLOCK_CHILD_URL_TMPL = "https://api.notion.com/v1/blocks/{block_id}/children"
    DATABASE_URL_TMPL = "https://api.notion.com/v1/databases/{database_id}/query"
    SEARCH_URL = "https://api.notion.com/v1/search"

    headers = {
        "Authorization": f"Bearer {notion_integration_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    @staticmethod
    def get_type(type):
        if type['select'] is not None:
            return type['select']['name']
        else:
            return None

    @staticmethod
    def get_metadata(page):

        page_id = page['id']
        object_type = page['object']
        created_time = page['created_time']
        last_edited_time = page['last_edited_time']
        page_url = page['url']
        page_type = NotionReader.get_type(page['properties']['Type'])

        return {
            'page_id': page_id,
            'object_type': object_type,
            'created_time': created_time,
            'last_edited_time': last_edited_time,
            'page_url': page_url,
            'page_type': page_type
        }

    def _read_block(block_id: str, num_tabs: int = 0) -> str:
        """Read a block."""
        done = False
        result_lines_arr = []
        cur_block_id = block_id
        while not done:
            block_url = NotionReader.BLOCK_CHILD_URL_TMPL.format(block_id=cur_block_id)
            query_dict: Dict[str, Any] = {}

            res = requests.request(
                "GET", block_url, headers=NotionReader.headers, json=query_dict
            )
            data = res.json()

            for result in data["results"]:
                result_type = result["type"]
                result_obj = result[result_type]

                cur_result_text_arr = []
                if "rich_text" in result_obj:
                    for rich_text in result_obj["rich_text"]:
                        # skip if doesn't have text object
                        if "text" in rich_text:
                            text = rich_text["text"]["content"]
                            prefix = "\t" * num_tabs
                            cur_result_text_arr.append(prefix + text)

                result_block_id = result["id"]
                has_children = result["has_children"]
                if has_children:
                    children_text = NotionReader._read_block(
                        result_block_id, num_tabs=num_tabs + 1
                    )
                    cur_result_text_arr.append(children_text)

                cur_result_text = "\n".join(cur_result_text_arr)
                result_lines_arr.append(cur_result_text)

            if data["next_cursor"] is None:
                done = True
                break
            else:
                cur_block_id = data["next_cursor"]

        return "\n".join(result_lines_arr)

    def read_page(page_id: str) -> str:
        """Read a page."""
        return NotionReader._read_block(page_id)


if __name__ == "__main__":
    notion = Client(auth="secret_7ILZpjQM14qXZyl30tNDWxzxBmQSOdSpmOevz4I9w5E")

    pages = notion.databases.query(
        **{
            "database_id": "ea1c070976cc484485f11752bb93737c",
        }
    )

    from notion_client.helpers import collect_paginated_api

    # Iterate over all pages in the database
    all_results = collect_paginated_api(
        notion.databases.query, database_id="ea1c070976cc484485f11752bb93737c"
    )

    journals = []

    for result in all_results:
        try:
            name_type = result['properties']['Type']['select']['name']
            if name_type == 'Daily':
                journals.append(result)
            else:
                print(name_type)
        except:
            print(None)

    notion_notes = []
    for page in journals:
        print(page['id'])
        metadata = NotionReader.get_metadata(page)
        notion_note = Note(metadata=metadata)

        notion_notes.append(notion_note)

    import json
    from tqdm import tqdm

    notion_objects: [Note] = []

    existing_ids = set()

    from pymongo import MongoClient

    client = MongoClient("mongodb://localhost:27017/")  # Hosted with Docker

    db = client["livescore"]

    pages_collection = db["journals"]

    journals = pages_collection.find({}, {"id": 1})

    journals = pages_collection.find({}, {"notion_id": 1})
    journal_ids = [journal['notion_id'] for journal in journals]

    data_file_path = "/Users/alexander.girardet/Code/Personal/projects/second_brain/knowledge_base/A3/data/journals_25.jsonl"

    with open(data_file_path, 'w') as file:
        for i, notion_page in tqdm(enumerate(notion_notes)):
            notion_id = notion_page.notion_id
            if notion_id in journal_ids:
                print("Id is already in set:", notion_id)
                pass
            else:
                text = NotionReader.read_page(notion_page.notion_id)
                notion_page.set_text(text)
                pages_collection.insert_one(notion_page.to_dict())
