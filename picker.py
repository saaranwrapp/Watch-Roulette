import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def get_recommendation(languages=None, content_types=None, genres=None):
    """
    languages: list[str] or None  (Language is multi-select in Notion)
    content_types: list[str] or None  (Type is select)
    genres: list[str] or None  (Genre(s) is multi-select)
    """

    filters = []

    # ---- Language (multi_select) ----
    # OR between multiple chosen languages
    if languages:
        lang_filters = [
            {
                "property": "Language",
                "multi_select": {"contains": lang}
            }
            for lang in languages
        ]
        filters.append({"or": lang_filters})

    # ---- Type (select) ----
    # OR between multiple types
    if content_types:
        type_filters = [
            {
                "property": "Type",
                "select": {"equals": t}
            }
            for t in content_types
        ]
        filters.append({"or": type_filters})

    # ---- Genre(s) (multi_select) ----
    # OR between multiple genres
    if genres:
        genre_filters = [
            {
                "property": "Genre(s)",
                "multi_select": {"contains": g}
            }
            for g in genres
        ]
        filters.append({"or": genre_filters})

    payload = {}
    if filters:
        payload["filter"] = {"and": filters}

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    res = requests.post(url, headers=HEADERS, json=payload)

    if not res.ok:
        print("Error from Notion:")
        print(res.status_code, res.text)
        return

    results = res.json().get("results", [])
    if not results:
        print("No matches found for those filters.")
        return

    page = random.choice(results)
    props = page["properties"]

    # --- Read fields back out ---
    title_parts = props["Name"]["title"]
    title = title_parts[0]["plain_text"] if title_parts else "Untitled"

    # Language (multi-select)
    lang_prop = props["Language"]["multi_select"]
    lang_value = ", ".join(v["name"] for v in lang_prop) if lang_prop else "Unknown"

    # Type (select)
    type_prop = props["Type"]["select"]
    type_value = type_prop["name"] if type_prop else "Unknown"

    # Genres (multi-select)
    genres_prop = props["Genre(s)"]["multi_select"]
    genre_list = [g["name"] for g in genres_prop] if genres_prop else []

    # Release Date – handle date, number, or select
    release_prop = props.get("Release Date", {})
    rtype = release_prop.get("type")

    if rtype == "date":
        date_val = release_prop.get("date")
        release = date_val["start"] if date_val else "Unknown"
    elif rtype == "number":
        num = release_prop.get("number")
        release = str(num) if num is not None else "Unknown"
    elif rtype == "select":
        sel = release_prop.get("select")
        release = sel["name"] if sel else "Unknown"
    else:
        release = "Unknown"

    url_to_open = page.get("url", "")

    print("\nYou should watch:\n")
    print(f"- Title: {title}")
    print(f"- Type: {type_value}")
    print(f"- Language: {lang_value}")
    print(f"- Genres: {', '.join(genre_list) if genre_list else '—'}")
    print(f"- Release date: {release}")
    if url_to_open:
        print(f"- Notion link: {url_to_open}")


if __name__ == "__main__":
    # Languages – comma-separated (because your Language is multi-select)
    lang_input = input(
        "Languages (comma-separated, e.g. Chinese, Korean) or Enter to skip: "
    ).strip()
    languages = [s.strip() for s in lang_input.split(",") if s.strip()] or None

    print("Possible types: Movie, TV Show, Anime (Show), Anime (Movie)")
    type_input = input("Types (comma-separated) or Enter to skip: ").strip()
    content_types = [t.strip() for t in type_input.split(",") if t.strip()] or None

    genre_input = input(
        "Genres (comma-separated, e.g. Romance, Thriller) or Enter to skip: "
    ).strip()
    genres = [g.strip() for g in genre_input.split(",") if g.strip()] or None

    get_recommendation(languages=languages, content_types=content_types, genres=genres)
