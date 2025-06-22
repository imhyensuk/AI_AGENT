# tools/news.py
import os
from dotenv import load_dotenv
from newsapi import NewsApiClient
from googletrans import Translator

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def map_query_to_keyword(query):
    if not query or not query.strip():
        return "world"
    try:
        translator = Translator()
        translated = translator.translate(query, src='ko', dest='en')
        return translated.text
    except Exception:
        return query

def run(query=None):
    if not NEWS_API_KEY:
        return "NEWS_API_KEY가 설정되어 있지 않습니다."
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)
    articles = []
    if not query or not query.strip():
        response = newsapi.get_top_headlines(country="kr", page_size=5)
        articles = response.get("articles", [])
    else:
        q_en = map_query_to_keyword(query.strip())
        response = newsapi.get_top_headlines(q=q_en, country="kr", page_size=5)
        articles = response.get("articles", [])
        if not articles:
            response = newsapi.get_everything(q=q_en, language="en", sort_by="publishedAt", page_size=5)
            articles = response.get("articles", [])
    if not articles:
        return f"'{query}'(으)로 뉴스 결과를 찾을 수 없습니다."
    news_list = []
    for i, article in enumerate(articles):
        title = article.get("title", "제목 없음")
        description = article.get("description", "설명 없음")
        source = article.get("source", {}).get("name", "출처 없음")
        url = article.get("url", "")
        news_list.append(
            f"{i+1}. {title}\n- 요약: {description}\n- 출처: {source}\n- 링크: {url}"
        )
    return "\n\n".join(news_list)
