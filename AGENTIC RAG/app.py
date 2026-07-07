import base64
import gc
import os
import sys
import time
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

load_dotenv(ROOT / ".env")

from agentic_rag.crew_factory import create_agents_and_tasks
from agentic_rag.tools.document_search import DocumentSearchTool

UPLOAD_DIR = ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

LLM_OPTIONS = {
    "OpenAI (cloud)": {"provider": "openai", "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")},
    "Ollama — Llama 3.2": {"provider": "ollama", "model": "llama3.2"},
    "Ollama — DeepSeek R1": {"provider": "ollama", "model": "deepseek-r1:7b"},
}

WEB_SEARCH_OPTIONS = {
    "Firecrawl": "firecrawl",
    "Serper (Google)": "serper",
}


def init_session_state() -> None:
    defaults = {
        "messages": [],
        "document_tool": None,
        "crew": None,
        "crew_config_key": None,
        "uploaded_file_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_chat() -> None:
    st.session_state.messages = []
    gc.collect()


def reset_document() -> None:
    st.session_state.document_tool = None
    st.session_state.crew = None
    st.session_state.crew_config_key = None
    st.session_state.uploaded_file_id = None
    st.session_state.messages = []
    gc.collect()


def display_document_preview(file_bytes: bytes, file_name: str) -> None:
    st.markdown(f"### Preview: {file_name}")
    if file_name.lower().endswith(".pdf"):
        base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
        pdf_display = (
            f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
            f'width="100%" height="500" type="application/pdf"></iframe>'
        )
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.text(file_bytes.decode("utf-8", errors="replace")[:4000])


def save_upload(uploaded_file) -> Path:
    file_id = uuid.uuid4().hex[:8]
    dest = UPLOAD_DIR / f"{file_id}_{uploaded_file.name}"
    dest.write_bytes(uploaded_file.getvalue())
    return dest


def build_crew_config_key(llm_label: str, web_label: str, has_document: bool) -> str:
    return f"{llm_label}|{web_label}|{has_document}"


def stream_response(text: str, placeholder) -> None:
    full_response = ""
    lines = text.split("\n")
    for index, line in enumerate(lines):
        full_response += line
        if index < len(lines) - 1:
            full_response += "\n"
        placeholder.markdown(full_response + "▌")
        time.sleep(0.08)
    placeholder.markdown(full_response)


def main() -> None:
    init_session_state()

    st.set_page_config(
        page_title="Agentic RAG",
        page_icon="🔍",
        layout="wide",
    )

    with st.sidebar:
        st.header("Settings")

        llm_label = st.selectbox("LLM Provider", list(LLM_OPTIONS.keys()), index=0)
        web_label = st.selectbox("Web Search", list(WEB_SEARCH_OPTIONS.keys()), index=0)

        llm_cfg = LLM_OPTIONS[llm_label]
        web_provider = WEB_SEARCH_OPTIONS[web_label]

        st.divider()
        st.header("Document")
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=["pdf", "md", "txt"],
            help="Optional. Without a document, the agent uses web search only.",
        )

        if uploaded_file is not None:
            file_key = f"{uploaded_file.name}:{uploaded_file.size}"
            if st.session_state.uploaded_file_id != file_key:
                with st.spinner("Indexing document..."):
                    saved_path = save_upload(uploaded_file)
                    st.session_state.document_tool = DocumentSearchTool(file_path=str(saved_path))
                    st.session_state.uploaded_file_id = file_key
                    st.session_state.crew = None
                    st.session_state.crew_config_key = None
                st.success("Document indexed.")

            display_document_preview(uploaded_file.getvalue(), uploaded_file.name)
        else:
            if st.session_state.document_tool is not None:
                reset_document()

        col1, col2 = st.columns(2)
        with col1:
            st.button("Clear Chat", on_click=reset_chat, use_container_width=True)
        with col2:
            st.button("Reset All", on_click=reset_document, use_container_width=True)

        st.divider()
        st.caption("Requires API keys in `.env` — see `.env.example`.")

    st.title("Agentic RAG")
    st.caption(
        "CrewAI agents search your documents first, then fall back to web search when needed."
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask a question...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        config_key = build_crew_config_key(
            llm_label,
            web_label,
            st.session_state.document_tool is not None,
        )

        if (
            st.session_state.crew is None
            or st.session_state.crew_config_key != config_key
        ):
            st.session_state.crew = create_agents_and_tasks(
                document_tool=st.session_state.document_tool,
                llm_provider=llm_cfg["provider"],
                llm_model=llm_cfg["model"],
                web_search_provider=web_provider,
            )
            st.session_state.crew_config_key = config_key

        with st.chat_message("assistant"):
            placeholder = st.empty()
            with st.spinner("Agents working..."):
                result = st.session_state.crew.kickoff(inputs={"query": prompt}).raw

            stream_response(result, placeholder)

        st.session_state.messages.append({"role": "assistant", "content": result})


if __name__ == "__main__":
    main()
