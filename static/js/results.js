/* results.js — Pantalla de resultados */

let jobId = null;
let resultData = null;
let cartaExpandida = false;

// ── Inicialización ────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  jobId = new URLSearchParams(window.location.search).get('job_id');
  if (!jobId) {
    window.location.href = '/';
    return;
  }

  try {
    const res = await fetch(`/api/results/${jobId}`);
    if (!res.ok) throw new Error('Resultados no encontrados.');
    resultData = await res.json();
    renderResultados(resultData);
  } catch (err) {
    document.getElementById('loading-state').innerHTML = `
      <div style="text-align:center;padding:40px">
        <div style="font-size:2rem;margin-bottom:16px">⚠️</div>
        <p style="color:#EF4444;font-weight:600;margin-bottom:8px">No se pudieron cargar los resultados</p>
        <p style="color:rgba(255,255,255,0.4);font-size:0.875rem;margin-bottom:24px">${err.message}</p>
        <button class="btn-primary" onclick="window.location.href='/'">Volver al inicio</button>
      </div>`;
  }
});

// ── Render principal ──────────────────────────────────────────────────────────

function renderResultados(data) {
  // Título de la oferta
  document.getElementById('job-title').textContent    = data.offer_title   || 'Análisis de oferta';
  document.getElementById('job-company').textContent  = data.offer_company || '';

  // Score circular
  const score = data.score || 0;
  animarScore(score);

  // Justificación
  document.getElementById('score-justificacion').textContent = data.justificacion || '';

  // Puntos fuertes
  renderLista('strengths-list', data.puntos_fuertes || [], 'strength');

  // Gaps
  renderLista('gaps-list', data.gaps || [], 'gap');

  // Carta de presentación
  const cartaEl = document.getElementById('carta-text');
  if (data.carta) {
    cartaEl.innerHTML = data.carta
      .split('\n')
      .map(p => p.trim() ? `<p style="margin-bottom:12px">${esc(p)}</p>` : '')
      .join('');
  } else {
    document.querySelector('.carta-card').style.display = 'none';
  }

  // Botones de descarga
  configurarDescargas(jobId);

  // Ocultar loading, mostrar resultados
  document.getElementById('loading-state').style.display = 'none';
  document.getElementById('results-main').style.display  = 'block';
}

// ── Arco circular animado ─────────────────────────────────────────────────────

function animarScore(score) {
  const r          = 68;
  const circumference = 2 * Math.PI * r; // 427.26
  const arc        = document.getElementById('score-arc');
  const numberEl   = document.getElementById('score-number');

  // Color según umbral
  const color = score >= 70 ? '#3B82F6' : score >= 40 ? '#F59E0B' : '#EF4444';
  arc.style.stroke = color;
  numberEl.style.color = color;

  // Animar desde 0 hasta el score en 1.2s
  const offset = circumference - (score / 100) * circumference;

  // Forzar estado inicial
  arc.style.strokeDashoffset = circumference;

  // Pequeño delay para que la transición CSS se active
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      arc.style.strokeDashoffset = offset;
    });
  });

  // Animar número contando de 0 a score
  let current = 0;
  const step  = score / 60; // 60 frames ≈ 1s
  const timer = setInterval(() => {
    current = Math.min(current + step, score);
    numberEl.textContent = Math.round(current) + '%';
    if (current >= score) clearInterval(timer);
  }, 16);
}

// ── Listas de puntos fuertes y gaps ──────────────────────────────────────────

function renderLista(containerId, items, tipo) {
  const ul = document.getElementById(containerId);
  if (!ul) return;

  if (items.length === 0) {
    ul.innerHTML = '<li><span class="icon">—</span><span style="color:rgba(255,255,255,0.3)">Sin datos</span></li>';
    return;
  }

  ul.innerHTML = items.map(item => {
    if (tipo === 'strength') {
      return `<li>
        <span class="icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        </span>
        <span>${esc(item)}</span>
      </li>`;
    } else {
      return `<li>
        <span class="icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>
        </span>
        <span>${esc(item)}</span>
      </li>`;
    }
  }).join('');
}

// ── Carta expandible ──────────────────────────────────────────────────────────

function toggleCarta() {
  cartaExpandida = !cartaExpandida;
  const preview = document.getElementById('carta-preview');
  const fade    = document.getElementById('carta-fade');
  const btn     = document.getElementById('carta-expand-btn');

  if (cartaExpandida) {
    preview.classList.add('expanded');
    if (fade) fade.style.display = 'none';
    btn.textContent = 'Ver menos ↑';
  } else {
    preview.classList.remove('expanded');
    if (fade) fade.style.display = 'block';
    btn.textContent = 'Ver carta completa ↓';
  }
}

// ── Descargas ─────────────────────────────────────────────────────────────────

function configurarDescargas(jobId) {
  const tipos = [
    { id: 'dl-cv',          type: 'cv',          filename: 'CV_Adaptado_Fitjob.pdf' },
    { id: 'dl-carta',       type: 'carta',       filename: 'Carta_Presentacion.pdf' },
    { id: 'dl-carta-corta', type: 'carta-corta', filename: 'Carta_Corta.pdf'        },
  ];

  tipos.forEach(({ id, type, filename }) => {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.href     = `/api/download/${type}/${jobId}`;
    btn.download = filename;
    btn.addEventListener('click', e => {
      // Feedback visual breve
      const originalText = btn.querySelector('.download-btn-label').innerHTML;
      btn.querySelector('.download-btn-label').innerHTML = '⏳ Generando…';
      setTimeout(() => {
        btn.querySelector('.download-btn-label').innerHTML = originalText;
      }, 2000);
    });
  });
}

// ── Email ─────────────────────────────────────────────────────────────────────

async function enviarEmail() {
  const emailEl    = document.getElementById('email-input');
  const feedbackEl = document.getElementById('email-feedback');
  const email      = emailEl.value.trim();

  // Ocultar feedback previo
  feedbackEl.style.display = 'none';
  feedbackEl.className = 'email-feedback';

  if (!email || !email.includes('@')) {
    feedbackEl.textContent   = 'Introduce un email válido.';
    feedbackEl.className     = 'email-feedback err';
    feedbackEl.style.display = 'block';
    return;
  }

  const btn = document.querySelector('.email-card .btn-primary');
  btn.disabled = true;
  btn.textContent = 'Enviando…';

  try {
    const res = await fetch('/api/email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, job_id: jobId }),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Error al enviar el email.');

    feedbackEl.textContent   = `✓ Email enviado a ${email}`;
    feedbackEl.className     = 'email-feedback ok';
    feedbackEl.style.display = 'block';
    emailEl.value            = '';
  } catch (err) {
    feedbackEl.textContent   = `Error: ${err.message}`;
    feedbackEl.className     = 'email-feedback err';
    feedbackEl.style.display = 'block';
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Enviar';
  }
}

// ── Analizar otra oferta ──────────────────────────────────────────────────────

function analizarOtra() {
  // Vuelve al onboarding en el paso 3 (ya tiene CV y perfil)
  window.location.href = '/onboarding';
}

// ── Utilidades ────────────────────────────────────────────────────────────────

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
