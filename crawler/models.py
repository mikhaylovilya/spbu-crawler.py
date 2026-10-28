from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class Link:
    url: str
    text: str
    internal: bool


@dataclass(slots=True)
class Page:
    url: str
    status_code: int
    title: str
    text: str
    links: list[Link] = field(default_factory=list)
    depth: int = 0
    fetched_at: str = ""


@dataclass(slots=True)
class Failure:
    url: str
    error: str
    status_code: int | None = None


@dataclass(slots=True)
class CrawlResult:
    start_url: str
    pages: list[Page] = field(default_factory=list)
    failures: list[Failure] = field(default_factory=list)

    def to_dict(self):
        return {
            "start_url": self.start_url,
            "pages": [asdict(page) for page in self.pages],
            "failures": [asdict(failure) for failure in self.failures],
        }
