import base64
import gc
import os
import time
from pathlib import Path

import streamlit as st
import yaml
from crewai import Agent, Crew, LLM, Process, Task
from crewai_tools import FileReadTool
from dotenv import load_dotenv
from tqdm import tqdm

from brightdata_scrapper import get_output, get_progress, normalize_videos, trigger_scraping_channels

load_dotenv()

TRANSCRIPTS_DIR = Path("transcripts")
docs_tool = FileReadTool()
bright_data_api_key = os.getenv("BRIGHT_DATA_API_KEY")


@st.cache_resource
def load_llm():
    if os.getenv("OPENAI_API_KEY"):
        return LLM(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    return LLM(model="ollama/llama3.2", base_url="http://localhost:11434")


def create_agents_and_tasks():
    with open("config.yaml", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    analysis_agent = Agent(
        role=config["agents"][0]["role"],
        goal=config["agents"][0]["goal"],
        backstory=config["agents"][0]["backstory"],
        verbose=True,
        tools=[docs_tool],
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
        description=config["tasks"][0]["description"],
        expected_output=config["tasks"][0]["expected_output"],
        agent=analysis_agent,
    )

    response_task = Task(
        description=config["tasks"][1]["description"],
        expected_output=config["tasks"][1]["expected_output"],
        agent=response_synthesizer_agent,
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


def start_analysis():
    if not bright_data_api_key:
        st.error("Set BRIGHT_DATA_API_KEY in your .env file.")
        return

    channels = [url.strip() for url in st.session_state.youtube_channels if url.strip()]
    if not channels:
        st.error("Add at least one YouTube channel URL.")
        return

    status_container = st.empty()

    with st.spinner("Scraping videos... This may take a moment."):
        status_container.info("Extracting videos from the channels...")
        snapshot = trigger_scraping_channels(
            bright_data_api_key,
            channels,
            10,
            st.session_state.start_date,
            st.session_state.end_date,
            "Latest",
            "",
        )
        if not snapshot or "snapshot_id" not in snapshot:
            status_container.error("Failed to start Bright Data scraping job.")
            return

        snapshot_id = snapshot["snapshot_id"]
        while True:
            status = get_progress(bright_data_api_key, snapshot_id)
            if not status:
                status_container.error("Failed to check scraping progress.")
                return
            status_container.info(f"Current status: {status.get('status', 'unknown')}")
            if status.get("status") == "ready":
                break
            if status.get("status") == "failed":
                status_container.error(f"Scraping failed: {status}")
                return
            time.sleep(10)

        status_container.success("Scraping completed successfully!")
        scraped = get_output(bright_data_api_key, snapshot_id, format="json")
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

    with st.spinner("The agent is analyzing the videos... This may take a moment."):
        st.session_state.crew = create_agents_and_tasks()
        st.session_state.response = st.session_state.crew.kickoff(
            inputs={"file_paths": ", ".join(st.session_state.all_files)}
        )


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
    st.button("Start Analysis 🚀", type="primary", on_click=start_analysis)
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
