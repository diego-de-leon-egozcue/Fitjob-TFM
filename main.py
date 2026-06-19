"""
main.py — Fitjob · Backend FastAPI
Rutas, SSE, gestión de sesiones y orquestación de agentes.
"""

import asyncio
import json
import os
import shutil
import traceback
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from agents.analizador import run_analizador
from agents.optimizador_cv import run_optimizador_cv
from agents.redactor import run_redactor
from services.email_service import enviar_documentos
from services.pdf_extractor import extraer_texto_cv, EXTENSIONES_PERMITIDAS
from services.session_store import SessionStore

BASE_DIR = Path(__file__).parent
TMP_DIR  = BASE_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Fitjob")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/pages",  StaticFiles(directory=BASE_DIR / "pages"),  name="pages")

store = SessionStore()


# ── Utilidad: sesión ──────────────────────────────────────────────────────────

def get_session_id(fitjob_session: str | None) -> str:
    """Devuelve el session_id de la cookie, o lanza 401 si no existe."""
    if not fitjob_session:
        raise HTTPException(status_code=401, detail="Sesión no encontrada. Vuelve al inicio.")
    return fitjob_session


def session_tmp(session_id: str) -> Path:
    p = TMP_DIR / session_id
    p.mkdir(exist_ok=True)
    return p


# ── Páginas HTML ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing():
    return (BASE_DIR / "pages" / "index.html").read_text(encoding="utf-8")


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding():
    return (BASE_DIR / "pages" / "onboarding.html").read_text(encoding="utf-8")


@app.get("/processing", response_class=HTMLResponse)
async def processing():
    return (BASE_DIR / "pages" / "processing.html").read_text(encoding="utf-8")


@app.get("/results", response_class=HTMLResponse)
async def results():
    return (BASE_DIR / "pages" / "results.html").read_text(encoding="utf-8")


@app.get("/history", response_class=HTMLResponse)
async def history():
    return (BASE_DIR / "pages" / "history.html").read_text(encoding="utf-8")


# ── API: sesión ───────────────────────────────────────────────────────────────

@app.post("/api/session")
async def crear_sesion(response: Response):
    """Crea una nueva sesión y devuelve el session_id en cookie."""
    session_id = str(uuid.uuid4())
    store.create(session_id)
    response.set_cookie(
        key="fitjob_session",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=86400,  # 24h
    )
    return {"session_id": session_id}


# ── API: CV ───────────────────────────────────────────────────────────────────

@app.post("/api/cv")
async def subir_cv(
    file: UploadFile,
    fitjob_session: str | None = Cookie(default=None),
):
    session_id = get_session_id(fitjob_session)

    ext = Path(file.filename).suffix.lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail="Formato no soportado. Sube tu CV en PDF, Word (.docx) o texto (.txt).",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10 MB máximo
        raise HTTPException(status_code=400, detail="El archivo no puede superar los 10 MB.")

    # Guardar con la extensión original para extraer texto correctamente
    tmp = session_tmp(session_id)
    cv_path = tmp / f"cv_original{ext}"
    cv_path.write_bytes(contents)

    try:
        texto = extraer_texto_cv(cv_path)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not texto.strip():
        raise HTTPException(
            status_code=422,
            detail="No se pudo extraer texto del archivo. Si es un PDF escaneado como imagen, conviértelo a Word o copia el texto a un .txt.",
        )

    store.set(session_id, "cv_text", texto)
    store.set(session_id, "cv_filename", file.filename)

    return {"ok": True, "chars": len(texto)}


# ── API: perfil ───────────────────────────────────────────────────────────────

class PerfilPayload(BaseModel):
    sectores: list[str]
    modalidad: str
    ciudades: str
    salario_min: int
    moneda: str
    tipo_empresa: list[str]
    nivel_responsabilidad: str
    prioridades: list[str]
    rechazos: list[str]
    momento_carrera: str
    notas_adicionales: str = ""


@app.post("/api/profile")
async def guardar_perfil(
    payload: PerfilPayload,
    fitjob_session: str | None = Cookie(default=None),
):
    session_id = get_session_id(fitjob_session)
    store.set(session_id, "profile", payload.model_dump())
    return {"ok": True}


# ── API: oferta ───────────────────────────────────────────────────────────────

class OfertaPayload(BaseModel):
    texto: str
    limite_carta_larga: int = 0
    limite_carta_corta: int = 0


@app.post("/api/offer")
async def guardar_oferta(
    payload: OfertaPayload,
    fitjob_session: str | None = Cookie(default=None),
):
    session_id = get_session_id(fitjob_session)
    if len(payload.texto.strip()) < 100:
        raise HTTPException(status_code=400, detail="El texto de la oferta es demasiado corto.")
    store.set(session_id, "offer_text", payload.texto.strip())
    store.set(session_id, "limite_carta_larga", max(0, payload.limite_carta_larga))
    store.set(session_id, "limite_carta_corta", max(0, payload.limite_carta_corta))
    return {"ok": True}


# ── API: procesamiento SSE ────────────────────────────────────────────────────

def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _procesar(session_id: str):
    """Generador SSE que orquesta los tres agentes secuencialmente."""
    session = store.get(session_id)
    cv_text    = session.get("cv_text", "")
    profile    = session.get("profile", {})
    offer_text = session.get("offer_text", "")
    limite_carta_larga = session.get("limite_carta_larga", 0)
    limite_carta_corta = session.get("limite_carta_corta", 0)

    if not cv_text or not profile or not offer_text:
        yield sse("error_fatal", {"message": "Faltan datos. Vuelve al inicio y completa todos los pasos."})
        return

    job_id  = str(uuid.uuid4())[:8]
    tmp     = session_tmp(session_id)
    results = {"job_id": job_id}

    # ── Agente 1: Analizador ────────────────────────────────────────────────
    yield sse("agent_start", {
        "agent": 1,
        "message": "Comparando tu perfil con los requisitos de la oferta…",
    })
    try:
        analisis = await asyncio.to_thread(run_analizador, cv_text, profile, offer_text)
    except Exception as e:
        print(f"[Fitjob] ERROR Agente 1:\n{traceback.format_exc()}")
        yield sse("agent_error", {"agent": 1, "message": f"Error en el Analizador: {type(e).__name__}: {str(e)[:300]}"})
        return

    results["score"]     = analisis["score"]
    results["justificacion"] = analisis["justificacion"]
    results["puntos_fuertes"] = analisis["puntos_fuertes"]
    results["gaps"]      = analisis["gaps"]

    yield sse("agent_complete", {
        "agent": 1,
        "score": analisis["score"],
        "puntos_fuertes": analisis["puntos_fuertes"],
        "gaps": analisis["gaps"],
    })

    # ── Agente 2: Redactor ──────────────────────────────────────────────────
    yield sse("agent_start", {
        "agent": 2,
        "message": "Redactando tu carta de presentación personalizada…",
    })
    try:
        cartas = await asyncio.to_thread(run_redactor, cv_text, profile, offer_text, analisis, limite_carta_larga, limite_carta_corta)
    except Exception as e:
        print(f"[Fitjob] ERROR Agente 2:\n{traceback.format_exc()}")
        yield sse("agent_error", {"agent": 2, "message": f"Error en el Redactor: {type(e).__name__}: {str(e)[:300]}"})
        return

    results["carta"]       = cartas["carta"]
    results["carta_corta"] = cartas["carta_corta"]
    results["email_subject"] = cartas.get("email_subject", "")

    yield sse("agent_complete", {"agent": 2})

    # ── Agente 3: Optimizador CV ────────────────────────────────────────────
    yield sse("agent_start", {
        "agent": 3,
        "message": "Adaptando tu CV a esta oferta concreta…",
    })
    try:
        cv_data = await asyncio.to_thread(run_optimizador_cv, cv_text, offer_text, analisis, tmp, job_id)
    except Exception as e:
        print(f"[Fitjob] ERROR Agente 3:\n{traceback.format_exc()}")
        yield sse("agent_error", {"agent": 3, "message": f"Error en el Optimizador de CV: {type(e).__name__}: {str(e)[:300]}"})
        return

    results["cv_pdf"]        = cv_data.get("cv_pdf")
    results["offer_title"]   = cv_data.get("offer_title", "")
    results["offer_company"] = cv_data.get("offer_company", "")
    results["cv_nombre"]     = cv_data.get("cv_data", {}).get("nombre", "")

    yield sse("agent_complete", {"agent": 3})

    # ── Generar PDFs de cartas ──────────────────────────────────────────────
    from services.pdf_generator import carta_to_pdf, carta_corta_to_pdf
    try:
        carta_path       = tmp / f"{job_id}_carta.pdf"
        carta_corta_path = tmp / f"{job_id}_carta_corta.pdf"
        await asyncio.to_thread(carta_to_pdf, results["carta"], carta_path)
        await asyncio.to_thread(carta_corta_to_pdf, results["carta_corta"], carta_corta_path)
        results["carta_pdf"]       = str(carta_path)
        results["carta_corta_pdf"] = str(carta_corta_path)
    except Exception as e:
        # PDFs de carta no críticos — el usuario puede ver el texto igualmente
        results["carta_pdf"]       = None
        results["carta_corta_pdf"] = None

    # ── Guardar en historial de sesión ──────────────────────────────────────
    from datetime import datetime
    entry = {
        "job_id":        job_id,
        "offer_title":   results.get("offer_title", "Sin título"),
        "offer_company": results.get("offer_company", ""),
        "score":         results["score"],
        "timestamp":     datetime.now().strftime("%d/%m/%Y %H:%M"),
        "results":       results,
    }
    history = store.get(session_id).get("history", [])
    history.append(entry)
    history.sort(key=lambda x: x["score"], reverse=True)
    store.set(session_id, "history", history)
    store.set(session_id, f"results_{job_id}", results)

    yield sse("process_complete", {"job_id": job_id})


@app.get("/api/process/stream")
async def process_stream(
    request: Request,
    fitjob_session: str | None = Cookie(default=None),
):
    session_id = get_session_id(fitjob_session)

    async def event_generator():
        async for chunk in _procesar(session_id):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Utilidad: nombres de archivo ─────────────────────────────────────────────

def _nombre_archivo(s: str) -> str:
    """Convierte una cadena a nombre de archivo seguro (sin chars prohibidos)."""
    for ch in '/\\:*?"<>|':
        s = s.replace(ch, "")
    s = "_".join(s.split())   # espacios → guiones bajos
    return s[:60] if s else "Fitjob"


# ── API: resultados ───────────────────────────────────────────────────────────

@app.get("/api/results/{job_id}")
async def get_results(
    job_id: str,
    fitjob_session: str | None = Cookie(default=None),
):
    session_id = get_session_id(fitjob_session)
    results = store.get(session_id).get(f"results_{job_id}")
    if not results:
        raise HTTPException(status_code=404, detail="Resultados no encontrados.")
    return results


# ── API: descargas ────────────────────────────────────────────────────────────

@app.get("/api/download/{doc_type}/{job_id}")
async def descargar_documento(
    doc_type: str,
    job_id: str,
    fitjob_session: str | None = Cookie(default=None),
):
    session_id = get_session_id(fitjob_session)
    results = store.get(session_id).get(f"results_{job_id}")
    if not results:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    empresa = _nombre_archivo(results.get("offer_company", "empresa"))
    nombre  = _nombre_archivo(results.get("cv_nombre", "candidato"))

    key_map = {
        "cv":          ("cv_pdf",          f"CV_{nombre}_{empresa}.pdf"),
        "carta":       ("carta_pdf",       f"Carta_Presentación_{empresa}.pdf"),
        "carta-corta": ("carta_corta_pdf", f"Carta_Corta_{empresa}.pdf"),
    }
    if doc_type not in key_map:
        raise HTTPException(status_code=400, detail="Tipo de documento no válido.")

    key, filename = key_map[doc_type]
    path = results.get(key)
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="El archivo no está disponible.")

    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/pdf",
    )


# ── API: email ────────────────────────────────────────────────────────────────

class EmailPayload(BaseModel):
    email: str
    job_id: str


@app.post("/api/email")
async def enviar_email(
    payload: EmailPayload,
    fitjob_session: str | None = Cookie(default=None),
):
    session_id = get_session_id(fitjob_session)
    results = store.get(session_id).get(f"results_{payload.job_id}")
    if not results:
        raise HTTPException(status_code=404, detail="Resultados no encontrados.")

    docs = []
    for key in ("cv_pdf", "carta_pdf", "carta_corta_pdf"):
        p = results.get(key)
        if p and Path(p).exists():
            docs.append(Path(p))

    if not docs:
        raise HTTPException(status_code=404, detail="No hay documentos disponibles para enviar.")

    ok = await asyncio.to_thread(
        enviar_documentos,
        payload.email,
        results.get("offer_title", "tu oferta"),
        results.get("offer_company", ""),
        results.get("score", 0),
        docs,
        results.get("puntos_fuertes", []),
        results.get("gaps", []),
        results.get("cv_nombre", ""),
    )
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo enviar el email. Comprueba la configuración SMTP.")
    return {"ok": True}


# ── API: historial ────────────────────────────────────────────────────────────

@app.get("/api/history")
async def get_history(fitjob_session: str | None = Cookie(default=None)):
    session_id = get_session_id(fitjob_session)
    history = store.get(session_id).get("history", [])
    # Devolver versión resumida (sin el blob completo de resultados)
    summary = [
        {
            "job_id":        e["job_id"],
            "offer_title":   e["offer_title"],
            "offer_company": e["offer_company"],
            "score":         e["score"],
            "timestamp":     e["timestamp"],
        }
        for e in history
    ]
    return summary
