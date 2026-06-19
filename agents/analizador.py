"""
analizador.py — Agente 1: Analizador de encaje CV ↔ oferta.
Calcula porcentaje de afinidad, puntos fuertes y gaps.
"""

import json
import re

from services.claude_cli import call_claude

SYSTEM_PROMPT = """Eres un experto en selección de personal y orientación profesional.
Tu función es analizar con honestidad y precisión el encaje entre el perfil de un candidato y una oferta de trabajo concreta.

CRITERIOS DE PUNTUACIÓN (0-100%):
El porcentaje combina dos dimensiones con igual peso:

1. ENCAJE DE HABILIDADES (50%): ¿El CV cubre los requisitos técnicos de la oferta?
   - Experiencia laboral directamente relevante → sube
   - Herramientas y habilidades pedidas que el candidato tiene → sube
   - Formación alineada con el puesto → sube
   - Requisitos que el CV no cumple o cumple parcialmente → baja

2. ENCAJE CON LAS PREFERENCIAS DEL CANDIDATO (50%): ¿Esta oferta corresponde a lo que busca?
   - Modalidad de trabajo (presencial/híbrido/remoto) coincide → sube
   - Sector y tipo de empresa encajan con sus preferencias → sube
   - Nivel de responsabilidad apropiado → sube
   - Salario estimado por encima de su mínimo → sube
   - Condiciones que el candidato ha marcado como rechazos → penalización fuerte
   - Momento de carrera compatible con lo que ofrece el puesto → sube

IMPORTANTE:
- Sé honesto. No infles puntuaciones para quedar bien.
- Un gap real es un gap real — nómbralo claramente.
- Si el candidato marca algo como rechazo absoluto y la oferta lo tiene, penaliza fuerte.
- Los puntos fuertes deben ser específicos a esta oferta, no genéricos.
- Los gaps deben ser accionables, no juicios de valor.

FORMATO DE RESPUESTA (JSON estricto, sin markdown):
{
  "score": <número entero 0-100>,
  "justificacion": "<3-4 frases explicando el porcentaje de forma clara y honesta. IMPORTANTE: usa segunda persona directa (tú/tu) dirigiéndote al candidato. Ej: 'Tu perfil encaja bien porque…', 'No cumples el requisito de…', 'Tu experiencia en X es lo más relevante aquí.'>",
  "puntos_fuertes": [
    "<punto fuerte específico, en segunda persona. Ej: 'Tienes experiencia directa en…', 'Tu formación en X encaja con lo que piden.'>",
    "<punto fuerte>",
    "<punto fuerte>"
  ],
  "gaps": [
    "<gap en segunda persona. Ej: 'No tienes experiencia en X, que piden como requisito.', 'Tu nivel de inglés no queda claro en el CV.'>",
    "<gap>"
  ],
  "oferta_titulo": "<título del puesto extraído de la oferta>",
  "oferta_empresa": "<nombre de la empresa extraído de la oferta>"
}

Responde ÚNICAMENTE con el JSON. Sin texto adicional, sin ```json, sin explicaciones fuera del JSON."""


def _perfil_a_texto(profile: dict) -> str:
    sectores     = ", ".join(profile.get("sectores", [])) or "Sin especificar"
    modalidad    = profile.get("modalidad", "Sin especificar")
    ciudades     = profile.get("ciudades", "Sin especificar")
    salario      = f"{profile.get('salario_min', 0):,} {profile.get('moneda', 'EUR')} brutos/año"
    _te          = profile.get("tipo_empresa", [])
    tipo_empresa = ", ".join(_te) if isinstance(_te, list) else (_te or "Sin especificar")
    nivel        = profile.get("nivel_responsabilidad", "Sin especificar")
    prioridades  = ", ".join(profile.get("prioridades", [])) or "Sin especificar"
    rechazos     = ", ".join(profile.get("rechazos", [])) or "Ninguno indicado"
    momento      = profile.get("momento_carrera", "Sin especificar")
    notas        = profile.get("notas_adicionales", "").strip()

    texto = f"""PREFERENCIAS Y PERFIL PROFESIONAL:
- Sectores de interés: {sectores}
- Modalidad buscada: {modalidad}
- Ciudades: {ciudades}
- Salario mínimo aceptable: {salario}
- Tipo de empresa preferida: {tipo_empresa}
- Nivel de responsabilidad buscado: {nivel}
- Prioridades en el trabajo: {prioridades}
- Condiciones que rechazaría: {rechazos}
- Momento de carrera: {momento}"""

    if notas:
        texto += f"\n- Notas adicionales: {notas}"

    return texto


def run_analizador(cv_text: str, profile: dict, offer_text: str) -> dict:
    """
    Ejecuta el Analizador y devuelve un dict con score, justificacion,
    puntos_fuertes, gaps, oferta_titulo y oferta_empresa.
    """
    perfil_texto = _perfil_a_texto(profile)

    prompt = f"""{SYSTEM_PROMPT}

[CV DEL CANDIDATO]
{cv_text.strip()}

[PREFERENCIAS DEL CANDIDATO]
{perfil_texto}

[OFERTA DE TRABAJO]
{offer_text.strip()}

Analiza el encaje y responde con el JSON indicado."""

    raw = call_claude(prompt, timeout=180)

    # Limpiar posibles bloques markdown
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
        else:
            raise ValueError(f"El Analizador no devolvió JSON válido: {raw[:300]}")

    data.setdefault("score", 0)
    data.setdefault("justificacion", "")
    data.setdefault("puntos_fuertes", [])
    data.setdefault("gaps", [])
    data.setdefault("oferta_titulo", "")
    data.setdefault("oferta_empresa", "")
    data["score"] = max(0, min(100, int(data["score"])))

    return data
