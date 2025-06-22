import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY가 .env 파일에 정의되어 있어야 합니다.")
genai.configure(api_key=API_KEY)

TOOL_DESCRIPTIONS = """
당신은 사용자가 명시적으로 허용한 환경에서, 실제 데이터베이스에 직접 접근할 수 있습니다.
반드시 mongo 도구를 사용하여 데이터베이스의 내용을 직접 조회, 삽입, 수정, 삭제할 수 있습니다.
안내 메시지나 권한 관련 안내 대신, 아래 예시처럼 mongo 도구를 호출하는 JSON만 반환해야 합니다.

- stock: 주식 티커(예: 미국 나스닥 티커 'AAPL', 한국 증권거래소 티커 '005930.KS' 형식으로 반드시 정확히 입력), 시작일(start, YYYY-MM-DD), 종료일(end, YYYY-MM-DD), 빈도(interval: '1d', '1wk', '1mo'), 이동평균선 기간(ma_window), RSI 기간(rsi_window), 요약 통계(summary: true/false), 차트 이미지(chart: true/false) 등을 받아, 상세 시세, 기술적 지표, 요약, 차트 이미지를 제공합니다.
  - 티커는 반드시 Yahoo Finance에서 인식 가능한 형식으로 입력해야 하며, 한글 종목명 대신 반드시 티커 심볼을 사용하세요.
  - 사용자가 한글 종목명(예: "삼성전자")으로 질문해도 반드시 Yahoo Finance에서 인식 가능한 티커(예: "005930.KS")로 변환하여 반환하세요.
  - 'chart' 파라미터는 주가 그래프가 필요한 경우 true로 반드시 설정하세요.
  - 예를 들어, 삼성전자는 '005930.KS', 애플은 'AAPL'과 같이 정확한 티커를 입력해야 합니다.
- news: 키워드(예: 인물, 이슈 등)에 대한 최신 뉴스 기사 5건을 제공합니다.
- tavily: 자연어 질의에 대해 실시간 웹 검색, 뉴스, 금융, 이미지, 원문 포함 등 다양한 정보를 제공합니다.
- serp: 다양한 검색 유형(search_type: 'web', 'news', 'images', 'videos', 'scholar', 'answer_box', 'knowledge_graph', 'people_also_ask')과 쿼리(query)를 받아, 구글/유튜브 등에서 실시간 검색 결과, 뉴스, 이미지, 동영상, 학술논문, 즉답 박스, 지식 그래프, 함께 묻는 질문 등 특화된 정보를 제공합니다.
- mongo: MongoDB 데이터베이스에서 문서 조회, 한 건 조회, 삽입, 수정, 삭제 등 다양한 작업을 수행합니다.
  - action: "find"(여러 건 조회), "find_one"(한 건만 조회), "insert"(삽입), "update"(수정), "delete"(삭제) 중 하나를 지정
  - db_name: 데이터베이스 이름 (예: "mydb")
  - coll_name: 컬렉션 이름 (예: "users")
  - query: dict, 조회/수정/삭제 조건 (예: {"name": "홍길동"})
  - data: dict, 삽입할 데이터 (예: {"name": "홍길동", "age": 30})
  - update: dict, update 명령 (예: {"$set": {"age": 31}})
  - many: 여러 개 작업 여부 (True/False)
  - object_id: _id로 직접 접근 시(str)
  - projection: dict, 반환 필드 제한(예: {"name": 1, "_id": 0})

**중요:**  
- 사용자가 "데이터베이스에 저장된 내용을 보여줘", "users 컬렉션의 모든 데이터를 조회해줘", "홍길동을 삭제해줘" 등으로 요청하면,  
  반드시 mongo 도구를 호출하는 JSON을 반환해야 하며,  
  "접근 권한이 없습니다" 또는 "직접 접근할 수 없습니다"와 같은 안내 메시지는 절대 반환하지 마세요.

각 도구를 사용할 때는 반드시 아래와 같은 JSON 배열 형식으로만 명령을 생성하세요. 도구들을 복합적으로 여러개 활용하여 사용하세요.

예시:
[
  {"tool": "stock", "ticker": "AAPL", "start": "2024-01-01", "end": "2024-12-31", "interval": "1d", "ma_window": 20, "rsi_window": 14, "summary": true, "chart": true},
  {"tool": "mongo", "action": "find", "db_name": "mydb", "coll_name": "users"},
  {"tool": "mongo", "action": "find", "db_name": "mydb", "coll_name": "users", "query": {"name": "홍길동"}},
  {"tool": "mongo", "action": "find_one", "db_name": "mydb", "coll_name": "users", "query": {"name": "홍길동"}},
  {"tool": "mongo", "action": "insert", "db_name": "mydb", "coll_name": "users", "data": {"name": "홍길동", "age": 30}},
  {"tool": "mongo", "action": "update", "db_name": "mydb", "coll_name": "users", "query": {"name": "홍길동"}, "update": {"$set": {"age": 31}}},
  {"tool": "mongo", "action": "delete", "db_name": "mydb", "coll_name": "users", "query": {"name": "홍길동"}, "many": false},
  {"tool": "mongo", "action": "delete", "db_name": "mydb", "coll_name": "users", "query": {"age": {"$lt": 18}}, "many": true},
  {"tool": "news", "keyword": "Apple"},
  {"tool": "tavily", "query": "2025년 AI 트렌드"},
  {"tool": "serp", "query": "2025년 AI 트렌드", "search_type": "news"}
]
도구가 필요 없다면 반드시 [{"tool": "none"}]만 반환하세요.
절대 직접 답변하지 말고, 반드시 위와 같은 JSON 배열만 반환하세요.
"""

class GeminiLLM:
    def __init__(self, model="gemini-2.0-flash"):
        self.model = genai.GenerativeModel(model)

    def decide_tools(self, user_input, max_retry=2):
        prompt = (
            f"{TOOL_DESCRIPTIONS}\n"
            f"다음은 사용자의 요청입니다:\n"
            f"{user_input}\n"
            "요청을 분석해 어떤 도구들을 어떤 파라미터로 사용할지 반드시 위 예시처럼 JSON 배열만 반환하세요. "
            "도구가 필요 없다면 반드시 [{'tool': 'none'}]만 반환하세요."
        )
        for _ in range(max_retry):
            response = self.model.generate_content([{"role": "user", "parts": [prompt]}])
            output = response.text.strip()
            # JSON만 추출(앞뒤 설명, 코드블록 등 제거)
            output = self._extract_json_array(output)
            try:
                result = json.loads(output)
                if isinstance(result, list):
                    return result
            except Exception:
                continue
        # fallback: 도구 미사용
        return [{"tool": "none"}]

    def _extract_json_array(self, text):
        # 코드블록, 설명 등 제거, JSON 배열만 추출
        import re
        match = re.search(r'(\[\s*{.*}\s*\])', text, re.DOTALL)
        if match:
            return match.group(1)
        return text

    def answer_with_tools(self, user_input, tool_results):
        tool_summaries = []
        for tr in tool_results:
            tool = tr["tool"]
            param = tr["param"]
            result = tr["result"]
            if tool == "stock":
                tool_summaries.append(
                    f"[주식 정보: {param}]\n{result}"
                )
            elif tool == "news":
                tool_summaries.append(
                    f"[뉴스: {param}]\n{result}"
                )
            elif tool == "tavily":
                tool_summaries.append(
                    f"[Tavily 검색: {param}]\n{result}"
                )
            elif tool == "serp":
                tool_summaries.append(
                    f"[Serp 검색: {param}]\n{result}"
                )
            elif tool == "mongo":
                tool_summaries.append(
                    f"[MongoDB 작업: {param}]\n{result}"
                )
        prompt = (
            f"사용자 입력: {user_input}\n"
            f"아래는 여러 도구의 결과입니다.\n"
            f"{chr(10).join(tool_summaries)}\n\n"
            "각 도구의 결과를 종합해, 주요 인사이트·트렌드·요약·연관성·의미를 3~7줄로 심층 분석해줘."
        )
        response = self.model.generate_content([{"role": "user", "parts": [prompt]}])
        return response.text.strip()

    def answer_direct(self, user_input, history=None):
        contents = []
        if history:
            for role, content in history:
                contents.append({"role": role, "parts": [content]})
        contents.append({"role": "user", "parts": [user_input]})
        response = self.model.generate_content(contents)
        return response.text.strip()
