"""
pdf_extractor.py — Extrae texto de CVs en PDF, DOCX o TXT.
"""

from pathlib import Path


EXTENSIONES_PERMITIDAS = {".pdf", ".docx", ".doc", ".txt"}


def extraer_texto_pdf(pdf_path: Path) -> str:
    """Extrae texto de un PDF con pdfplumber."""
    import pdfplumber

    partes = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=2, y_tolerance=2)
            if texto:
                partes.append(texto.strip())
    return "\n\n".join(partes)


def _extraer_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    partes = []
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            partes.append(t)
    return "\n".join(partes)


def _extraer_txt(path: Path) -> str:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def extraer_texto_cv(path: Path) -> str:
    """
    Extrae texto de un CV según su extensión.
    Soporta: .pdf, .docx, .doc, .txt
    """
    ext = path.suffix.lower()

    if ext == ".pdf":
        return extraer_texto_pdf(path)

    if ext in (".docx", ".doc"):
        try:
            return _extraer_docx(path)
        except Exception as e:
            raise ValueError(
                f"No se pudo leer el archivo Word. "
                f"Si es un .doc antiguo, conviértelo a .docx primero. ({e})"
            )

    if ext == ".txt":
        return _extraer_txt(path)

    raise ValueError(f"Formato no soportado: {ext}. Usa PDF, DOCX o TXT.")
