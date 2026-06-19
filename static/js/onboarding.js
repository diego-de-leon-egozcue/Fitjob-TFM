/* onboarding.js — Lógica completa del onboarding (3 pasos) */

let cvSubido = false;

// ── Inicialización ────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initChips();
  initUploadDragDrop();
  initOfertaCounter();
});

// ── Navegación entre pasos ────────────────────────────────────────────────────

function mostrarPaso(n) {
  [1, 2, 3].forEach(i => {
    document.getElementById(`step-${i}`).style.display = i === n ? 'flex' : 'none';
    const navStep = document.getElementById(`nav-step-${i}`);
    navStep.classList.remove('active', 'done');
    if (i === n) navStep.classList.add('active');
    if (i < n)  navStep.classList.add('done');
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function irPaso1() { mostrarPaso(1); }
function irPaso2() { mostrarPaso(2); }

// ── Paso 1: subida de CV ──────────────────────────────────────────────────────

function initUploadDragDrop() {
  const area = document.getElementById('upload-area');
  if (!area) return;

  area.addEventListener('dragover', e => {
    e.preventDefault();
    area.classList.add('dragover');
  });
  area.addEventListener('dragleave', () => area.classList.remove('dragover'));
  area.addEventListener('drop', e => {
    e.preventDefault();
    area.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) procesarArchivo(file);
  });
}

function handleFileSelect(input) {
  if (input.files[0]) procesarArchivo(input.files[0]);
}

async function procesarArchivo(file) {
  ocultarError('upload-error');

  const ext = file.name.toLowerCase().split('.').pop();
  if (!['pdf', 'docx', 'doc', 'txt'].includes(ext)) {
    mostrarError('upload-error', 'Formato no soportado. Sube tu CV en PDF, Word (.docx) o texto (.txt).');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    mostrarError('upload-error', 'El archivo no puede superar los 10 MB.');
    return;
  }

  document.getElementById('upload-area').style.opacity = '0.5';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/cv', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Error al subir el CV.');
    }

    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('upload-filename').textContent = file.name;
    document.getElementById('upload-success').style.display = 'flex';

    cvSubido = true;
    document.getElementById('btn-step1').disabled = false;

  } catch (err) {
    document.getElementById('upload-area').style.opacity = '1';
    mostrarError('upload-error', err.message);
  }
}

function resetUpload() {
  cvSubido = false;
  document.getElementById('upload-area').style.display = 'block';
  document.getElementById('upload-area').style.opacity = '1';
  document.getElementById('upload-success').style.display = 'none';
  document.getElementById('btn-step1').disabled = true;
  document.getElementById('cv-input').value = '';
  ocultarError('upload-error');
}

// ── Paso 2: perfil ────────────────────────────────────────────────────────────

function initChips() {
  initChipGroup('chips-modalidad',    false, null, null);
  initChipGroup('chips-tipo-empresa', true,  null, 'otro-tipo-empresa');
  initChipGroup('chips-nivel',        false, null, null);
  initChipGroup('chips-momento',      false, null, 'otro-momento');
  initChipGroup('chips-sectores',     true,  null, 'otro-sectores');
  initChipGroup('chips-rechazos',     true,  null, 'otro-rechazos');
  initChipGroup('chips-prioridades',  true,  null, 'otro-prioridades');
}

function initChipGroup(groupId, multi, max, otroInputId) {
  const group = document.getElementById(groupId);
  if (!group) return;

  group.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const isSelected = chip.classList.contains('selected');

      if (!multi) {
        group.querySelectorAll('.chip').forEach(c => c.classList.remove('selected'));
        chip.classList.add('selected');
      } else {
        if (isSelected) {
          chip.classList.remove('selected');
        } else {
          if (max) {
            const selected = group.querySelectorAll('.chip.selected').length;
            if (selected >= max) return;
          }
          chip.classList.add('selected');
        }
      }

      // Mostrar/ocultar campo "Otro" según si el chip Otro está seleccionado
      if (otroInputId) {
        const otroInput = document.getElementById(otroInputId);
        const otroChip  = group.querySelector('.chip[data-value="Otro"]');
        if (otroInput && otroChip) {
          const visible = otroChip.classList.contains('selected');
          otroInput.style.display = visible ? 'block' : 'none';
          if (!visible) otroInput.value = '';
        }
      }
    });
  });
}

function getChipValues(groupId) {
  const group = document.getElementById(groupId);
  if (!group) return [];
  return [...group.querySelectorAll('.chip.selected')].map(c => c.dataset.value);
}

function getSingleChipValue(groupId) {
  return getChipValues(groupId)[0] || '';
}

// Si el chip "Otro" está seleccionado y hay texto, sustituye "Otro" por ese texto
function getChipValuesWithOtro(groupId, otroInputId) {
  const values = getChipValues(groupId);
  if (!otroInputId) return values;
  const otroInput  = document.getElementById(otroInputId);
  const customText = otroInput ? otroInput.value.trim() : '';
  return values.map(v => (v === 'Otro' && customText) ? customText : v);
}

function getSingleChipValueWithOtro(groupId, otroInputId) {
  return getChipValuesWithOtro(groupId, otroInputId)[0] || '';
}

async function irPaso3() {
  ocultarError('profile-error');

  const sectores  = getChipValuesWithOtro('chips-sectores', 'otro-sectores');
  const modalidad = getSingleChipValue('chips-modalidad');
  const nivel     = getSingleChipValue('chips-nivel');
  const momento   = getSingleChipValueWithOtro('chips-momento', 'otro-momento');

  if (sectores.length === 0) {
    mostrarError('profile-error', 'Selecciona al menos un sector de interés.');
    document.getElementById('chips-sectores').scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  if (!modalidad) {
    mostrarError('profile-error', 'Selecciona la modalidad de trabajo que buscas.');
    return;
  }
  if (!nivel) {
    mostrarError('profile-error', 'Selecciona el nivel de responsabilidad que buscas.');
    return;
  }
  if (!momento) {
    mostrarError('profile-error', 'Selecciona en qué momento de tu carrera estás.');
    return;
  }

  const salarioVal = parseInt(document.getElementById('input-salario').value) || 0;

  const payload = {
    sectores,
    modalidad,
    ciudades:              document.getElementById('input-ciudades').value.trim(),
    salario_min:           salarioVal,
    moneda:                document.getElementById('select-moneda').value,
    tipo_empresa:          getChipValuesWithOtro('chips-tipo-empresa', 'otro-tipo-empresa'),
    nivel_responsabilidad: nivel,
    prioridades:           getChipValuesWithOtro('chips-prioridades', 'otro-prioridades'),
    rechazos:              getChipValuesWithOtro('chips-rechazos', 'otro-rechazos'),
    momento_carrera:       momento,
    notas_adicionales:     document.getElementById('input-notas').value.trim(),
  };

  try {
    const res = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Error al guardar el perfil.');
    }
    mostrarPaso(3);
  } catch (err) {
    mostrarError('profile-error', err.message);
  }
}

// ── Paso 3: oferta ────────────────────────────────────────────────────────────

function initOfertaCounter() {
  const textarea = document.getElementById('input-oferta');
  const counter  = document.getElementById('offer-chars');
  if (!textarea || !counter) return;

  textarea.addEventListener('input', () => {
    const n = textarea.value.length;
    counter.textContent = `${n} caracteres`;
    counter.style.color = n >= 100 ? 'rgba(255,255,255,0.5)' : '#EF4444';
  });
}

async function analizarOferta() {
  ocultarError('offer-error');

  const texto = document.getElementById('input-oferta').value.trim();
  if (texto.length < 100) {
    mostrarError('offer-error', 'El texto de la oferta es demasiado corto. Pega el contenido completo de la oferta.');
    return;
  }

  const btn = document.querySelector('#step-3 .btn-primary');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px"></span> Enviando…';

  try {
    const limiteLarga = parseInt(document.getElementById('limite-carta-larga').value) || 0;
    const limiteCorta = parseInt(document.getElementById('limite-carta-corta').value) || 0;

    const res = await fetch('/api/offer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto, limite_carta_larga: limiteLarga, limite_carta_corta: limiteCorta }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || 'Error al guardar la oferta.');
    }
    window.location.href = '/processing';
  } catch (err) {
    btn.disabled = false;
    btn.innerHTML = 'Analizar oferta <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    mostrarError('offer-error', err.message);
  }
}

// ── Utilidades ────────────────────────────────────────────────────────────────

function mostrarError(id, mensaje) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = mensaje;
  el.style.display = 'block';
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function ocultarError(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = 'none';
}
