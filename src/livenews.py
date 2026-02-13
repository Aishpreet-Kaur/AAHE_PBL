import requests
from datetime import datetime

API_KEY = "GEMINI_API_KEY"

def fetch_latest_news(query, from_time=None):
    url = "https://newsapi.org/v2/everything"
    
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": API_KEY
    }
    
    if from_time:
        params["from"] = from_time  # ISO timestamp

    response = requests.get(url, params=params)
    data = response.json()
    
    articles = []
    for a in data.get("articles", []):
        articles.append({
            "title": a["title"],
            "content": a["description"],
            "published_at": a["publishedAt"]
        })
    
    return articles
