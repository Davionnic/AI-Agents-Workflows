from pydantic import BaseModel, Field


class Outline(BaseModel):
    total_chapters: int = Field(ge=1)
    titles: list[str] = Field(min_length=1)


class Chapter(BaseModel):
    title: str
    content: str


class BookState(BaseModel):
    topic: str
    max_chapters: int = 5
    outline: Outline | None = None
    chapters: list[Chapter] = Field(default_factory=list)