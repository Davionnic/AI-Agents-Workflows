from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from book_writer_flow.flow import BookFlow


def main() -> None:
    st.set_page_config(page_title="Book Writer Flow", page_icon="📚", layout="wide")
    st.title("Book Writer Flow")
    st.caption("Research a topic, shape an outline, and write every chapter with a CrewAI flow.")

    with st.sidebar:
        st.header("Book settings")
        topic = st.text_input("Topic", value="Astronomy in 2025")
        chapters = st.slider("Maximum chapters", min_value=1, max_value=12, value=5)
        st.divider()
        st.caption("Set OPENAI_API_KEY or run Ollama locally. Bright Data credentials enable live research.")

    if "book_path" not in st.session_state:
        st.session_state.book_path = None
    if st.button("Write book", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Enter a topic first.")
        else:
            with st.status("Writing your book...", expanded=True) as status:
                flow = BookFlow(topic=topic.strip(), max_chapters=chapters)
                path = flow.run()
                st.session_state.book_path = path
                status.update(label="Book ready", state="complete")

    if st.session_state.book_path:
        path = Path(st.session_state.book_path)
        st.success(f"Saved to {path.relative_to(ROOT)}")
        content = path.read_text(encoding="utf-8")
        st.download_button("Download Markdown", content, file_name=path.name, mime="text/markdown")
        st.markdown(content)


if __name__ == "__main__":
    main()