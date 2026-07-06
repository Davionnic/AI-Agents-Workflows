import base64
import gc
import os
from pathlib import Path

import importlib

import requests
import streamlit as st
import yaml
from crewai import Agent, Crew, LLM, Process, Task
from crewai_tools import FileReadTool
from dotenv import load_dotenv
from tqdm import tqdm

import brightdata_scrapper
importlib.reload(brightdata_scrapper)
from brightdata_scrapper import (
    BrightDataError,
    get_output,
    normalize_videos,
    trigger_scraping_channels,
    wait_for_snapshot,
)

load_dotenv()

TRANSCRIPTS_DIR = Path("transcripts")
docs_tool = FileReadTool()
bright_data_api_key = os.getenv("BRIGHT_DATA_API_KEY")
PLACEHOLDER_KEYS = {"your_openai_api_key", "your_bright_data_api_key", "changeme"}


def is_valid_api_key(value: str | None) -> bool:
    if not value or not value.strip():
        return False
    return value.strip().lower() not in PLACEHOLDER_KEYS and not value.strip().lower().startswith("your_")


def get_openai_api_key() -> str | None:
    key = os.getenv("OPENAI_API_KEY")
    return key if is_valid_api_key(key) else None


def get_llm_label() -> str:
    if get_openai_api_key():
        return "OpenAI gpt-4o"
    return "Ollama llama3.2 (local)"


@st.cache_resource
def load_llm():
    openai_key = get_openai_api_key()
    if openai_key:
        return LLM(model="gpt-4o", api_key=openai_key)
    return LLM(model="ollama/llama3.2", base_url="http://localhost:11434")


def load_transcripts(file_paths: list[str], max_chars: int = 20000) -> str:
    parts = []
    for path in file_paths:
        content = Path(path).read_text(encoding="utf-8")
        parts.append(f"--- {Path(path).name} ---\n{content}")
    combined = "\n\n".join(parts)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[Transcript truncated for context limit]"
    return combined


def create_agents_and_tasks(transcripts: str):
    with open("config.yaml", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    use_openai = get_openai_api_key() is not None
    analysis_description = (
        f"{config['tasks'][0]['description'].strip()}\n\n"
        f"--- TRANSCRIPTS ---\n\n{transcripts}"
    )

    analysis_agent = Agent(
        role=config["agents"][0]["role"],
        goal=config["agents"][0]["goal"],
        backstory=config["agents"][0]["backstory"],
        verbose=True,
        tools=[docs_tool] if use_openai else [],
        llm=load_llm(),
    )

    response_synthesizer_agent = Agent(
        role=config["agents"][1]["role"],
        goal=config["agents"][1]["goal"],
        backstory=config["agents"][1]["backstory"],
        verbose=True,
        llm=load_llm(),
    )

    analysis_task = Task(
        description=analysis_description,
        expected_output=config["tasks"][0]["expected_output"],
        agent=analysis_agent,
    )

    response_task = Task(
        description=config["tasks"][1]["description"],
        expected_output=config["tasks"][1]["expected_output"],
        agent=response_synthesizer_agent,
        context=[analysis_task],
    )

    return Crew(
        agents=[analysis_agent, response_synthesizer_agent],
        tasks=[analysis_task, response_task],
        process=Process.sequential,
        verbose=True,
    )


def save_transcripts(videos: list) -> list[str]:
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    files = []
    for video in videos:
        video_id = video.get("shortcode") or video.get("video_id") or "unknown"
        file_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
        files.append(str(file_path))
        with open(file_path, "w", encoding="utf-8") as handle:
            for segment in video.get("formatted_transcript") or []:
                text = segment.get("text", "")
                start_time = segment.get("start_time", 0)
                end_time = segment.get("end_time", 0)
                handle.write(f"({start_time:.2f}-{end_time:.2f}): {text}\n")
    return files


def run_crew_analysis(openai_key: str | None):
    transcript_files = sorted(str(p) for p in TRANSCRIPTS_DIR.glob("*.txt"))
    if not transcript_files:
        st.error("No transcript files found in the transcripts/ folder.")
        return

    st.session_state.all_files = transcript_files
    with st.spinner("The agent is analyzing the videos... This may take a moment."):
        try:
            max_chars = 100000 if openai_key else 20000
            transcripts = load_transcripts(transcript_files, max_chars=max_chars)
            st.session_state.crew = create_agents_and_tasks(transcripts)
            st.session_state.response = st.session_state.crew.kickoff()
            if "can't fulfill" in str(st.session_state.response.raw).lower():
                st.warning("The model returned a refusal. Try again or switch to OpenAI for better results.")
        except Exception as exc:
            error_name = type(exc).__name__
            if "Authentication" in error_name or "401" in str(exc):
                st.error(
                    "LLM authentication failed. Add a real `OPENAI_API_KEY` to `.env`, "
                    "or remove it and run `ollama pull llama3.2` for local analysis."
                )
            else:
                st.error(f"Analysis failed: {exc}")


def analyze_existing_transcripts():
    openai_key = get_openai_api_key()
    if not openai_key:
        st.info(f"Using **{get_llm_label()}**. Ensure Ollama is running, or set a real `OPENAI_API_KEY` in `.env`.")
    run_crew_analysis(openai_key)


def start_analysis():
    if not is_valid_api_key(bright_data_api_key):
        st.error("Set a valid BRIGHT_DATA_API_KEY in your .env file.")
        return

    openai_key = get_openai_api_key()
    if not openai_key:
        st.info(f"Using **{get_llm_label()}**. Ensure Ollama is running, or set a real `OPENAI_API_KEY` in `.env`.")

    channels = [url.strip() for url in st.session_state.youtube_channels if url.strip()]
    if not channels:
        st.error("Add at least one YouTube channel URL.")
        return

    status_container = st.empty()

    with st.spinner("Scraping videos... This may take a moment."):
        status_container.info("Extracting videos from the channels...")
        try:
            snapshot = trigger_scraping_channels(
                bright_data_api_key,
                channels,
                10,
                st.session_state.start_date,
                st.session_state.end_date,
                "Latest",
                "",
            )
        except BrightDataError as exc:
            if exc.status_code in {502, 503, 504}:
                status_container.error(
                    "Bright Data returned a temporary server error (502/503). "
                    "Wait a minute and try again, or use **Analyze Saved Transcripts** to skip scraping."
                )
            else:
                status_container.error(str(exc))
            return
        except requests.RequestException:
            status_container.error("Could not reach Bright Data. Check your connection and try again.")
            return
        if not snapshot or "snapshot_id" not in snapshot:
            status_container.error("Failed to start Bright Data scraping job. Try again in a minute.")
            return

        snapshot_id = snapshot["snapshot_id"]
        status_container.info("Waiting for Bright Data to finish scraping (may take several minutes)...")
        try:
            status = wait_for_snapshot(bright_data_api_key, snapshot_id)
        except TimeoutError:
            status_container.error("Scraping timed out. Try a shorter date range or fewer channels.")
            return
        except (requests.RequestException, BrightDataError):
            status_container.error("Lost connection to Bright Data while waiting. Please try again.")
            return
        if status.get("status") == "failed":
            status_container.error(f"Scraping failed: {status}")
            return

        status_container.success("Scraping completed successfully!")
        status_container.info("Downloading scraped results (this can take a few minutes)...")
        try:
            scraped = get_output(bright_data_api_key, snapshot_id, format="json")
        except (requests.RequestException, BrightDataError):
            status_container.error(
                "Bright Data timed out while downloading results. "
                "Try again with a shorter date range or fewer channels."
            )
            return
        if not scraped:
            status_container.error("No videos returned from Bright Data.")
            return

        videos = normalize_videos(scraped)
        st.session_state.channel_scrapped_output = videos

        st.markdown("## YouTube Videos Extracted")
        videos_per_row = 3
        num_rows = (len(videos) + videos_per_row - 1) // videos_per_row
        for row in range(num_rows):
            cols = st.columns(videos_per_row)
            for col_idx in range(videos_per_row):
                video_idx = row * videos_per_row + col_idx
                if video_idx < len(videos):
                    with cols[col_idx]:
                        st.video(videos[video_idx].get("url"))

        status_container.info("Processing transcripts...")
        st.session_state.all_files = save_transcripts(videos)
        status_container.success("Scraping complete! Analyzing videos and reporting trends...")

    run_crew_analysis(openai_key)


def reset_chat():
    st.session_state.messages = []
    st.session_state.response = None
    gc.collect()


crewai_logo = base64.b64encode(Path("assets/crewai.png").read_bytes()).decode()
brightdata_logo = base64.b64encode(Path("assets/brightdata.png").read_bytes()).decode()

st.markdown(
    f"""
    # YouTube Trend Analysis powered by
    <img src="data:image/png;base64,{crewai_logo}" width="120" />
    &nbsp;
    <img src="data:image/png;base64,{brightdata_logo}" width="120" />
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "response" not in st.session_state:
    st.session_state.response = None
if "crew" not in st.session_state:
    st.session_state.crew = None
if "youtube_channels" not in st.session_state:
    st.session_state.youtube_channels = [""]

with st.sidebar:
    st.header("YouTube Channels")

    def add_channel_field():
        st.session_state.youtube_channels.append("")

    for i, channel in enumerate(st.session_state.youtube_channels):
        col1, col2 = st.columns([6, 1])
        with col1:
            st.session_state.youtube_channels[i] = st.text_input(
                "Channel URL",
                value=channel,
                key=f"channel_{i}",
                label_visibility="collapsed",
            )
        with col2:
            if i > 0 and st.button("❌", key=f"remove_{i}"):
                st.session_state.youtube_channels.pop(i)
                st.rerun()

    st.button("Add Channel ➕", on_click=add_channel_field)
    st.divider()

    st.subheader("Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
        st.session_state.start_date = start_date.strftime("%Y-%m-%d")
    with col2:
        end_date = st.date_input("End Date")
        st.session_state.end_date = end_date.strftime("%Y-%m-%d")

    st.divider()
    st.caption(f"LLM: {get_llm_label()}")
    st.button("Start Analysis 🚀", type="primary", on_click=start_analysis)
    st.button("Analyze Saved Transcripts 📄", on_click=analyze_existing_transcripts)
    st.button("Clear Results", on_click=reset_chat)

if st.session_state.response:
    with st.spinner("Generating content... This may take a moment."):
        try:
            result = st.session_state.response
            st.markdown("### Generated Analysis")
            st.markdown(result)
            st.download_button(
                label="Download Content",
                data=result.raw,
                file_name="youtube_trend_analysis.md",
                mime="text/markdown",
            )
        except Exception as exc:
            st.error(f"An error occurred: {exc}")

st.markdown("---")
st.markdown("Built with CrewAI, Bright Data and Streamlit")
