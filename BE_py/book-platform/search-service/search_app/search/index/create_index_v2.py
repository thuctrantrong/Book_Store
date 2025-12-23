import json
from search_app.search.client import get_os_client

INDEX = "books_v2"
MAPPING_PATH = "app/search/index/mapping_books_v2.json"


def main():
    client = get_os_client()
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        body = json.load(f)

    if client.indices.exists(index=INDEX):
        print(f"[SKIP] index exists: {INDEX}")
    else:
        client.indices.create(index=INDEX, body=body)
        print(f"[OK] created index: {INDEX}")


if __name__ == "__main__":
    main()
