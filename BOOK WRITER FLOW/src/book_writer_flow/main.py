import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from book_writer_flow.flow import BookFlow


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a researched book with CrewAI.")
    parser.add_argument("topic", nargs="?", default="Astronomy in 2025")
    parser.add_argument("--chapters", type=int, default=5)
    parser.add_argument("--demo", action="store_true", help="Generate a local sample without an LLM or web search.")
    args = parser.parse_args()
    path = BookFlow(topic=args.topic, max_chapters=args.chapters).run(demo=args.demo)
    print(f"Book saved to {Path(path).resolve()}")


if __name__ == "__main__":
    main()