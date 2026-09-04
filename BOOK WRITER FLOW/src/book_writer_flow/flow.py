import asyncio
import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

from book_writer_flow.llm_factory import create_llm
from book_writer_flow.models import BookState, Chapter, Outline
from book_writer_flow.tools import BrightDataWebSearchTool


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "outputs"


def _outline_crew() -> Crew:
    llm = create_llm()
    researcher = Agent(
        role="Book Research Agent",
        goal="Research {topic} and gather accurate, current insights for a book outline.",
        backstory="You are a meticulous researcher who finds the most relevant facts and themes.",
        tools=[BrightDataWebSearchTool()],
        llm=llm,
        verbose=True,
    )
    writer = Agent(
        role="Book Outline Writer",
        goal="Create a compelling, logically ordered outline about {topic}.",
        backstory="You are an experienced author who turns research into readable structures.",
        llm=llm,
        verbose=True,
    )
    research = Task(
        description="Research {topic}. Return useful facts, themes, and sources for an outline.",
        expected_output="A concise research brief with factual insights and source names.",
        agent=researcher,
    )
    outline = Task(
        description="Create a book outline for {topic} with 3 to 12 distinct chapter titles.",
        expected_output="A structured outline containing total_chapters and titles.",
        agent=writer,
        context=[research],
        output_pydantic=Outline,
    )
    return Crew(agents=[researcher, writer], tasks=[research, outline], process=Process.sequential, verbose=True)


def _chapter_crew() -> Crew:
    llm = create_llm()
    researcher = Agent(
        role="Topic Researcher",
        goal="Research the chapter topic {title} within the larger book topic {topic}.",
        backstory="You find specific, useful details and distinguish facts from speculation.",
        tools=[BrightDataWebSearchTool()],
        llm=llm,
        verbose=True,
    )
    writer = Agent(
        role="Senior Writer",
        goal="Write an engaging and informative chapter about {title}.",
        backstory="You write clear, well-structured chapters that resonate with readers.",
        llm=llm,
        verbose=True,
    )
    research = Task(
        description="Research {title} as part of a book about {topic}. Gather facts and examples.",
        expected_output="A focused research brief for the chapter.",
        agent=researcher,
    )
    chapter = Task(
        description="Write the chapter {title} for the book about {topic}. Other chapter titles: {chapters}.",
        expected_output="A polished chapter with a clear title and substantial Markdown content.",
        agent=writer,
        context=[research],
        output_pydantic=Chapter,
    )
    return Crew(agents=[researcher, writer], tasks=[research, chapter], process=Process.sequential, verbose=True)


class BookFlow:
    def __init__(self, topic: str = "Astronomy in 2025", max_chapters: int = 5, output_dir: Path | None = None):
        self.state = BookState(topic=topic, max_chapters=max_chapters)
        self.output_dir = output_dir or OUTPUT_DIR

    def run(self, demo: bool = False) -> str:
        load_dotenv(ROOT / ".env")
        if demo:
            self.state.outline = Outline(total_chapters=2, titles=[f"Foundations of {self.state.topic}", f"The Future of {self.state.topic}"])
            self.state.chapters = [Chapter(title=title, content=f"This is a demonstration chapter about {title.lower()}.") for title in self.state.outline.titles]
        else:
            self.state.outline = self._generate_outline()
            self.state.chapters = asyncio.run(self._generate_chapters(self.state.outline.titles[: self.state.max_chapters]))
        return self._save_book()

    def _generate_outline(self) -> Outline:
        result = _outline_crew().kickoff(inputs={"topic": self.state.topic})
        if result.pydantic:
            outline = result.pydantic
        else:
            raise RuntimeError("The outline agent did not return structured output.")
        outline.total_chapters = min(outline.total_chapters, self.state.max_chapters)
        outline.titles = outline.titles[: outline.total_chapters]
        return outline

    async def _generate_chapters(self, titles: list[str]) -> list[Chapter]:
        async def write(title: str) -> Chapter:
            result = await asyncio.to_thread(_chapter_crew().kickoff, inputs={"title": title, "topic": self.state.topic, "chapters": titles})
            if not result.pydantic:
                raise RuntimeError(f"Chapter agent did not return structured output for {title!r}.")
            return result.pydantic

        return await asyncio.gather(*(write(title) for title in titles))

    def _save_book(self) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        safe_topic = "".join(char.lower() if char.isalnum() else "-" for char in self.state.topic).strip("-")
        path = self.output_dir / f"{safe_topic or 'book'}.md"
        lines = [f"# {self.state.topic}\n"]
        for index, chapter in enumerate(self.state.chapters, start=1):
            lines.extend([f"## Chapter {index}: {chapter.title}\n", f"{chapter.content.strip()}\n"])
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)