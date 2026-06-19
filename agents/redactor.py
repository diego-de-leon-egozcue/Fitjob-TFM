"""
redactor.py — Agente 2: Redactor de carta de presentación.
Genera carta completa + carta corta para formularios.
"""

import re

from services.claude_cli import call_claude

SYSTEM_PROMPT = """Eres un experto en redacción de cartas de presentación para candidatos a empleo.
Tu trabajo es escribir cartas personalizadas, directas y naturales — nunca genéricas ni con clichés corporativos.

REGLAS ABSOLUTAS:
1. NUNCA inventes datos, logros, experiencias ni habilidades que no estén en el CV del candidato.
2. Solo reordenas y reformulas lo que ya existe en el CV.
3. La carta debe sonar humana y genuina, no como una plantilla.
4. El idioma de la carta debe coincidir con el idioma de la oferta (si la oferta es en español → carta en español; en inglés → carta en inglés).
5. La carta corta debe tener MÁXIMO 550 caracteres (cuenta exactamente).

ESTRUCTURA DE LA CARTA COMPLETA (180-230 palabras):
- Párrafo 1 — Apertura: menciona el puesto y la empresa por su nombre. Explica brevemente por qué esta oferta te llama la atención de forma genuina y específica.
- Párrafo 2 — Formación: menciona la formación más relevante para ESTE puesto.
- Párrafo 3 — Experiencia: menciona la experiencia más relevante del CV para ESTA oferta concreta. Conecta lo que hizo con lo que pide la oferta.
- Párrafo 4 — Por qué este rol: conexión honesta entre el puesto/empresa y lo que busca el candidato.
- Cierre: "Quedo a disposición para cualquier información. Un saludo, [Nombre]" (adaptar al idioma).

ESTILO:
- Directo, sin rigidez corporativa.
- No uses: "no dudaré en", "adjunto mi CV", "me dirijo a usted", "estimado/a", "en relación a", ni clichés similares.
- Usa el nombre real del candidato, empresa y puesto.

CARTA CORTA (para formularios online):
- Máximo 550 caracteres exactos (incluyendo espacios).
- 2-3 frases: quién es + experiencia relevante para ESTA oferta + por qué le interesa.
- Sin saludo inicial ni firma. Funciona sola, sin contexto adicional.

ASUNTO DEL EMAIL:
- Conciso y profesional.
- Formato: "Candidatura — [Puesto] | [Nombre del candidato]"

FORMATO DE RESPUESTA (marcadores exactos):
[CARTA]
<carta completa>
[/CARTA]

[CARTA_CORTA]
<carta corta, máximo 550 caracteres>
[/CARTA_CORTA]

[EMAIL_SUBJECT]
<asunto del email>
[/EMAIL_SUBJECT]"""


def run_redactor(
    cv_text: str,
    profile: dict,
    offer_text: str,
    analisis: dict,
    limite_carta_larga: int = 0,
    limite_carta_corta: int = 0,
) -> dict:
    """
    Ejecuta el Redactor y devuelve carta, carta_corta y email_subject.
    limite_carta_larga / limite_carta_corta: 0 = sin límite definido por el usuario.
    """
    nombre_candidato = _extraer_nombre(cv_text)
    oferta_titulo    = analisis.get("oferta_titulo", "el puesto")
    oferta_empresa   = analisis.get("oferta_empresa", "la empresa")
    puntos_fuertes   = "\n".join(f"- {p}" for p in analisis.get("puntos_fuertes", []))
    gaps             = "\n".join(f"- {g}" for g in analisis.get("gaps", []))

    # Construir reglas de longitud según los límites indicados por el usuario
    if limite_carta_larga > 0:
        regla_larga = f"La carta completa debe tener MÁXIMO {limite_carta_larga} caracteres (cuenta exactamente, incluyendo espacios)."
    else:
        regla_larga = "La carta completa debe tener entre 180 y 230 palabras."

    if limite_carta_corta > 0:
        regla_corta = f"La carta corta debe tener MÁXIMO {limite_carta_corta} caracteres (cuenta exactamente, incluyendo espacios)."
    else:
        regla_corta = "La carta corta debe tener MÁXIMO 550 caracteres (incluyendo espacios)."

    # Construir el system prompt con las reglas dinámicas
    system_prompt_dinamico = SYSTEM_PROMPT.replace(
        "5. La carta corta debe tener MÁXIMO 550 caracteres (cuenta exactamente).",
        f"5. {regla_corta}",
    ).replace(
        "ESTRUCTURA DE LA CARTA COMPLETA (180-230 palabras):",
        f"ESTRUCTURA DE LA CARTA COMPLETA ({regla_larga}):",
    ).replace(
        "Máximo 550 caracteres exactos (incluyendo espacios).",
        f"{regla_corta}",
    )

    prompt = f"""{system_prompt_dinamico}

[CV DEL CANDIDATO]
{cv_text.strip()}

[OFERTA DE TRABAJO — {oferta_titulo} en {oferta_empresa}]
{offer_text.strip()}

[ANÁLISIS PREVIO DEL ENCAJE]
Puntos fuertes del candidato para esta oferta:
{puntos_fuertes}

Gaps o áreas de mejora:
{gaps}

[INSTRUCCIÓN]
Escribe la carta de presentación, la carta corta y el asunto del email para que {nombre_candidato} se postule a {oferta_titulo} en {oferta_empresa}.
Usa el análisis previo para destacar los puntos fuertes correctos y no mencionar los gaps.
Responde EXACTAMENTE con el formato de marcadores indicado."""

    raw = call_claude(prompt, timeout=240)

    carta       = _extraer_bloque(raw, "CARTA")
    carta_corta = _extraer_bloque(raw, "CARTA_CORTA")
    email_subj  = _extraer_bloque(raw, "EMAIL_SUBJECT")

    # Truncar carta corta si supera el límite (defensa de última capa)
    limite_corta_efectivo = limite_carta_corta if limite_carta_corta > 0 else 550
    if len(carta_corta) > limite_corta_efectivo:
        carta_corta = carta_corta[:limite_corta_efectivo - 3] + "…"

    return {
        "carta":         carta,
        "carta_corta":   carta_corta,
        "email_subject": email_subj,
    }


def _extraer_bloque(texto: str, etiqueta: str) -> str:
    m = re.search(
        rf"\[{re.escape(etiqueta)}\]\s*(.*?)\s*\[/{re.escape(etiqueta)}\]",
        texto,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


def _extraer_nombre(cv_text: str) -> str:
    lineas = [l.strip() for l in cv_text.strip().split("\n") if l.strip()]
    if lineas:
        primera = lineas[0]
        if len(primera) < 60 and "@" not in primera and "/" not in primera:
            return primera
    return "el candidato"
