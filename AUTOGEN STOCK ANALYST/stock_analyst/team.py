"""Multi-agent coding + stock analysis team (Groq-powered AG2)."""

from __future__ import annotations

from pathlib import Path

from autogen import AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent
from autogen.coding import LocalCommandLineCodeExecutor

from stock_analyst.config import get_llm_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODING_DIR = PROJECT_ROOT / "coding"

PLANNER_SYSTEM = """You are a financial analysis planner.
Given a stock analysis request, break it into clear steps:
1) What data to fetch (ticker, period, metrics)
2) What code the engineer should write (charts, returns, moving averages, etc.)
3) What the final report should cover

Do NOT write code yourself. Hand off to the engineer after outlining the plan.
Keep plans practical and limited to yfinance + pandas + matplotlib.
"""

ENGINEER_SYSTEM = """You are a Python engineer for financial analysis.

Write complete, runnable Python scripts in a single ```python code block.

Rules:
- Use only: yfinance, pandas, matplotlib, numpy, pathlib, datetime
- Set matplotlib backend to Agg (non-interactive):
  import matplotlib
  matplotlib.use("Agg")
- Save charts under figures/ and CSVs under data/ (relative to the working directory)
- Print key numbers with print() so the executor can capture them
- Never use plt.show(), input(), or interactive plots
- Prefer one self-contained script per turn
- If execution fails, fix the full script and send it again

After successful execution with useful output, tell the writer to draft the report.
"""

WRITER_SYSTEM = """You are a financial report writer.
Using the planner's goals and the executor's code output (numbers + chart paths),
write a clear Markdown report with:
- Executive summary
- Price / performance highlights
- Technical observations (if computed)
- Risks / caveats (data delays, not investment advice)
- Paths to any generated charts

End your final report with the word TERMINATE.
"""


def build_team(max_rounds: int = 12) -> tuple[UserProxyAgent, GroupChatManager]:
    """Create the stock analysis agent team."""
    CODING_DIR.mkdir(exist_ok=True)
    (CODING_DIR / "data").mkdir(exist_ok=True)
    (CODING_DIR / "figures").mkdir(exist_ok=True)

    llm_config = get_llm_config()
    executor = LocalCommandLineCodeExecutor(timeout=90, work_dir=str(CODING_DIR))

    user = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        code_execution_config=False,
        description="Human that submits the stock analysis request.",
    )

    planner = AssistantAgent(
        name="planner",
        system_message=PLANNER_SYSTEM,
        llm_config=llm_config,
        description="Plans the stock analysis steps.",
    )

    engineer = AssistantAgent(
        name="engineer",
        system_message=ENGINEER_SYSTEM,
        llm_config=llm_config,
        description="Writes Python code for stock data and charts.",
    )

    executor_agent = UserProxyAgent(
        name="executor",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=8,
        code_execution_config={"executor": executor},
        default_auto_reply="Continue. If the analysis is complete, ask the writer for the report.",
        description="Executes Python code from the engineer.",
    )

    writer = AssistantAgent(
        name="writer",
        system_message=WRITER_SYSTEM,
        llm_config=llm_config,
        description="Writes the final Markdown stock report.",
    )

    def _speaker_selection(last_speaker, groupchat: GroupChat):
        """Simple handoff: planner -> engineer -> executor -> engineer/writer."""
        messages = groupchat.messages
        if not messages:
            return planner

        if last_speaker is user:
            return planner
        if last_speaker is planner:
            return engineer
        if last_speaker is engineer:
            return executor_agent
        if last_speaker is executor_agent:
            content = (messages[-1].get("content") or "").lower()
            # Retry on failure; otherwise move to writer after enough signal
            if "exitcode: 0" in content or "execution succeeded" in content:
                # If we already have a successful run, prefer writer after 1 success cycle
                success_count = sum(
                    1
                    for m in messages
                    if "exitcode: 0" in (m.get("content") or "").lower()
                    or "execution succeeded" in (m.get("content") or "").lower()
                )
                if success_count >= 1:
                    return writer
            return engineer
        if last_speaker is writer:
            return None
        return engineer

    groupchat = GroupChat(
        agents=[user, planner, engineer, executor_agent, writer],
        messages=[],
        max_round=max_rounds,
        speaker_selection_method=_speaker_selection,
        send_introductions=False,
    )

    manager = GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config,
        is_termination_msg=lambda msg: "TERMINATE" in (msg.get("content") or ""),
    )

    return user, manager


def run_analysis(task: str, max_rounds: int = 12) -> str:
    """Run a full multi-agent stock analysis and return chat summary text."""
    user, manager = build_team(max_rounds=max_rounds)
    result = user.initiate_chat(manager, message=task, summary_method="last_msg")
    summary = result.summary
    if isinstance(summary, dict):
        return summary.get("content") or str(summary)
    return summary or ""
