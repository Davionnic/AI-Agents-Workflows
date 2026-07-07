from typing import Optional

from crewai import Agent, Crew, Process, Task

from agentic_rag.llm_factory import create_llm
from agentic_rag.tools.web_search import create_web_search_tool


RETRIEVER_ROLE = "Retrieve relevant information to answer the user query: {query}"
RETRIEVER_GOAL = (
    "Retrieve the most relevant information from the available sources "
    "for the user query: {query}. Always try the document search tool first. "
    "If document search does not return useful information, use web search."
)
RETRIEVER_BACKSTORY = (
    "You are a meticulous analyst who understands user queries and picks "
    "the best knowledge source for each question."
)

SYNTHESIZER_ROLE = "Response synthesizer for the user query: {query}"
SYNTHESIZER_GOAL = (
    "Synthesize retrieved information into a concise, accurate response "
    "for the user query: {query}. If nothing useful was found, respond with: "
    "\"I'm sorry, I couldn't find the information you're looking for.\""
)
SYNTHESIZER_BACKSTORY = (
    "You are a skilled communicator who turns complex information into "
    "clear, well-structured answers."
)


def create_agents_and_tasks(
    document_tool=None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    web_search_provider: Optional[str] = None,
) -> Crew:
    llm = create_llm(provider=llm_provider, model=llm_model)
    web_search_tool = create_web_search_tool(provider=web_search_provider)

    tools = [t for t in [document_tool, web_search_tool] if t is not None]
    agent_kwargs = {"verbose": True, "tools": tools}
    synthesizer_kwargs = {"verbose": True}

    if llm is not None:
        agent_kwargs["llm"] = llm
        synthesizer_kwargs["llm"] = llm

    retriever_agent = Agent(
        role=RETRIEVER_ROLE,
        goal=RETRIEVER_GOAL,
        backstory=RETRIEVER_BACKSTORY,
        **agent_kwargs,
    )

    response_synthesizer_agent = Agent(
        role=SYNTHESIZER_ROLE,
        goal=SYNTHESIZER_GOAL,
        backstory=SYNTHESIZER_BACKSTORY,
        **synthesizer_kwargs,
    )

    retrieval_task = Task(
        description=(
            "Retrieve the most relevant information from available sources "
            "for the user query: {query}"
        ),
        expected_output=(
            "The most relevant information as text retrieved from the sources."
        ),
        agent=retriever_agent,
    )

    response_task = Task(
        description="Synthesize the final response for the user query: {query}",
        expected_output=(
            "A concise and coherent response based on retrieved information. "
            "If nothing was found, say you could not find the information."
        ),
        agent=response_synthesizer_agent,
    )

    return Crew(
        agents=[retriever_agent, response_synthesizer_agent],
        tasks=[retrieval_task, response_task],
        process=Process.sequential,
        verbose=True,
    )
