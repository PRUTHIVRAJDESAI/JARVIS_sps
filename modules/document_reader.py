"""Read text from uploaded documents and source files."""

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except Exception:
    PYPDF_AVAILABLE = False


def extract_file_content(filepath: str, filename: str) -> str:
    """Extract text from PDF, code, CSV, or text files uploaded to J.A.R.V.I.S."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        if not PYPDF_AVAILABLE:
            return "[Error: pypdf not installed. Run: pip install pypdf]"
        try:
            reader = PdfReader(filepath)
            pages = []
            for idx, page in enumerate(reader.pages[:25]):
                txt = page.extract_text() or ""
                pages.append(f"--- Page {idx + 1} ---\n{txt.strip()}")
            return "\n\n".join(pages)[:20000]
        except Exception as exc:
            return f"[PDF Read Error: {exc}]"
    else:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                return f.read()[:20000]
        except Exception as exc:
            return f"[File Read Error: {exc}]"
