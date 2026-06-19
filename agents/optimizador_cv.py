"""
optimizador_cv.py — Agente 3: Optimizador de CV.
Extrae información del CV, la adapta a la oferta y genera PDF con la plantilla Fitjob.
"""

import json
import re
from pathlib import Path

from services.claude_cli import call_claude

SYSTEM_PROMPT = """Eres un experto en adaptación de CVs para candidatos a empleo.
Tu trabajo es tomar el CV de un candidato y adaptarlo a una oferta concreta, priorizando y reformulando la información más relevante.

REGLAS ABSOLUTAS:
1. NUNCA inventes datos, logros, experiencias ni habilidades que no estén en el CV original.
2. Solo reordenas, priorizas y reformulas — no añades información que no exista.
3. El CV adaptado siempre en inglés, sea cual sea el idioma de la oferta o el CV original.
4. Usa el lenguaje de la oferta para reformular bullets cuando sea posible (mismas palabras clave).
5. El titular debe ser una línea concisa que conecte el perfil del candidato con el puesto.

QUÉ PUEDES CAMBIAR:
- Titular/tagline: reformular para conectar con el puesto
- Orden de bullets dentro de cada experiencia: pon primero los más relevantes
- Redacción de bullets: usa palabras clave de la oferta, reformula el enfoque
- Selección de skills: prioriza las que pide la oferta

QUÉ NO PUEDES CAMBIAR:
- Nombres de empresas, instituciones ni títulos
- Fechas
- Datos personales de contacto
- Inventar experiencias, proyectos o habilidades

ESTRUCTURA DEL JSON DE SALIDA:
Devuelve un JSON con esta estructura. Incluye solo las secciones que existen en el CV original.

{
  "nombre": "<nombre completo del candidato>",
  "titular": "<una línea en inglés conectando perfil con puesto>",
  "contacto": {
    "email": "<email>",
    "telefono": "<teléfono>",
    "linkedin": "<URL linkedin si existe>",
    "ubicacion": "<ciudad/país si se menciona>",
    "web": "<web personal si existe>"
  },
  "info_personal": {
    "nacionalidad": "<si se menciona>",
    "fecha_nacimiento": "<si se menciona>"
  },
  "educacion": [
    {
      "institucion": "<nombre>",
      "titulo": "<título o grado>",
      "fechas": "<período>",
      "ubicacion": "<ciudad si se menciona>",
      "bullets": ["<punto relevante>"]
    }
  ],
  "experiencia": [
    {
      "empresa": "<nombre empresa>",
      "rol": "<cargo o puesto>",
      "departamento": "<departamento si se menciona>",
      "fechas": "<período>",
      "ubicacion": "<ciudad si se menciona>",
      "bullets": ["<bullet reformulado más relevante para la oferta>"]
    }
  ],
  "idiomas": "<línea con idiomas y nivel>",
  "habilidades": "<línea con habilidades técnicas priorizadas según la oferta>",
  "voluntariado": [
    {
      "descripcion": "<descripción>",
      "fechas": "<período>"
    }
  ],
  "adicional": "<cualquier sección adicional relevante>"
}

Responde ÚNICAMENTE con el JSON. Sin texto adicional, sin ```json."""


def run_optimizador_cv(
    cv_text: str,
    offer_text: str,
    analisis: dict,
    tmp_dir: Path,
    job_id: str,
) -> dict:
    """
    Adapta el CV a la oferta y genera el PDF con la plantilla Fitjob.
    Devuelve dict con 'cv_pdf', 'offer_title', 'offer_company'.
    """
    oferta_titulo  = analisis.get("oferta_titulo", "el puesto")
    oferta_empresa = analisis.get("oferta_empresa", "la empresa")
    puntos_fuertes = "\n".join(f"- {p}" for p in analisis.get("puntos_fuertes", []))

    prompt = f"""{SYSTEM_PROMPT}

[CV ORIGINAL DEL CANDIDATO]
{cv_text.strip()}

[OFERTA DE TRABAJO — {oferta_titulo} en {oferta_empresa}]
{offer_text.strip()}

[PUNTOS FUERTES IDENTIFICADOS PARA ESTA OFERTA]
{puntos_fuertes}

Adapta el CV del candidato para esta oferta concreta.
Prioriza y reformula la información existente para destacar lo más relevante.
Responde ÚNICAMENTE con el JSON indicado."""

    raw = call_claude(prompt, timeout=300)

    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        cv_data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            cv_data = json.loads(m.group(0))
        else:
            raise ValueError(f"El Optimizador no devolvió JSON válido: {raw[:300]}")

    from services.pdf_generator import cv_json_to_pdf
    cv_pdf_path = tmp_dir / f"{job_id}_cv.pdf"
    cv_json_to_pdf(cv_data, cv_pdf_path)

    return {
        "cv_pdf":        str(cv_pdf_path),
        "offer_title":   oferta_titulo,
        "offer_company": oferta_empresa,
        "cv_data":       cv_data,
    }
