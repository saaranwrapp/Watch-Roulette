import os
import random
import requests
import streamlit as st
from dotenv import load_dotenv

# ---------- Page config ----------
st.set_page_config(
    page_title="Watch Roulette",
    page_icon="🎲",
    layout="wide",
)

# ---------- Custom CSS ----------
def add_custom_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

/* Overall app – soft pink */
.stApp {
    font-family: "Nunito", system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
    background-color: #DFC1CB;  /* pale pink */
    color: #3B1020;             /* dark plum text */
}

/* Main content container */
.block-container {
    max-width: 900px;
    padding-top: 3rem;
    padding-bottom: 3rem;
}

/* Sidebar – medium pink */
[data-testid="stSidebar"] {
    background-color: #C48197;
    border-right: none;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] label {
    color: #FDF6F8 !important;
    font-family: "Nunito", system-ui, sans-serif;
}

/* Multiselect pills in sidebar */
[data-baseweb="tag"] {
    background-color: #FDF6F8 !important;
    color: #3B1020 !important;
    font-family: "Nunito", system-ui, sans-serif;
}

/* Buttons – pink */
.stButton > button {
    background-color: #B66681;      /* deeper pink */
    color: #FDF6F8;
    border-radius: 999px;
    padding: 0.45rem 1.3rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: none;
    border: none;
    box-shadow: 0 6px 14px rgba(0, 0, 0, 0.22);
    font-family: "Nunito", system-ui, sans-serif;
}
.stButton > button:hover {
    background-color: #A25271;
    transform: translateY(-1px);
    cursor: pointer;
}
[data-testid="stSidebar"] .stButton {
    margin-top: 1.5rem;
}

/* Title + headings */
h1 {
    font-family: "Playfair Display", serif;
    font-size: 3rem;
    text-align: center;
    margin-bottom: 0.5rem;
    color: #3B1020;
}
h3, p, li {
    font-family: "Nunito", system-ui, sans-serif;
    color: #3B1020;
}
.watch-card h2 {
    font-family: "Playfair Display", serif !important;
    color: #3B1020;
}

/* Card layout */
.watch-card-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
}
.watch-card {
    padding: 1.8rem 2rem;
    border-radius: 18px;
    background-color: #FDF6F8;
    max-width: 620px;
    width: 100%;
    box-shadow: 0 14px 35px rgba(0,0,0,0.18);
    border: 2px solid #C48197;
}
.watch-card-inner {
    display: flex;
    gap: 1.25rem;
    align-items: center;   /* center vertically */
}

.watch-card-text {
    flex: 1;
}
.watch-card-poster {
    flex: 0 0 35%;
}
.watch-card-poster img {
    width: 100%;
    height: auto;          /* keep natural aspect ratio */
    border-radius: 12px;
    object-fit: contain;   /* or just remove this line */
    max-height: 320px;     /* optional safety cap; you can drop this too */
}

}
.watch-card h2 {
    font-family: "Playfair Display", serif;
}
</style>
        """,
        unsafe_allow_html=True,
    )

# ---------- Notion setup ----------
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# ---------- Notion helpers ----------
def get_database_options():
    """
    Fetch Language, Type, and Genre(s) options from the Notion database.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    data = res.json()
    props = data["properties"]

    language_opts = [opt["name"] for opt in props["Language"]["multi_select"]["options"]]
    type_opts = [opt["name"] for opt in props["Type"]["select"]["options"]]
    genre_opts = [opt["name"] for opt in props["Genre(s)"]["multi_select"]["options"]]

    return {
        "languages": sorted(language_opts),
        "types": sorted(type_opts),
        "genres": sorted(genre_opts),
    }


def pick_random(languages=None, content_types=None, genres=None):
    """
    Query Notion and return one random matching page (or None).
    Uses:
      - Language (multi-select)
      - Type (select)
      - Genre(s) (multi-select)
      - Release Date (select)
      - Poster (url) [optional]
      - Link (url) [optional]
    """
    filters = []

    if languages:
        filters.append({
            "or": [
                {"property": "Language", "multi_select": {"contains": lang}}
                for lang in languages
            ]
        })

    if content_types:
        filters.append({
            "or": [
                {"property": "Type", "select": {"equals": t}}
                for t in content_types
            ]
        })

    if genres:
        filters.append({
            "or": [
                {"property": "Genre(s)", "multi_select": {"contains": g}}
                for g in genres
            ]
        })

    payload = {}
    if filters:
        payload["filter"] = {"and": filters}

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    res = requests.post(url, headers=HEADERS, json=payload)

    if not res.ok:
        st.error(f"Error from Notion while querying:\n\n{res.status_code} {res.text}")
        return None

    results = res.json().get("results", [])
    if not results:
        return None

    page = random.choice(results)
    props = page["properties"]

    # Title
    title_prop = props.get("Name", {})
    title_parts = title_prop.get("title", [])
    title = title_parts[0]["plain_text"] if title_parts else "Untitled"

    # Language
    lang_prop = props.get("Language", {})
    lang_vals = lang_prop.get("multi_select", []) or []
    language_value = ", ".join(v["name"] for v in lang_vals) if lang_vals else "Unknown"

    # Type
    type_prop = props.get("Type", {})
    type_sel = type_prop.get("select")
    type_value = type_sel["name"] if type_sel else "Unknown"

    # Genres
    genres_prop = props.get("Genre(s)", {})
    genres_vals = genres_prop.get("multi_select", []) or []
    genre_list = [g["name"] for g in genres_vals] if genres_vals else []

    # Release Date
    release_prop = props.get("Release Date", {})
    release_sel = release_prop.get("select")
    release_value = release_sel["name"] if release_sel else "Unknown"

    # Poster
    poster_url = ""
    poster_prop = props.get("Poster")
    if isinstance(poster_prop, dict) and poster_prop.get("type") == "url":
        poster_url = (poster_prop.get("url") or "").strip()

    # External Link
    external_link = ""
    link_prop = props.get("Link")
    if isinstance(link_prop, dict) and link_prop.get("type") == "url":
        external_link = (link_prop.get("url") or "").strip()

    return {
        "title": title,
        "language": language_value,
        "type": type_value,
        "genres": genre_list,
        "release": release_value,
        "url": page.get("url", ""),
        "poster_url": poster_url,
        "external_link": external_link,
    }

# ---------- Streamlit UI ----------
def main():
    add_custom_css()

    st.title("Watch Roulette")

    # Load dropdown options
    try:
        options = get_database_options()
    except Exception as e:
        st.error(f"Error talking to Notion while loading options:\n\n{e}")
        return

    st.sidebar.header("Filters")

    sel_languages = st.sidebar.multiselect(
        "Languages", options["languages"], default=[]
    )
    sel_types = st.sidebar.multiselect("Types", options["types"], default=[])
    sel_genres = st.sidebar.multiselect("Genres", options["genres"], default=[])

    if st.sidebar.button("Pick something!"):
        try:
            rec = pick_random(
                languages=sel_languages or None,
                content_types=sel_types or None,
                genres=sel_genres or None,
            )
        except Exception as e:
            st.error(f"Error talking to Notion while picking:\n\n{e}")
            return

        if rec is None:
            st.warning("No matches found for those filters.")
            return

        # "You should watch" only after we have a rec
        st.markdown(
            '<h3 style="text-align:center; margin-top: 1.5rem;">You should watch:</h3>',
            unsafe_allow_html=True,
        )

        genres_str = ", ".join(rec["genres"]) if rec["genres"] else "—"

        # Poster HTML (right side), only if URL exists
        poster_html = ""
        if rec.get("poster_url"):
            poster_html = f"""
<div class="watch-card-poster">
<img src="{rec['poster_url']}" alt="Poster for {rec['title']}" />
</div>
"""

        # Build card HTML with NO leading spaces on lines
        card_html = f"""
<div class="watch-card-wrapper">
<div class="watch-card">
<div class="watch-card-inner">
<div class="watch-card-text">
<h2 style="margin-top:0;margin-bottom:0.8rem;font-size:1.8rem;">{rec['title']}</h2>
<p><strong>Type:</strong> {rec['type']}</p>
<p><strong>Language:</strong> {rec['language']}</p>
<p><strong>Genres:</strong> {genres_str}</p>
<p><strong>Release:</strong> {rec['release']}</p>
"""

        if rec.get("external_link"):
            card_html += f"""
<p style="margin-top:1rem;">
<a href="{rec['external_link']}" target="_blank"
   style="color:#B66681;text-decoration:none;font-weight:500;">
Watch here ↗
</a>
</p>
"""

        card_html += f"""
<p style="margin-top:0.3rem;">
<a href="{rec['url']}" target="_blank"
   style="color:#B66681;text-decoration:none;font-weight:500;">
Open in Notion ↗
</a>
</p>
</div>
{poster_html}
</div>
</div>
</div>
"""

        st.markdown(card_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
