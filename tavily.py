# tools/tavily.py
import os
from tavily import TavilyClient

api_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=api_key)

def run(
    query,
    max_results=5,
    topic="general",           # "general", "news", "finance" 등
    include_answer=True,       # LLM이 생성한 요약 포함
    include_raw_content=False, # 원문 전체 포함
    include_images=False,      # 관련 이미지 포함
    search_depth="advanced",   # "basic" or "advanced"
    time_range=None,           # "day", "week", "month", "year" 등
    include_domains=None,      # ['wikipedia.org', ...] 등
    exclude_domains=None       # ['reddit.com', ...] 등
):
    """
    Tavily Search Tool - 실시간 웹/뉴스/금융/이미지/원문 검색 및 요약
    """
    try:
        response = tavily_client.search(
            query=query,
            max_results=max_results,
            topic=topic,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
            include_images=include_images,
            search_depth=search_depth,
            time_range=time_range,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
        results = response.get("results", [])
        answer = response.get("answer")
        if not results:
            return "검색 결과가 없습니다."

        lines = []
        for i, r in enumerate(results):
            title = r.get('title', '제목 없음')
            content = r.get('content', '')
            url = r.get('url', '')
            raw_content = r.get('raw_content')
            img_list = r.get('images', [])
            img_info = f"\n- 이미지: {', '.join(img_list)}" if img_list else ""
            raw_info = f"\n- 원문: {raw_content[:200]}..." if include_raw_content and raw_content else ""
            lines.append(
                f"{i+1}. {title}\n- 요약: {content}\n- 링크: {url}{img_info}{raw_info}"
            )

        summary = f"\n\n[AI 요약]\n{answer}" if include_answer and answer else ""
        return "\n\n".join(lines) + summary
    except Exception as e:
        return f"Tavily Search Tool 오류: {e}"
