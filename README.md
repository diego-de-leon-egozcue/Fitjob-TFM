# Fitjob — Asistente Inteligente de Búsqueda de Empleo

TFM de Diego de León Egozcue · Máster en IA Generativa e Innovación · Evolve Academy · 2026

---

## ¿Qué es Fitjob?

Fitjob es una aplicación web que ayuda a cualquier persona a:

1. **Analizar el encaje** entre su CV y una oferta de trabajo concreta (score de 0–100%)
2. **Generar una carta de presentación** personalizada (versión completa + versión corta para formularios)
3. **Adaptar su CV** a la oferta, generando un PDF con diseño profesional

Todo funciona mediante un sistema multiagente de IA que trabaja en segundo plano mientras el usuario ve una interfaz visual con personajes pixel art animados.

---

## Arquitectura

```
Fitjob/
├── main.py                      FastAPI: rutas, SSE, orquestación
├── requirements.txt             Dependencias Python
├── .env.example                 Plantilla de variables de entorno
│
├── agents/
│   ├── analizador.py            Agente 1: calcula % de encaje, puntos fuertes y gaps
│   ├── redactor.py              Agente 2: genera carta completa + carta corta (≤550 chars)
│   └── optimizador_cv.py        Agente 3: adapta el CV → JSON → PDF
│
├── services/
│   ├── claude_cli.py            Llamadas a Claude vía subprocess (sin API key)
│   ├── pdf_generator.py         Plantilla HTML del CV + conversión a PDF con Playwright
│   ├── pdf_extractor.py         Extrae texto de PDF, DOCX y TXT
│   ├── email_service.py         Envío de documentos por email (Gmail SMTP)
│   ├── session_store.py         Gestión de sesiones en memoria
│   └── _pdf_worker.py           Worker aislado para Playwright en Windows
│
├── pages/                       5 páginas HTML (landing, onboarding, processing, results, history)
└── static/                      CSS, JS, imágenes, sprites pixel art, webview de animación
```

### Stack técnico
- **Backend**: FastAPI + Uvicorn (Python)
- **Frontend**: HTML / CSS / JavaScript vanilla
- **IA**: Claude Code (`claude.exe`) vía subprocess — sin API key, usa la sesión activa
- **Tiempo real**: Server-Sent Events (SSE)
- **PDF generación**: Playwright Chromium
- **PDF extracción**: pdfplumber + python-docx
- **Sesiones**: diccionario en memoria + cookie UUID (sin base de datos)

### Los tres agentes (secuenciales)
Los agentes se ejecutan en orden: Analizador → Redactor → Optimizador CV.
Cada uno recibe el CV del usuario, su perfil de preferencias y el texto de la oferta.
El Agente 3 genera el CV adaptado siempre en inglés; la carta va en el idioma de la oferta.

---

## Requisitos previos

- **Python 3.10+**
- **Claude Code** instalado en VS Code con sesión activa — los agentes llaman a `claude.exe` por subprocess. Sin esto, la IA no funciona.

---

## Instalación y arranque

```bash
# 1. Clonar el repositorio
git clone https://github.com/diego-de-leon-egozcue/Fitjob-TFM.git
cd Fitjob-TFM

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Instalar el navegador de Playwright (solo la primera vez)
playwright install chromium

# 4. Configurar variables de entorno (opcional — solo para email)
cp .env.example .env
# Editar .env con las credenciales de Gmail

# 5. Arrancar el servidor
python -m uvicorn main:app --reload --port 8000
```

Abrir en el navegador: **http://localhost:8000**

La terminal debe quedar abierta mientras se usa la app. Para parar: `Ctrl + C`.

---

## Variables de entorno

Crear un archivo `.env` basado en `.env.example`:

| Variable | Para qué | Obligatoria |
|---|---|---|
| `CLAUDE_BIN` | Ruta manual al `claude.exe` (solo si no se detecta automáticamente) | No |
| `FITJOB_GMAIL_USER` | Email remitente para el envío de documentos | No |
| `FITJOB_GMAIL_PASSWORD` | App password de Google (no la contraseña normal) | No |

Las variables de email son opcionales. Sin ellas, la app funciona completa excepto el envío por correo.

---

## Flujo de usuario

1. **Landing** → botón "Empezar" crea sesión
2. **Onboarding** (3 pasos): sube tu CV (PDF / Word / TXT) · completa tu perfil · pega la oferta
3. **Procesamiento**: los 3 agentes trabajan en secuencia con animación pixel art en tiempo real
4. **Resultados**: score circular, puntos fuertes, gaps, carta y 3 descargas en PDF
5. **Historial**: todas las ofertas analizadas en la sesión, ordenadas por score

---

## Notas

- No hay login, registro ni base de datos. El historial se pierde al cerrar el navegador (por diseño).
- La carpeta `tmp/` se genera automáticamente y almacena los PDFs de cada sesión.
- El CV adaptado se genera siempre en inglés. La carta va en el idioma de la oferta.
