# HANDOFF — Fitjob · Asistente Inteligente de Búsqueda de Empleo

> Documento de traspaso para continuar el desarrollo sin perder contexto.
> Estado: **funcional y corriendo**. Última actualización: 2026-06-16.

---

## Qué es Fitjob

Fitjob es una aplicación web que ayuda a cualquier persona a:
1. Entender si una oferta de trabajo encaja realmente con su perfil
2. Adaptar su CV a esa oferta concreta
3. Generar una carta de presentación personalizada

Todo mediante un sistema multiagente de IA que trabaja en segundo plano mientras el usuario ve una interfaz visual.

**Contexto**: TFM de Diego de León Egozcue en el Máster en IA Generativa e Innovación de Evolve Academy. Demo en vivo el **19 de junio de 2026**. No puede fallar nada en la demo.

**Base**: se construye a partir del proyecto PACO (`Paco_agente_empleo/`). Fitjob reutiliza la lógica de agentes pero la migra a web y la hace genérica para cualquier usuario (no solo Diego).

---

## Cómo arrancar el servidor (instrucción principal)

```bash
cd "C:\Users\Asus\OneDrive\Documentos\Máster Evolve\Fitjob"
python -m uvicorn main:app --reload --port 8000
```

Abrir en Chrome: **`http://localhost:8000`**

La terminal debe quedarse abierta mientras se usa la app. Para parar: `Ctrl + C`.

**Primera vez (ya hecho, no repetir):**
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## Estado actual: TODO COMPLETADO Y FUNCIONANDO

### Archivos creados y verificados

```
Fitjob/
├── main.py                      ✅ FastAPI: rutas, SSE, orquestación, _nombre_archivo()
├── requirements.txt             ✅ Sin anthropic + python-docx añadido
├── .env                         ✅ FITJOB_GMAIL_USER/PASSWORD configurados
├── .env.example                 ✅ Plantilla documentada
│
├── agents/
│   ├── analizador.py            ✅ Agente 1: encaje CV↔oferta → JSON con score
│   ├── redactor.py              ✅ Agente 2: carta completa + carta corta
│   └── optimizador_cv.py        ✅ Agente 3: CV adaptado → JSON → PDF
│
├── services/
│   ├── claude_cli.py            ✅ Wrapper subprocess → claude.exe (como PACO)
│   ├── session_store.py         ✅ Dict en memoria thread-safe
│   ├── pdf_extractor.py         ✅ PDF + DOCX + TXT → texto (multi-formato)
│   ├── pdf_generator.py         ✅ Plantilla CV Fitjob + Playwright (via worker)
│   ├── _pdf_worker.py           ✅ Subproceso aislado para Playwright (fix Windows asyncio)
│   └── email_service.py         ✅ Gmail SMTP + HTML diseñado + puntos fuertes/gaps
│
├── pages/
│   ├── index.html               ✅ Landing: foto hero a sangre (static/img/hero.jpg.webp) + SVG IA mini centrado abajo
│   ├── onboarding.html          ✅ 3 pasos: CV (PDF/DOCX/TXT) + perfil + oferta
│   ├── processing.html          ✅ Canvas pixel art + paneles de agentes
│   ├── results.html             ✅ Score circular + descargas + email
│   └── history.html             ✅ Historial de sesión con JS integrado
│
├── static/
│   ├── css/styles.css           ✅ Sistema de diseño completo
│   ├── img/
│   │   └── hero.jpg.webp        ✅ Foto hero landing (entrevista de trabajo)
│   ├── js/
│   │   ├── onboarding.js        ✅ Chips con "Otro"+texto libre, upload multi-formato, validación, API calls
│   │   ├── processing.js        ✅ Puente SSE↔postMessage al webview pixel-agents (iframe)
│   │   └── results.js           ✅ Score animado, descargas, email, historial
│   ├── sprites/                 ✅ Assets pixel-agents copiados localmente (chars, floors, furniture)
│   └── pixel-agents-webview/    ✅ Webview oficial de la extensión pixel-agents (React bundle + assets)
│       └── assets/
│           └── fitjob-layout.json  ✅ Layout personalizado: 3 escritorios + zona break
│
└── tmp/                         ✅ Carpeta creada (PDFs por sesión)
```

### Verificaciones realizadas
- ✅ Servidor arranca sin errores: `uvicorn main:app --port 8000`
- ✅ Los 9 módulos Python importan correctamente
- ✅ `find_claude_bin()` detecta: `anthropic.claude-code-2.1.175-win32-x64/resources/native-binary/claude.exe`
- ✅ `call_claude("Responde solo con: OK")` → devuelve `"OK"`
- ✅ pdfplumber 0.11.4 instalado
- ✅ Playwright/Chromium instalado y funcional
- ✅ Todas las páginas responden 200: `/`, `/onboarding`, `/processing`, `/results`, `/history`
- ✅ Todos los estáticos sirven correctamente
- ✅ `POST /api/session` crea sesión con cookie UUID

---

## Decisiones de diseño fijadas (no reabrir)

### Stack técnico
- **Backend**: FastAPI + Uvicorn (Python)
- **Frontend**: HTML/CSS/JS vanilla (sin frameworks)
- **IA**: `claude.exe` via subprocess — **igual que PACO**, sin API key, usa la sesión de Claude Code activa en VSCode
- **PDF extracción**: `pdfplumber`
- **PDF generación**: Playwright Chromium
- **Real-time**: Server-Sent Events (SSE)
- **Sesiones**: diccionario en memoria del servidor + cookie UUID (sin base de datos)
- **Email**: Gmail SMTP vía `smtplib` (opcional, no crítico para la demo)

### Lo que NO existe y no hay que añadir
- Sin login ni registro
- Sin base de datos (todo en memoria, se pierde al cerrar el navegador — por diseño)
- Sin búsqueda automática de ofertas (ni SerpAPI ni Adzuna)
- Sin integración Notion
- Sin bot de Telegram
- No responsive para móvil (solo escritorio)

### Diseño visual — Landing (actualizado 2026-06-14)
- **Hero derecho**: foto `static/img/hero.jpg.webp` a sangre, ocupa la mitad derecha hasta el borde con `object-fit: cover`. Gradiente CSS izquierda→transparente para legibilidad del texto. El `div.hero-right` tiene `margin-right: -60px` para cancelar el padding y llegar al borde.
- **SVG mini (IA analysis)**: posición `absolute` centrado horizontalmente (`left:50%; transform:translateX(-50%)`), `bottom: 48px`, `width: 360px`, `z-index: 5`. Es hijo directo del `<section class="hero">` (no de `hero-right`). Muestra CV + oferta + badge "82% match".
- **Navbar landing**: logo + "Mis ofertas" (btn-ghost) + "Empezar" (btn-primary)
- **Navbar páginas internas**: todas incluyen "Mis ofertas" como btn-ghost en la esquina derecha

### Diseño visual
- **Landing**: fondo `#0a0a0a`
- **Páginas internas**: fondo `#1a1a1a`, tarjetas `#242424`
- **Acento**: azul eléctrico `#3B82F6`
- **Tipografía**: Inter (Google Fonts)
- **Colores de encaje** (usados en arco circular Y en historial):
  - ≥70% → `#3B82F6` azul
  - 40–69% → `#F59E0B` amarillo
  - <40% → `#EF4444` rojo
- **Ilustración landing**: SVG inline custom (escena de análisis de empleo con tarjetas y nodo IA). **No usa undraw.co** — la API no funciona, se hizo SVG propio.
- **Pantalla de procesamiento**: Canvas 860×480 con dos zonas. Sprites reales del repo `pixel-agents-hq/pixel-agents`: 6 personajes (char_0…5), 9 suelos, 22+ muebles (escritorios, PC animado, sofá, estanterías, whiteboard, plantas, etc.). Personajes 16×32 px escala ×3 (48×96 en canvas). Z-sorting por Y: desks se dibujan DESPUÉS de chars (deskY=410 > charY=370) → personaje aparece sentado detrás del escritorio. PC cicla entre ON_1/2/3 cuando el agente está activo.

### Los tres agentes
Los agentes NO tienen nombres propios. Solo se muestran sus funciones:
- **Analizador** (Agente 1): calcula % de encaje, puntos fuertes, gaps
- **Redactor** (Agente 2): carta completa + carta corta para formularios (máx 550 chars)
- **Optimizador de CV** (Agente 3): adapta el CV, genera JSON estructurado → plantilla Fitjob → PDF

Secuenciales: 1 → 2 → 3. Ninguno empieza hasta que el anterior termina.

### Gestión de errores en procesamiento
Si un agente falla: animación se detiene, ❗ rojo sobre el personaje fallido, panel de error con "Reintentar" y "Volver atrás". Nunca puede quedar la animación corriendo con el sistema roto.

---

## Flujo de usuario

### Pantalla 1 — Landing (`/`)
- Navbar fijo: logo "Fitjob" azul + botón "Empezar"
- Hero: título grande izquierda + ilustración SVG derecha
- Sección 3 pasos: "Sube tu CV", "Pega la oferta", "Obtén tu propuesta"
- Clic "Empezar" → `POST /api/session` → cookie UUID → redirige a `/onboarding`

### Pantalla 2 — Onboarding (`/onboarding`) — 3 pasos

**Paso 1 — CV**: upload PDF / Word (.docx/.doc) / TXT, drag & drop, máx 10 MB → `POST /api/cv` → extrae texto (pdfplumber para PDF, python-docx para Word, lectura directa para TXT)

**Paso 2 — Perfil** (10 preguntas con chips y campos):
1. Sectores (chips múltiple): Tecnología, Marketing, Consultoría, Banca y finanzas, Moda y lujo, Cosmética y belleza, Deporte, Educación, Salud, Entretenimiento, Otro
2. Modalidad (chip single): Solo presencial / Pref. presencial / Híbrido / Pref. remoto / Solo remoto
3. Ciudades (texto libre)
4. Salario mínimo bruto anual + moneda (EUR/USD/GBP)
5. Tipo empresa (chip single + **Otro con texto libre**): Startup, Pyme, Empresa mediana, Multinacional, Agencia, Consultora, Institución pública, Sin preferencia, Otro
6. Nivel responsabilidad (chip single): Prácticas o primer empleo, Junior, Media, Senior, Liderazgo
7. Prioridades (chips **sin límite** + **Otro con texto libre**): Salario, Flexibilidad, Remoto, Crecimiento, Equipo, Propósito, Estabilidad, Creatividad, Aprendizaje, Reconocimiento, Otro
8. Rechazos (chips múltiple + **Otro con texto libre**): Solo presencial sin flex, Salario bajo mínimo, Sin feedback, Viajes, Sin crecimiento, Sector no motivador, Otro
9. Momento carrera (chip single + **Otro con texto libre**): Primer empleo, Cambio sector, Crecimiento en sector, Vuelta al mercado, Cambio tras mucho tiempo, Otro
10. Notas adicionales (texto libre, opcional)
→ `POST /api/profile`

**Paso 3 — Oferta**: textarea grande, mínimo 100 chars → `POST /api/offer` → redirige a `/processing`

### Pantalla 3 — Procesamiento (`/processing`)
- **`<iframe>`** que carga el webview oficial de la extensión VS Code `pixel-agents` (React + Canvas pixel art)
- El webview corre en modo browser (detecta que `acquireVsCodeApi` no existe y usa fallback)
- `processing.js` es un **puente SSE↔postMessage**: no dibuja nada, solo traduce eventos del backend a mensajes al iframe
- Layout personalizado (`fitjob-layout.json`): sala única con 3 escritorios + PC + silla cada uno, zona break con sofá y mesa de café, decoraciones de pared y suelo
- 5 personajes: IDs 1-3 con nombre (Analizador, Redactor, Optimizador CV) + IDs 4-5 como ambiente sin nombre
- `alwaysShowLabels: true` → los nombres se muestran siempre sobre cada personaje
- Cuando un agente empieza: `agentToolStart` → personaje se mueve al escritorio y anima escribiendo
- Cuando un agente termina: `agentToolDone` + `agentToolsClear` → personaje vuelve a la zona de descanso
- 3 tarjetas bajo el iframe: nombre del agente + mensaje en tiempo real
- SSE: `GET /api/process/stream` controla todo en tiempo real
- Al completar: redirige a `/results?job_id=xxx`

### Pantalla 4 — Resultados (`/results?job_id=xxx`)
- Arco circular con score en color según umbral
- Justificación del score (3-4 líneas)
- Dos columnas: puntos fuertes (✓ azul) + gaps (⚠ amarillo)
- Preview expandible de la carta
- 3 botones descarga: CV Adaptado, Carta Completa, Carta Corta
- Campo email opcional → `POST /api/email`
- Botón "Analizar otra oferta" → vuelve al onboarding

### Pantalla 5 — Historial (`/history`)
- Botón "Mis ofertas" en navbar, visible tras ≥1 análisis
- Tarjetas ordenadas por score (mayor a menor)
- Badge con score + color + título + empresa + timestamp + "Ver informe" + "Descargar CV"
- Se pierde al cerrar el navegador (sin base de datos, por diseño)

---

## Variables de entorno (`.env`)

| Variable | Para qué | Obligatoria |
|----------|----------|-------------|
| `CLAUDE_BIN` | Ruta manual al claude.exe (solo si no se detecta auto) | No |
| `FITJOB_GMAIL_USER` | Gmail remitente para envío de docs | No |
| `FITJOB_GMAIL_PASSWORD` | App password de Google | No |

**No hay `ANTHROPIC_API_KEY`**. Claude se llama vía subprocess al binario local detectado automáticamente en `~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude.exe`.

---

## Arquitectura interna clave

### Cómo se llama a Claude
`services/claude_cli.py` → `call_claude(prompt, timeout)` → `subprocess.run([claude_bin, "-p", prompt])` → texto de respuesta

Exactamente igual que PACO. No hay SDK, no hay API key. Usa la sesión activa de Claude Code.

### Cómo funciona el SSE
`GET /api/process/stream` abre un generador async que:
1. Ejecuta `run_analizador()` en thread → emite `agent_start` y `agent_complete`
2. Ejecuta `run_redactor()` en thread → emite `agent_start` y `agent_complete`
3. Ejecuta `run_optimizador_cv()` en thread → emite `agent_start` y `agent_complete`
4. Genera PDFs de cartas → emite `process_complete`
5. Si cualquier paso falla → emite `agent_error` y para

### Cómo funciona la plantilla del CV
`services/pdf_generator.py` → `_render_cv_html(data: dict)` recibe el JSON del Agente 3 y genera HTML con el diseño del CV de Diego pero contenido dinámico (cualquier candidato). Playwright lo convierte a PDF.

El JSON tiene estas claves: `nombre`, `titular`, `contacto`, `info_personal`, `educacion[]`, `experiencia[]`, `idiomas`, `habilidades`, `voluntariado[]`, `adicional`. Todas opcionales excepto nombre.

### Sesiones
- Se crean en la landing con `POST /api/session` → UUID en cookie `fitjob_session`
- `SessionStore` es un dict en memoria: `{session_id: {cv_text, profile, offer_text, history[], results_xxx}}`
- PDFs en `tmp/<session_id>/`: `cv_original.<ext>` (con extensión original), `<job_id>_cv.pdf`, `<job_id>_carta.pdf`, `<job_id>_carta_corta.pdf`
- Nombre de descarga dinámico: `CV_<nombre>_<empresa>.pdf`, `Carta_Presentación_<empresa>.pdf`, `Carta_Corta_<empresa>.pdf`
- `results` almacena `cv_nombre` (nombre del candidato extraído del JSON del Agente 3) para construir los nombres

---

## Rutas FastAPI completas

| Método | Ruta | Qué hace |
|--------|------|----------|
| GET | `/` | Landing HTML |
| GET | `/onboarding` | Onboarding HTML |
| GET | `/processing` | Processing HTML |
| GET | `/results` | Results HTML |
| GET | `/history` | History HTML |
| POST | `/api/session` | Crea sesión → cookie UUID |
| POST | `/api/cv` | Recibe PDF → extrae texto → sesión |
| POST | `/api/profile` | Guarda las 10 respuestas del perfil |
| POST | `/api/offer` | Guarda texto de la oferta |
| GET | `/api/process/stream` | SSE: 3 agentes secuenciales |
| GET | `/api/results/{job_id}` | Devuelve resultados completos |
| GET | `/api/download/{type}/{job_id}` | Descarga PDF (`cv` / `carta` / `carta-corta`) |
| POST | `/api/email` | Envía los 3 docs al email del usuario |
| GET | `/api/history` | Lista resumida del historial de sesión |

---

## Puntos críticos a recordar

1. **Sesión obligatoria antes del onboarding**: el botón "Empezar" de la landing crea la sesión. Si el usuario va directo a `/onboarding` sin pasar por la landing, las llamadas a API fallarán con 401.

2. **Claude via subprocess**: los agentes son síncronos (bloquean el hilo). Se ejecutan con `asyncio.to_thread()` para no bloquear el event loop de FastAPI. Si se cambia esto, hay que mantener `to_thread`.

3. **Timeout de agentes**: Analizador 180s, Redactor 240s, Optimizador 300s. Si Claude tarda más (raro pero posible), el agente lanzará `subprocess.TimeoutExpired` que se captura en el SSE y emite `agent_error`.

4. **El CV siempre en inglés**: el Agente 3 genera el CV en inglés siempre. La carta va en el idioma de la oferta (Agente 2).

5. **Carta corta máx 550 chars**: el Redactor intenta respetarlo; el código trunca a 547+`…` si el modelo se pasa.

6. **Pantalla de procesamiento = iframe**: el webview oficial de la extensión pixel-agents está copiado en `static/pixel-agents-webview/`. `processing.js` solo envía mensajes `postMessage` al iframe. No hay canvas propio. Los sprites están también en `static/sprites/` como respaldo. Para ajustar la sala, editar `static/pixel-agents-webview/assets/fitjob-layout.json`.

7. **tmp/ no se limpia**: los PDFs generados se acumulan en `tmp/`. Para la demo no es problema. En producción habría que añadir cleanup periódico.

---

## Estado: FUNCIONAL END-TO-END ✅

Probado el 2026-06-14. Todo el flujo completo funciona:
- Subida de CV en PDF, Word (.docx/.doc) o TXT
- Perfil con 10 preguntas y chips
- 3 agentes secuenciales con animación Canvas pixel art y SSE real
- Animación: personajes caminan entre cafetería y escritorios según su estado (ROW_E espejado, z-sorting correcto)
- Resultados con score circular, puntos fuertes, gaps y carta
- Descarga de 3 PDFs con nombres dinámicos (nombre candidato + empresa)
- Email HTML con diseño Fitjob, puntos fuertes/gaps en el cuerpo, desde `fitjob.assistant@gmail.com`
- "Mis ofertas" visible en todas las pantallas (landing, onboarding, processing, results, history)

## Bugs corregidos y mejoras implementadas

### 2026-06-13
| Cambio | Descripción |
|--------|-------------|
| Upload multi-formato | Soporte para PDF, DOCX, DOC, TXT. `python-docx` añadido a requirements |
| Fix Playwright en Windows | `NotImplementedError` en asyncio → PDF generation movida a `services/_pdf_worker.py` (subproceso aislado) |
| Fix feedback email invisible | `style.display:none` inline sobreescribía CSS → `style.display='block'` explícito |
| Email HTML rediseñado | Puntos fuertes (✓ verde) + áreas de mejora (⚠ amarillo) en el cuerpo del email |
| Nombres de archivo dinámicos | `CV_<nombre>_<empresa>.pdf`, `Carta_Presentación_<empresa>.pdf`, `Carta_Corta_<empresa>.pdf` |
| Animación procesamiento | Canvas rediseñado: cafetería + sala de trabajo + personajes con movimiento entre zonas |
| Credenciales email | `fitjob.assistant@gmail.com` configurado en `.env` con app password de Google |

### 2026-06-14
| Cambio | Descripción |
|--------|-------------|
| Landing hero rediseñada | Foto `hero.jpg.webp` a sangre en mitad derecha + gradiente CSS + SVG mini centrado abajo |
| SVG mini reposicionado | Hijo directo de `<section.hero>`, centrado horizontalmente, `bottom:48px`, `width:360px` |
| Hint upload corregido | "Solo PDF" → "PDF, Word (.docx) o TXT · Máximo 10 MB" en onboarding paso 1 |
| "Mis ofertas" en todos los navbars | Añadido como `btn-ghost` a landing, onboarding, processing, results (siempre visible), history |
| Tiempo estimado procesamiento | "30 y 60 segundos" → "entre 1 y 3 minutos" (más realista con Claude CLI) |
| Fix `analizarOtra()` en historial | Redirigía a `/onboarding#step3` (hash inútil) → corregido a `/onboarding` |
| Subtitle historial suavizado | "El historial se pierde al cerrar el navegador" → "El historial está disponible durante esta sesión" |

### 2026-06-15
| Cambio | Descripción |
|--------|-------------|
| Onboarding: opción "Otro" con texto | Preguntas 1 (Sectores), 5 (Tipo empresa), 7 (Prioridades), 8 (Rechazos) y 9 (Momento carrera) tienen chip "Otro" que despliega input de texto. El texto sustituye a "Otro" antes de enviar al backend. |
| Onboarding: Prioridades sin límite | Eliminado el tope de 3 selecciones. Ahora se pueden elegir todas. |
| `onboarding.js` refactorizado | `initChipGroup()` acepta `otroInputId`. Nuevas funciones `getChipValuesWithOtro` y `getSingleChipValueWithOtro`. |
| Fix FRAME_H (sprites cortados) | `FRAME_H` 16→32. Los sprites de personajes son 16×32 por frame. |
| Fix ROW_E (invisible al caminar) | El spritesheet no tiene fila Este. Se espeja ROW_W con `ctx.scale(-1,1)`. |
| Halo activo: blob → anillo | Cambiado de círculo relleno a anillo fino pulsante. |
| Canvas: 340 → 480px | Escena más grande. |
| Sprites reales de muebles | Sustitución completa del dibujo programático por sprites del repo pixel-agents. |
| PC animado | Cicla entre `PC_FRONT_ON_1/2/3` cada 15 frames cuando el agente está activo. |
| Z-sorting correcto | Drawables ordenados por Y cada frame. `deskY=410 > charY=370` → efecto sentado. |
| Personajes de ambiente (4) | `char_3/4` en cafetería; `char_5/4` en sala de trabajo. |
| Sistema de burbujas idle | Timer aleatorio + fade in/out suave para personajes en reposo. |

### 2026-06-16
| Cambio | Descripción |
|--------|-------------|
| Extensión pixel-agents instalada | Diego instaló la extensión `pablodelucca.pixel-agents-1.3.0` en VS Code. Assets en `~/.vscode/extensions/pablodelucca.pixel-agents-1.3.0/dist/`. |
| Sprites copiados localmente | Todos los assets (chars 0–5, floors 0–8, 22+ muebles) copiados a `static/sprites/` para que la demo funcione sin internet. |
| Webview de extensión copiado | El bundle React completo de la extensión copiado a `static/pixel-agents-webview/`. Funciona en modo browser (sin VS Code). |
| Canvas reemplazado por iframe | `processing.html`: el `<canvas>` sustituido por `<iframe id="office-iframe" src="/static/pixel-agents-webview/index.html">`. |
| `processing.js` reescrito | Ya no dibuja nada. Es un puente SSE↔postMessage. Protocolo: `layoutLoaded` → `settingsLoaded` → `existingAgents` → `agentToolStart`/`agentToolDone`/`agentToolsClear` según eventos SSE. |
| Layout personalizado | `static/pixel-agents-webview/assets/fitjob-layout.json`: sala única 21×22, 3 DESK_FRONT+PC+silla, zona break (sofá, mesa café, sillas), decoraciones. |
| Agentes con nombre visible | `alwaysShowLabels: true`. IDs 1-3 tienen `folderName` = "Analizador"/"Redactor"/"Optimizador CV". IDs 4-5 son ambiente sin nombre. |

## Lo pendiente

- Verificar visualmente que el webview renderiza bien en el iframe (Diego lo está mirando).
- Si el webview muestra controles de edición de sala no deseados, se pueden ocultar con CSS en el iframe.

---

## Referencia PACO

Proyecto original en: `C:\Users\Asus\OneDrive\Documentos\Máster Evolve\Paco_agente_empleo\`

Equivalencias:
- `AGENTE_DANI` → `agents/analizador.py`
- `AGENTE_JAVI` → `agents/redactor.py` + `agents/optimizador_cv.py`
- `generar_cv_html()` → `services/pdf_generator.py::_render_cv_html()`
- `call_claude()` → `services/claude_cli.py::call_claude()`
