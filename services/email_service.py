"""
email_service.py — Envío de documentos por email via Gmail SMTP con diseño HTML.
"""

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path


def _fila_punto(texto: str, tipo: str) -> str:
    """Genera una fila HTML para un punto fuerte o área de mejora."""
    if tipo == "fuerte":
        icono = "✓"
        color_icono = "#4ade80"
        bg = "rgba(74,222,128,0.06)"
        borde = "rgba(74,222,128,0.2)"
    else:
        icono = "⚠"
        color_icono = "#F59E0B"
        bg = "rgba(245,158,11,0.06)"
        borde = "rgba(245,158,11,0.2)"

    return f"""
    <tr>
      <td style="padding:0 0 8px 0;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="background:{bg};border:1px solid {borde};border-radius:8px;">
          <tr>
            <td style="padding:12px 16px;">
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding-right:12px;vertical-align:top;font-size:14px;font-weight:700;color:{color_icono};line-height:1.5;">
                    {icono}
                  </td>
                  <td style="font-size:13px;color:rgba(255,255,255,0.75);line-height:1.5;vertical-align:top;">
                    {texto}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _construir_html(
    oferta_titulo: str,
    oferta_empresa: str,
    score: int,
    puntos_fuertes: list,
    gaps: list,
) -> str:
    empresa_str = oferta_empresa if oferta_empresa else "la empresa"
    score_color = (
        "#3B82F6" if score >= 70 else
        "#F59E0B" if score >= 40 else
        "#EF4444"
    )

    # Puntos fuertes
    filas_fuertes = "".join(_fila_punto(p, "fuerte") for p in puntos_fuertes if p)
    seccion_fuertes = f"""
    <tr>
      <td style="padding-bottom:8px;">
        <p style="margin:0 0 10px 0;font-size:12px;font-weight:700;color:#4ade80;letter-spacing:0.1em;text-transform:uppercase;">
          Puntos fuertes
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          {filas_fuertes}
        </table>
      </td>
    </tr>""" if filas_fuertes else ""

    # Áreas de mejora
    filas_gaps = "".join(_fila_punto(g, "gap") for g in gaps if g)
    seccion_gaps = f"""
    <tr>
      <td style="padding-bottom:36px;">
        <p style="margin:0 0 10px 0;font-size:12px;font-weight:700;color:#F59E0B;letter-spacing:0.1em;text-transform:uppercase;">
          Áreas de mejora
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          {filas_gaps}
        </table>
      </td>
    </tr>""" if filas_gaps else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#0a0a0a;">
    <tr>
      <td align="center" style="padding:40px 20px;">

        <!-- Contenedor principal -->
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;">

          <!-- Header: logo -->
          <tr>
            <td align="center" style="padding:40px 40px 24px;">
              <span style="font-size:28px;font-weight:900;color:#3B82F6;letter-spacing:-1px;">Fitjob</span>
            </td>
          </tr>

          <!-- Separador azul -->
          <tr>
            <td style="padding:0 40px;">
              <div style="height:2px;background:linear-gradient(90deg,transparent,#3B82F6,transparent);border-radius:2px;"></div>
            </td>
          </tr>

          <!-- Cuerpo principal -->
          <tr>
            <td style="background-color:#111111;border-radius:16px;padding:48px 48px 40px;margin-top:8px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">

                <!-- Título -->
                <tr>
                  <td style="padding-bottom:20px;">
                    <h1 style="margin:0;font-size:28px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;line-height:1.2;">
                      Tu candidatura está lista
                    </h1>
                  </td>
                </tr>

                <!-- Introducción -->
                <tr>
                  <td style="padding-bottom:36px;">
                    <p style="margin:0;font-size:15px;color:rgba(255,255,255,0.65);line-height:1.7;">
                      Hola, aquí tienes el análisis personalizado para tu candidatura al puesto de
                      <strong style="color:#ffffff;">{oferta_titulo}</strong>
                      en <strong style="color:#ffffff;">{empresa_str}</strong>.
                      Los documentos adaptados van adjuntos a este correo.
                    </p>
                  </td>
                </tr>

                <!-- Score -->
                <tr>
                  <td style="padding-bottom:36px;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="background-color:#0f0f0f;border:1px solid rgba(255,255,255,0.07);border-radius:12px;">
                      <tr>
                        <td align="center" style="padding:28px;">
                          <div style="font-size:64px;font-weight:900;color:{score_color};line-height:1;letter-spacing:-2px;">
                            {score}%
                          </div>
                          <div style="margin-top:10px;font-size:14px;color:rgba(255,255,255,0.5);font-weight:500;letter-spacing:0.02em;">
                            de encaje con esta oferta
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Puntos fuertes -->
                {seccion_fuertes}

                <!-- Áreas de mejora -->
                {seccion_gaps}

                <!-- Nota documentos adjuntos -->
                <tr>
                  <td style="padding-bottom:28px;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="background-color:#0f0f0f;border:1px solid rgba(59,130,246,0.2);border-radius:10px;">
                      <tr>
                        <td style="padding:16px 20px;">
                          <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.5);line-height:1.6;">
                            <span style="color:#3B82F6;font-weight:600;">📎 Adjuntos:</span>
                            CV Adaptado · Carta de Presentación · Carta Corta
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Párrafo final -->
                <tr>
                  <td>
                    <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.55);line-height:1.7;">
                      Recuerda revisar los documentos antes de enviarlos y personalizarlos si lo consideras necesario.
                      ¡Mucha suerte en tu candidatura!
                    </p>
                  </td>
                </tr>

              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:28px 40px 0;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background-color:#1a1a1a;border-radius:12px;">
                <tr>
                  <td align="center" style="padding:24px 32px;">
                    <p style="margin:0 0 8px 0;font-size:12px;color:rgba(255,255,255,0.4);line-height:1.6;">
                      Este email ha sido generado automáticamente por
                      <span style="color:#3B82F6;font-weight:600;">Fitjob</span>
                      · Asistente de empleo con IA
                    </p>
                    <p style="margin:0;font-size:11px;color:rgba(255,255,255,0.2);">
                      Si no solicitaste estos documentos puedes ignorar este mensaje.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>"""


def _nombre_archivo(s: str) -> str:
    for ch in '/\\:*?"<>|':
        s = s.replace(ch, "")
    s = "_".join(s.split())
    return s[:60] if s else "Fitjob"


def enviar_documentos(
    destinatario: str,
    oferta_titulo: str,
    oferta_empresa: str,
    score: int,
    documentos: list[Path],
    puntos_fuertes: list = None,
    gaps: list = None,
    cv_nombre: str = "",
) -> bool:
    """
    Envía los documentos generados al email del usuario.
    Devuelve True si el envío fue exitoso, False si falló.
    """
    gmail_user     = os.getenv("FITJOB_GMAIL_USER", "").strip()
    gmail_password = os.getenv("FITJOB_GMAIL_PASSWORD", "").strip()

    if not gmail_user or not gmail_password:
        return False

    empresa_str = f" en {oferta_empresa}" if oferta_empresa else ""
    asunto = f"Tus documentos de candidatura para {oferta_titulo}{empresa_str} — Fitjob"

    html_body = _construir_html(
        oferta_titulo,
        oferta_empresa,
        score,
        puntos_fuertes or [],
        gaps or [],
    )
    texto_plano = (
        f"Tu candidatura está lista\n\n"
        f"Análisis para {oferta_titulo}{empresa_str}\n\n"
        f"Encaje calculado: {score}%\n\n"
        f"Puntos fuertes:\n" +
        "\n".join(f"• {p}" for p in (puntos_fuertes or [])) +
        f"\n\nÁreas de mejora:\n" +
        "\n".join(f"• {g}" for g in (gaps or [])) +
        f"\n\nDocumentos adjuntos: CV Adaptado, Carta de Presentación, Carta Corta\n\n"
        f"¡Mucha suerte en tu candidatura!\n\n"
        f"— Fitjob · Asistente de empleo con IA"
    )

    msg = MIMEMultipart("alternative")
    msg["From"]    = formataddr(("Fitjob · Asistente de empleo", gmail_user))
    msg["To"]      = destinatario
    msg["Subject"] = asunto

    msg.attach(MIMEText(texto_plano, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,   "html",  "utf-8"))

    msg_outer = MIMEMultipart("mixed")
    msg_outer["From"]    = msg["From"]
    msg_outer["To"]      = msg["To"]
    msg_outer["Subject"] = msg["Subject"]
    msg_outer.attach(msg)

    empresa_fn = _nombre_archivo(oferta_empresa)
    nombre_fn  = _nombre_archivo(cv_nombre)
    nombres = {
        "_cv.pdf":          f"CV_{nombre_fn}_{empresa_fn}.pdf",
        "_carta.pdf":       f"Carta_Presentación_{empresa_fn}.pdf",
        "_carta_corta.pdf": f"Carta_Corta_{empresa_fn}.pdf",
    }

    for ruta in documentos:
        if ruta and ruta.exists():
            nombre_archivo = next(
                (v for k, v in nombres.items() if ruta.name.endswith(k)),
                ruta.name,
            )
            with open(ruta, "rb") as f:
                adjunto = MIMEApplication(f.read(), Name=nombre_archivo)
            adjunto["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
            msg_outer.attach(adjunto)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, destinatario, msg_outer.as_string())
        return True
    except smtplib.SMTPAuthenticationError:
        print("[Fitjob] Email: error de autenticación.")
        return False
    except Exception as e:
        print(f"[Fitjob] Email: {e}")
        return False
