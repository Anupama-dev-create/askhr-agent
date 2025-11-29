import io
from typing import List, Dict
from PyPDF2 import PdfReader

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
        text += "\n"
    return text

def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return file_bytes.decode(errors="ignore")

def split_text(text: str, max_chars: int = 1000, overlap: int = 200) -> List[str]:
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end]
        chunks.append(chunk.strip())
        if end == length:
            break
        start = end - overlap
    return [c for c in chunks if c]

def build_documents(uploaded_files) -> List[Dict]:
    """
    uploaded_files: List[streamlit.UploadedFile]
    Returns list of dicts: [{'text': ..., 'source': ...}, ...]
    """
    docs: List[Dict] = []
    for f in uploaded_files:
        name = f.name
        data = f.read()
        if name.lower().endswith(".pdf"):
            full_text = extract_text_from_pdf(data)
        else:
            full_text = extract_text_from_txt(data)

        chunks = split_text(full_text)
        for idx, chunk in enumerate(chunks):
            docs.append(
                {
                    "text": chunk,
                    "source": name,
                    "chunk_id": idx,
                }
            )
    return docs
