from pathlib import Path


def load_markdown_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    return path.read_text(encoding="utf-8")


def load_sample_documents(samples_dir: Path) -> dict[str, str]:
    documents: dict[str, str] = {}
    for path in sorted(samples_dir.glob("*.md")):
        documents[path.stem] = load_markdown_file(path)
    return documents