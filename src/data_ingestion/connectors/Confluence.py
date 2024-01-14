url = "https://livescoregroup.atlassian.net/wiki/spaces/LD/pages"

import json
import os
import base64
from typing import Any, Dict, List, Optional
import requests

spaces_of_interest = ["LiveScore Group", "LiveScore Data"]

base_url = os.environ["CONFLUENCE_URL"]
full_url = base_url + "/wiki/api/v2"

confluence_url = os.environ["CONFLUENCE_URL"]
email = os.environ['LIVESCORE_EMAIL']
api_token = os.environ['CONFLUENCE_API_TOKEN']

credentials = f'{email}:{api_token}'
encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {
    "Authorization": f"Basic {encoded_credentials}",
    "Accept": "application/json"
}

class ConfluentPage:
    confluent_id: str = None
    createdAt: str = None
    parentId: str = None
    title: str = None
    spaceId: str = None
    status: str = None

    metadata: Dict[str, str]

    def __init__(self, metadata: Dict, headers: Dict = None):
        self.metadata = metadata
        self.set_metadata(metadata)

    def set_metadata(self, metadata: Dict):
        self.confluent_id = metadata.get("id")
        self.parentType = metadata.get("parentType")
        self.title = metadata.get("title")
        self.createdAt = metadata.get("createdAt")
        self.parentId = metadata.get("parentId")
        self.spaceId = metadata.get("spaceId")
        self.status = metadata.get("status")

    def set_text(self, text):
        if self.text is None:
            self.text = text
        return self.text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.confluent_id,
            "parentType": self.parentType,
            "title": self.title,
            "createdAt": self.createdAt,
            "status": self.status,
            "parentId": self.parentId,
            "spaceId": self.spaceId,
            "text": self.text,
            "metadata": self.metadata
        }

space_key = "LD"

def space_filter(space: Dict, spaces_of_interest):
    if space['type'] == "personal":
        return False

    elif space['name'] not in spaces_of_interest:
        return False
    else:
        return True


def get_all_spaces():
    space_names = []
    spaces = get_spaces(space_names)
    with open(f"spaces.json", "w") as file:
        file.write(json.dumps(space_names))
    return space_names


def get_spaces(names, next_url=None):
    url = next_url if next_url else base_url + "wiki/api/v2/spaces"
    print(url)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:

        data = response.json()
        # Filter out
        names += [{"key": space['key'],
                   "name": space['name'],
                   "id": space['id'],
                   "type": space['type'],
                   "homepageId": space['homepageId']} for space in data['results'] if
                  space_filter(space, spaces_of_interest)]

        links = data['_links']
        print(links)
        if 'next' in links:
            next_url = base_url + links['next']
            get_spaces(names, next_url)

        else:
            return names
    else:
        print("Failed to fetch spaces")


def get_pages_in_space(space, pages, next_url=None):
    space_id = space['id']
    url = next_url if next_url else base_url + f"wiki/api/v2/spaces/{space_id}/pages"
    print(url)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:

        data = response.json()

        pages += [{"id": page['id'],
                   "parentType": page['parentType'],
                   "createdAt": page['createdAt'],
                   "title": page['title'],
                   "parentId": page['parentId'],
                   "spaceId": page['spaceId'],
                   "status": page['status']} for page in data['results']]

        links = data['_links']
        print(links)
        if 'next' in links:
            next_url = base_url + links['next']
            get_pages_in_space(space, pages, next_url)

        else:
            return pages
    else:
        print("Failed to fetch spaces")


def download_page_content(page_id):
    url = f"{base_url}/content/{page_id}?expand=body.storage"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()['body']['storage']['value']
        with open(f"{page_id}.html", "w") as file:
            file.write(content)
    else:
        print(f"Failed to download page {page_id}")

with open(f"/Users/alexander.girardet/Code/Personal/projects/A3_SecondBrain/A3/data/spaces.json", "r") as file:
    space_names = json.loads(file.read())

with open(f"/Users/alexander.girardet/Code/Personal/projects/A3_SecondBrain/A3/data/pages.json", "r") as file:
    pages = json.loads(file.read())