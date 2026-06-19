"""
pdf_generator.py — Generación de PDFs con Playwright.
cv_json_to_pdf: renderiza el JSON del Agente 3 en la plantilla Fitjob → PDF.
carta_to_pdf / carta_corta_to_pdf: convierte texto de carta → PDF limpio.
"""

import html as html_lib
import subprocess
import sys
import tempfile
from pathlib import Path

_WORKER = Path(__file__).parent / "_pdf_worker.py"


def _esc(t: str) -> str:
    return html_lib.escape(str(t)) if t else ""


# ── Plantilla CV Fitjob ───────────────────────────────────────────────────────

def _render_cv_html(data: dict) -> str:
    """
    Genera el HTML completo del CV usando el diseño Fitjob.
    El contenido es dinámico (cualquier candidato), el diseño es siempre el mismo.
    """

    def li(items: list) -> str:
        return "\n".join(f'<li>{_esc(b)}</li>' for b in items if b and b.strip())

    nombre   = _esc(data.get("nombre", ""))
    titular  = _esc(data.get("titular", ""))
    contacto = data.get("contacto", {})
    info_p   = data.get("info_personal", {})

    # Contacto: email, teléfono, linkedin, ubicación
    email     = _esc(contacto.get("email", ""))
    telefono  = _esc(contacto.get("telefono", ""))
    linkedin  = contacto.get("linkedin", "")
    ubicacion = _esc(contacto.get("ubicacion", ""))
    web       = contacto.get("web", "")

    # Info personal
    nacionalidad     = _esc(info_p.get("nacionalidad", ""))
    fecha_nacimiento = _esc(info_p.get("fecha_nacimiento", ""))

    # Columna izquierda de contacto (información personal)
    col_izq = ""
    if nacionalidad or fecha_nacimiento:
        col_izq += '<div class="info-col">'
        col_izq += '<div class="col-header">Personal Information</div>'
        if nacionalidad:
            col_izq += f'<div>Nationality: {nacionalidad}</div>'
        if fecha_nacimiento:
            col_izq += f'<div>Birth Date: {fecha_nacimiento}</div>'
        if ubicacion:
            col_izq += f'<div>Location: {ubicacion}</div>'
        col_izq += '</div>'

    # Columna derecha de contacto
    col_der = '<div class="info-col">'
    col_der += '<div class="col-header">Contact Information</div>'
    if telefono:
        col_der += f'<div>Mobile: {telefono}</div>'
    if email:
        col_der += f'<div>{email}</div>'
    if linkedin:
        linkedin_esc = _esc(linkedin)
        col_der += f'<div><a href="{linkedin_esc}">{linkedin_esc}</a></div>'
    if web and not linkedin:
        web_esc = _esc(web)
        col_der += f'<div><a href="{web_esc}">{web_esc}</a></div>'
    col_der += '</div>'

    # Si no hay info personal, solo mostramos columna de contacto sin grid
    if col_izq:
        info_grid = f'<div class="info-grid">{col_izq}{col_der}</div>'
    else:
        info_grid = f'<div class="info-grid-single">{col_der}</div>'

    # Educación
    educacion_html = ""
    for edu in data.get("educacion", []):
        bullets = li(edu.get("bullets", []))
        bullets_html = f'<ul class="entry-bullets">{bullets}</ul>' if bullets else ""
        loc = _esc(edu.get("ubicacion", ""))
        loc_html = f'<span class="entry-location">{loc}</span>' if loc else ""
        dept = _esc(edu.get("departamento", ""))
        dept_html = f'<span class="entry-role">{dept}</span>' if dept else f'<span class="entry-role">{_esc(edu.get("titulo",""))}</span>'

        educacion_html += f"""
    <div class="entry">
      <div class="entry-header">
        <span class="entry-company">{_esc(edu.get("institucion",""))}</span>
        {loc_html}
      </div>
      <div class="entry-sub">
        <span class="entry-role">{_esc(edu.get("titulo",""))}</span>
        <span class="entry-dates">{_esc(edu.get("fechas",""))}</span>
      </div>
      {bullets_html}
    </div>"""

    # Experiencia
    experiencia_html = ""
    for exp in data.get("experiencia", []):
        bullets = li(exp.get("bullets", []))
        bullets_html = f'<ul class="entry-bullets">{bullets}</ul>' if bullets else ""
        loc = _esc(exp.get("ubicacion", ""))
        loc_html = f'<span class="entry-location">{loc}</span>' if loc else ""
        dept = _esc(exp.get("departamento", ""))
        dept_html = f'<span class="entry-role">{dept}</span>' if dept else ""

        experiencia_html += f"""
    <div class="entry">
      <div class="entry-header">
        <span class="entry-company">{_esc(exp.get("empresa",""))}</span>
        {loc_html}
      </div>
      <div class="entry-sub">
        <span class="entry-role">{_esc(exp.get("rol",""))}</span>
        <span class="entry-dates">{_esc(exp.get("fechas",""))}</span>
      </div>
      {f'<div class="entry-dept">{dept}</div>' if dept else ""}
      {bullets_html}
    </div>"""

    # Idiomas y habilidades
    idiomas      = _esc(data.get("idiomas", ""))
    habilidades  = _esc(data.get("habilidades", ""))
    lang_skills_html = ""
    if idiomas or habilidades:
        lang_skills_html = '<div class="section"><div class="section-title">Languages &amp; Digital Skills</div>'
        if idiomas:
            lang_skills_html += f'<div class="skills-row"><span class="skills-label">Languages</span> – {idiomas}</div>'
        if habilidades:
            lang_skills_html += f'<div class="skills-row"><span class="skills-label">Technical &amp; Digital Skills:</span><ul class="entry-bullets" style="margin-top:3px;"><li>{habilidades}</li></ul></div>'
        lang_skills_html += '</div>'

    # Voluntariado
    voluntariado_html = ""
    voluntariado = data.get("voluntariado", [])
    if voluntariado:
        vol_items = ""
        for v in voluntariado:
            desc  = _esc(v.get("descripcion", ""))
            dates = _esc(v.get("fechas", ""))
            vol_items += f"""
      <li>
        <div class="vol-item">
          <span class="vol-text">{desc}</span>
          <span class="vol-year">{dates}</span>
        </div>
      </li>"""
        voluntariado_html = f"""
  <div class="section">
    <div class="section-title">Volunteering Experience</div>
    <div class="entry">
      <ul class="entry-bullets" style="margin-top:5px;">{vol_items}</ul>
    </div>
  </div>"""

    # Información adicional
    adicional_html = ""
    adicional = data.get("adicional", "").strip()
    if adicional:
        adicional_html = f"""
  <div class="section">
    <div class="section-title">Additional Information</div>
    <div class="skills-row">{_esc(adicional)}</div>
  </div>"""

    # Secciones de educación y experiencia (orden: experiencia primero si existe)
    exp_section = f"""
  <div class="section">
    <div class="section-title">Work Experience</div>
    {experiencia_html}
  </div>""" if data.get("experiencia") else ""

    edu_section = f"""
  <div class="section">
    <div class="section-title">Education</div>
    {educacion_html}
  </div>""" if data.get("educacion") else ""

    # Si hay experiencia, va antes que educación
    main_sections = exp_section + edu_section if exp_section else edu_section

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CV — {nombre}</title>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{
      font-family: 'Calibri', 'Arial', sans-serif;
      font-size: 11pt;
      color: #000;
      background: #e0e0e0;
      padding: 30px 20px;
    }}
    .page {{
      background: #fff;
      max-width: 780px;
      margin: 0 auto;
      padding: 52px 62px;
      box-shadow: 0 3px 28px rgba(0,0,0,0.18);
    }}
    .cv-name {{
      font-size: 24pt;
      font-weight: bold;
      margin-bottom: 14px;
    }}
    .info-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      font-size: 10.5pt;
      margin-bottom: 6px;
    }}
    .info-grid-single {{
      font-size: 10.5pt;
      margin-bottom: 6px;
    }}
    .info-col .col-header {{
      font-weight: bold;
      text-decoration: underline;
      margin-bottom: 3px;
    }}
    .info-col div {{ line-height: 1.55; }}
    .info-col a {{ color: #0563C1; text-decoration: underline; }}
    .info-grid-single .col-header {{
      font-weight: bold;
      text-decoration: underline;
      margin-bottom: 3px;
    }}
    .info-grid-single a {{ color: #0563C1; text-decoration: underline; }}
    .info-grid-single div {{ line-height: 1.55; }}
    .tagline {{
      font-weight: bold;
      font-size: 10.5pt;
      text-align: center;
      margin: 8px 0 16px 0;
    }}
    .section {{ margin-top: 14px; }}
    .section-title {{
      font-weight: bold;
      text-decoration: underline;
      font-size: 10.5pt;
      text-transform: uppercase;
      border-bottom: 1.2px solid #000;
      padding-bottom: 1px;
      margin-bottom: 9px;
    }}
    .entry {{ margin-bottom: 10px; }}
    .entry-header {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }}
    .entry-company {{ font-weight: bold; font-size: 10.5pt; }}
    .entry-location {{
      font-weight: bold;
      font-size: 10.5pt;
      white-space: nowrap;
      margin-left: 10px;
    }}
    .entry-sub {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }}
    .entry-role {{ font-style: italic; font-size: 10.5pt; }}
    .entry-dept {{ font-style: italic; font-size: 10pt; color: #333; margin-top: 1px; }}
    .entry-dates {{
      font-style: italic;
      font-size: 10.5pt;
      white-space: nowrap;
      margin-left: 10px;
    }}
    .entry-bullets {{
      margin-top: 4px;
      padding-left: 20px;
    }}
    .entry-bullets li {{
      font-size: 10.5pt;
      line-height: 1.45;
      margin-bottom: 2px;
    }}
    .skills-row {{ font-size: 10.5pt; margin-bottom: 5px; line-height: 1.5; }}
    .skills-label {{ font-weight: bold; }}
    .vol-item {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 2px;
    }}
    .vol-text {{ font-style: italic; font-size: 10.5pt; }}
    .vol-year {{ font-size: 10.5pt; white-space: nowrap; margin-left: 16px; }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .page {{ box-shadow: none; padding: 28px 38px; }}
    }}
  </style>
</head>
<body>
<div class="page">

  <div class="cv-name">{nombre}</div>

  {info_grid}

  {f'<div class="tagline">{titular}</div>' if titular else ""}

  {main_sections}

  {lang_skills_html}

  {voluntariado_html}

  {adicional_html}

</div>
</body>
</html>"""


def cv_json_to_pdf(cv_data: dict, output_path: Path) -> None:
    """Renderiza el JSON del CV en la plantilla Fitjob y genera el PDF."""
    html_content = _render_cv_html(cv_data)
    _html_to_pdf(html_content, output_path)


# ── PDF de cartas ─────────────────────────────────────────────────────────────

def carta_to_pdf(carta: str, output_path: Path) -> None:
    paragraphs = [p.strip() for p in carta.split("\n") if p.strip()]
    paras_html = "".join(f"<p>{_esc(p)}</p>" for p in paragraphs)
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Calibri','Arial',sans-serif; font-size:11pt; color:#000; padding:60px 70px; }}
  p {{ margin-bottom:14px; line-height:1.65; text-align:justify; }}
</style>
</head>
<body>{paras_html}</body>
</html>"""
    _html_to_pdf(html, output_path)


def carta_corta_to_pdf(carta_corta: str, output_path: Path) -> None:
    char_count = len(carta_corta)
    paragraphs = [p.strip() for p in carta_corta.split("\n") if p.strip()]
    paras_html = "".join(f"<p>{_esc(p)}</p>" for p in paragraphs)
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Calibri','Arial',sans-serif; font-size:11pt; color:#000; padding:60px 70px; }}
  .label {{ font-size:9pt; color:#888; border-bottom:1px solid #ddd; padding-bottom:8px; margin-bottom:20px; }}
  p {{ line-height:1.65; margin-bottom:12px; text-align:justify; }}
  .chars {{ font-size:9pt; color:#aaa; margin-top:16px; }}
</style>
</head>
<body>
<div class="label">Versión para formulario web</div>
{paras_html}
<div class="chars">{char_count} caracteres</div>
</body>
</html>"""
    _html_to_pdf(html, output_path)


def _html_to_pdf(html_content: str, output_path: Path) -> None:
    """
    Convierte HTML a PDF lanzando Playwright en un subproceso separado.
    Esto evita el conflicto entre Playwright y el event loop de asyncio en Windows.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(html_content)
        html_tmp = Path(tmp.name)

    try:
        result = subprocess.run(
            [sys.executable, str(_WORKER), str(html_tmp), str(output_path)],
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"PDF worker falló (código {result.returncode}): {result.stderr[:400]}"
            )
    finally:
        html_tmp.unlink(missing_ok=True)
