# tools/serp.py
import os
from serpapi import GoogleSearch

def run(query=None, search_type="web", location="South Korea", hl="ko", gl="kr", num=5):
    """
    query: 검색할 자연어 질의
    search_type: 'web'(기본), 'news', 'images', 'videos', 'scholar', 'answer_box', 'knowledge_graph', 'people_also_ask'
    location: 검색 위치(예: 'South Korea')
    hl: 언어 코드(예: 'ko')
    gl: 국가 코드(예: 'kr')
    num: 결과 개수(기본 5)
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return "SerpAPI API 키(SERPAPI_API_KEY)가 환경 변수(.env)에 설정되어 있지 않습니다."
    if not query or not query.strip():
        return "검색할 쿼리를 입력해 주세요."
    try:
        params = {
            "q": query,
            "api_key": api_key,
            "location": location,
            "hl": hl,
            "gl": gl,
            "num": num
        }
        # 검색 엔진/타입 지정
        if search_type == "news":
            params["engine"] = "google_news"
        elif search_type == "images":
            params["engine"] = "google_images"
        elif search_type == "videos":
            params["engine"] = "youtube"
        elif search_type == "scholar":
            params["engine"] = "google_scholar"
        else:
            params["engine"] = "google"
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # 특수 SERP 박스 추출
        if search_type == "answer_box":
            answer_box = results.get("answer_box")
            if answer_box:
                answer = answer_box.get("answer") or answer_box.get("snippet") or answer_box.get("title")
                return f"[Answer Box]\n{answer}"
            else:
                return "Answer Box(즉답 박스) 정보를 찾을 수 없습니다."
        elif search_type == "knowledge_graph":
            kg = results.get("knowledge_graph")
            if kg:
                lines = [f"{k}: {v}" for k, v in kg.items()]
                return "[Knowledge Graph]\n" + "\n".join(lines)
            else:
                return "Knowledge Graph 정보를 찾을 수 없습니다."
        elif search_type == "people_also_ask":
            paa = results.get("related_questions") or results.get("people_also_ask")
            if paa:
                lines = [f"- {q.get('question')}" for q in paa if 'question' in q]
                return "[People Also Ask]\n" + "\n".join(lines)
            else:
                return "People Also Ask(함께 묻는 질문) 정보를 찾을 수 없습니다."
        
        # 일반 결과(웹, 뉴스, 이미지, 동영상, 학술)
        if search_type == "news":
            news_results = results.get("news_results", [])
            if not news_results:
                return f"'{query}'에 대한 뉴스 검색 결과를 찾을 수 없습니다."
            lines = []
            for idx, item in enumerate(news_results[:num], 1):
                title = item.get("title", "제목 없음")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                lines.append(f"{idx}. {title}\n{snippet}\n{link}")
            return "\n\n".join(lines)
        elif search_type == "images":
            images = results.get("images_results", [])
            if not images:
                return f"'{query}'에 대한 이미지 검색 결과를 찾을 수 없습니다."
            lines = []
            for idx, item in enumerate(images[:num], 1):
                title = item.get("title", "이미지")
                link = item.get("original", "")
                lines.append(f"{idx}. {title}\n{link}")
            return "\n\n".join(lines)
        elif search_type == "videos":
            videos = results.get("video_results", [])
            if not videos:
                return f"'{query}'에 대한 동영상 검색 결과를 찾을 수 없습니다."
            lines = []
            for idx, item in enumerate(videos[:num], 1):
                title = item.get("title", "동영상")
                link = item.get("link", "")
                snippet = item.get("description", "")
                lines.append(f"{idx}. {title}\n{snippet}\n{link}")
            return "\n\n".join(lines)
        elif search_type == "scholar":
            scholar = results.get("organic_results", [])
            if not scholar:
                return f"'{query}'에 대한 학술 검색 결과를 찾을 수 없습니다."
            lines = []
            for idx, item in enumerate(scholar[:num], 1):
                title = item.get("title", "제목 없음")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                lines.append(f"{idx}. {title}\n{snippet}\n{link}")
            return "\n\n".join(lines)
        else:  # 기본: 웹검색
            organic = results.get("organic_results", [])
            if not organic:
                return f"'{query}'에 대한 검색 결과를 찾을 수 없습니다."
            lines = []
            for idx, item in enumerate(organic[:num], 1):
                title = item.get("title", "제목 없음")
                link = item.get("link", "")
                snippet = item.get("snippet", "")
                lines.append(f"{idx}. {title}\n{snippet}\n{link}")
            return "\n\n".join(lines)
    except Exception as e:
        return f"검색 정보를 가져오는 중 오류 발생: {e}"
