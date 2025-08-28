# extractor.py
from io import BytesIO
import fitz  # PyMuPDF
import docx

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))
    return "\n".join(text_parts)

def extract_text_from_docx(file_bytes: bytes) -> str:
    f = BytesIO(file_bytes)
    d = docx.Document(f)
    return "\n".join(p.text for p in d.paragraphs)

def extract_text(filename: str, file_bytes: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    # Fallback: treat as plain text
    return file_bytes.decode(errors="ignore")
