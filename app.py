import streamlit as st
import importlib
import os
from llm import GeminiLLM

st.set_page_config(page_title="Jarvis 챗봇", page_icon="🤖", layout="wide")

# --- ChatGPT 다크 테마 스타일 CSS ---
st.markdown("""
<style>
body, .stApp {
    background: #1a1b1e !important;
    color: #e5e5e5 !important;
}
header, .st-emotion-cache-18ni7ap {
    background: #1a1b1e !important;
}
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1.1em;
    margin-bottom: 1.8em;
}
.chat-bubble-user {
    align-self: flex-end;
    background: linear-gradient(90deg, #4f8cff 0%, #204080 100%);
    color: #fff;
    padding: 1.05em 1.4em;
    border-radius: 1.2em 1.2em 0.4em 1.2em;
    max-width: 68%;
    font-size: 1.11em;
    box-shadow: 0 2px 12px rgba(79,140,255,0.08);
    margin-right: 0.3em;
    margin-left: auto;
    word-break: break-word;
    border: 1px solid #4466aa33;
}
.chat-bubble-bot {
    align-self: flex-start;
    background: #23272f;
    color: #e5e5e5;
    padding: 1.05em 1.4em;
    border-radius: 1.2em 1.2em 1.2em 0.4em;
    max-width: 68%;
    font-size: 1.11em;
    box-shadow: 0 2px 12px rgba(0,0,0,0.13);
    margin-left: 0.3em;
    margin-right: auto;
    word-break: break-word;
    border: 1px solid #333846;
}
.stTextInput > div > input {
    background: #23272f;
    color: #e5e5e5;
    border-radius: 1.2em;
    border: 1.7px solid #333846;
    padding: 1em 1.4em;
    font-size: 1.14em;
    box-shadow: none;
}
.stTextInput > div > input::placeholder {
    color: #757b8a;
    opacity: 1;
}
.stButton > button {
    border-radius: 1.2em;
    background: linear-gradient(90deg, #4f8cff 0%, #204080 100%);
    color: #fff;
    font-weight: 600;
    font-size: 1.13em;
    padding: 0.8em 1.8em;
    border: none;
    margin-top: 0.3em;
    margin-bottom: 0.2em;
    box-shadow: 0 2px 8px #20408044;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #204080 0%, #4f8cff 100%);
}
.st-emotion-cache-1c7y2kd {
    background: #23272f !important;
}
::-webkit-scrollbar {
    width: 10px;
    background: #23272f;
}
::-webkit-scrollbar-thumb {
    background: #333846;
    border-radius: 6px;
}
.stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {
    color: #e5e5e5 !important;
}
.stAlert {
    background: #23272f !important;
    color: #e5e5e5 !important;
}
</style>
""", unsafe_allow_html=True)

def load_tools():
    tools = {}
    tools_dir = "tools"
    if not os.path.isdir(tools_dir):
        return tools
    for fname in os.listdir(tools_dir):
        if fname.endswith(".py") and not fname.startswith("__"):
            modname = fname[:-3]
            module = importlib.import_module(f"tools.{modname}")
            tools[modname] = module
    return tools

if "history" not in st.session_state:
    st.session_state["history"] = []

if "llm" not in st.session_state:
    st.session_state["llm"] = GeminiLLM()

if "tools" not in st.session_state:
    st.session_state["tools"] = load_tools()

if "notification" not in st.session_state:
    st.session_state["notification"] = "app.py에서 대기 중"

st.info(f"알림: {st.session_state['notification']}")

st.markdown(
    "<h1 style='color:#4f8cff; font-size:2.2em; margin-bottom:0.1em;'>🤖 Jarvis</h1>"
    "<div style='color:#a5b8d8; margin-bottom:1.3em; font-size:1.1em;'>자연어로 질문하면 LLM이 여러 도구를 조합해 답변합니다.</div>",
    unsafe_allow_html=True
)

chat_placeholder = st.container()
with chat_placeholder:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for role, content in st.session_state["history"]:
        if role == "user":
            st.markdown(f'<div class="chat-bubble-user">{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-bot">{content}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        label="메시지 입력",
        label_visibility='collapsed',
        key="user_input",
        autocomplete="on",
        placeholder="메시지를 입력하세요 (예: 2024년 월별 삼성전자 주가와 최신 뉴스, AI 트렌드 등)",
    )
    submitted = st.form_submit_button("보내기", use_container_width=True)

if submitted and user_input.strip():
    st.session_state["history"].append(("user", user_input))
    st.session_state["notification"] = "app.py: LLM이 도구 판단 중..."
    st.rerun()

if st.session_state["history"] and st.session_state["history"][-1][0] == "user":
    llm = st.session_state["llm"]
    user_input = st.session_state["history"][-1][1]
    tool_intents = llm.decide_tools(user_input)
    st.write("LLM 반환 tool_intents:", tool_intents)
    tool_results = []
    for intent in tool_intents:
        tool_name = intent.get("tool")
        if tool_name and tool_name in st.session_state["tools"] and tool_name != "none":
            st.session_state["notification"] = f"app.py: {tool_name}.py 실행 중"
            tool_module = st.session_state["tools"][tool_name]
            if tool_name == "stock":
                param = intent.get("ticker")
                chart_flag = intent.get("chart", True)
                tool_result = tool_module.run(
                    query=user_input,
                    ticker=param,
                    start=intent.get("start"),
                    end=intent.get("end"),
                    interval=intent.get("interval"),
                    ma_window=intent.get("ma_window", 5),
                    rsi_window=intent.get("rsi_window", 14),
                    summary=intent.get("summary", True),
                    chart=chart_flag
                )
                if "[차트 이미지(base64)]:" in tool_result:
                    text, img_line = tool_result.split("[차트 이미지(base64)]:", 1)
                    st.markdown(text)
                    chart_img = img_line.strip()
                    st.image("data:image/png;base64," + chart_img)
                    tool_result = text
            elif tool_name == "news":
                param = intent.get("keyword")
                tool_result = tool_module.run(query=param)
            elif tool_name == "tavily":
                param = intent.get("query")
                tool_result = tool_module.run(query=param)
            elif tool_name == "serp":
                param = intent.get("query")
                search_type = intent.get("search_type", "web")
                tool_result = tool_module.run(
                    query=param,
                    search_type=search_type
                )
            elif tool_name == "mongo":
                action = intent.get("action")
                db_name = intent.get("db_name")
                coll_name = intent.get("coll_name")
                query_param = intent.get("query")
                data_param = intent.get("data")
                update_param = intent.get("update")
                many_param = intent.get("many", False)
                object_id_param = intent.get("object_id")
                projection_param = intent.get("projection")
                tool_result = tool_module.run(
                    action=action,
                    db_name=db_name,
                    coll_name=coll_name,
                    query=query_param,
                    data=data_param,
                    update=update_param,
                    many=many_param,
                    object_id=object_id_param,
                    projection=projection_param
                )
            else:
                param = None
                tool_result = "지원하지 않는 도구입니다."
            tool_results.append({"tool": tool_name, "param": param if tool_name != "mongo" else intent, "result": tool_result})
            st.session_state["notification"] = f"{tool_name}.py 실행 완료, app.py로 복귀"
    if tool_results:
        tools_used = ', '.join(set([tr['tool'] for tr in tool_results]))
        summary = llm.answer_with_tools(user_input, tool_results)
        display_text = f"[사용된 도구: {tools_used}]\n\n{summary}"
        st.session_state["history"].append(("model", display_text))
    else:
        st.session_state["notification"] = "app.py: LLM 직접 답변"
        response = llm.answer_direct(user_input, history=st.session_state["history"])
        st.session_state["history"].append(("model", response))
        st.session_state["notification"] = "app.py에서 대기 중"
    st.rerun()
