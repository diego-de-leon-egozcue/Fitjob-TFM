/* processing.js — Canvas office animation v3 */

// ── Canvas ─────────────────────────────────────────────────────────────────────
const canvas = document.getElementById('office-canvas');
const ctx    = canvas.getContext('2d');
const CW = 860, CH = 480;

// ── Scales ─────────────────────────────────────────────────────────────────────
const CS  = 3;   // character pixel scale
const FS  = 3;   // furniture pixel scale
const FSW = 2;   // wall-decoration scale (fits in back wall band)

// ── Room geometry ──────────────────────────────────────────────────────────────
const BACK_WALL_TOP = 30;
const WALL_Y        = 90;   // floor line
const WCY = Math.round((BACK_WALL_TOP + WALL_Y) / 2);  // ~60

// Derived furniture Y positions (FS = 3)
const DESK_TOP_Y   = WALL_Y;                                   // 90
const DESK_CY      = DESK_TOP_Y + (32 * FS) / 2;              // 138
const CHAIR_CY     = DESK_TOP_Y + 32 * FS + (32 * FS) / 2;   // 234
const DESK_Y       = DESK_TOP_Y + 32 * FS + 32 * FS + 20;    // 302  char feet at desk
const BREAK_Y      = 390;                                       // char feet at break area

// ── Sprite frames (characters) ─────────────────────────────────────────────────
const CFW = 16, CFH = 32, CFRAMES = 7;
const DIR_DOWN = 0, DIR_UP = 1, DIR_RIGHT = 2;
// DIR_LEFT = 3  (mirror of RIGHT)

// ── Furniture sprite catalog ───────────────────────────────────────────────────
const BASE_F = '/static/pixel-agents-webview/assets/';
const FURN = {
  DESK_FRONT:            { path: 'furniture/DESK/DESK_FRONT.png',                       w: 48, h: 32 },
  PC_FRONT_OFF:          { path: 'furniture/PC/PC_FRONT_OFF.png',                       w: 16, h: 32 },
  WOODEN_CHAIR_FRONT:    { path: 'furniture/WOODEN_CHAIR/WOODEN_CHAIR_FRONT.png',       w: 16, h: 32 },
  SOFA_FRONT:            { path: 'furniture/SOFA/SOFA_FRONT.png',                       w: 32, h: 16 },
  CUSHIONED_CHAIR_FRONT: { path: 'furniture/CUSHIONED_CHAIR/CUSHIONED_CHAIR_FRONT.png', w: 16, h: 16 },
  DOUBLE_BOOKSHELF:      { path: 'furniture/DOUBLE_BOOKSHELF/DOUBLE_BOOKSHELF.png',     w: 32, h: 32 },
  WHITEBOARD:            { path: 'furniture/WHITEBOARD/WHITEBOARD.png',                 w: 32, h: 32 },
  HANGING_PLANT:         { path: 'furniture/HANGING_PLANT/HANGING_PLANT.png',           w: 16, h: 32 },
  SMALL_PAINTING:        { path: 'furniture/SMALL_PAINTING/SMALL_PAINTING.png',         w: 16, h: 32 },
  PLANT:                 { path: 'furniture/PLANT/PLANT.png',                           w: 16, h: 32 },
  CACTUS:                { path: 'furniture/CACTUS/CACTUS.png',                         w: 16, h: 32 },
  BIN:                   { path: 'furniture/BIN/BIN.png',                               w: 16, h: 16 },
  COFFEE_TABLE:          { path: 'furniture/COFFEE_TABLE/COFFEE_TABLE.png',             w: 32, h: 32 },
};

const sprF = {};   // furniture images keyed by FURN key
const sprC = [];   // character images indexed by ci

// ── Agent config ───────────────────────────────────────────────────────────────
const AGENT_CFG = {
  1: { name: 'Analizador',     ci: 0, deskX: 179, breakX: 265,
       idleTexts: ['Revisando CV…', 'Analizando…', '☕', 'Preparado ✓', 'Comparando…'] },
  2: { name: 'Redactor',       ci: 1, deskX: 430, breakX: 430,
       idleTexts: ['Redactando…', 'Buscando palabras…', '☕', 'Preparado ✓', '💭 …'] },
  3: { name: 'Optimizador CV', ci: 2, deskX: 681, breakX: 595,
       idleTexts: ['Optimizando…', 'Revisando formato…', '☕', 'Listo ✓', '📋 …'] },
};
const AMBIENT_CFG = {
  4: { ci: 3, x: 110, y: 290 },
  5: { ci: 4, x: 750, y: 270 },
};

// ── Furniture collision zones ─────────────────────────────────────────────────
// Ambient characters won't wander into these areas
const FZ = [
  { x1: 100, y1: WALL_Y, x2: 260, y2: DESK_Y - 10 },  // desk 1 zone
  { x1: 350, y1: WALL_Y, x2: 510, y2: DESK_Y - 10 },  // desk 2 zone
  { x1: 600, y1: WALL_Y, x2: 760, y2: DESK_Y - 10 },  // desk 3 zone
  { x1: 295, y1: 325,   x2: 572, y2: 435 },            // sofa + coffee table
  { x1: 185, y1: 328,   x2: 262, y2: 415 },            // left cushioned chair
  { x1: 595, y1: 328,   x2: 678, y2: 415 },            // right cushioned chair
];
const inFZ = (x, y) => FZ.some(z => x >= z.x1 && x <= z.x2 && y >= z.y1 && y <= z.y2);

// ── Wander points for ambient chars ───────────────────────────────────────────
const WANDER = [
  { x:  62, y: 205 }, { x:  62, y: 310 }, { x:  62, y: 415 },
  { x: 798, y: 205 }, { x: 798, y: 310 }, { x: 798, y: 415 },
  { x: 308, y: 220 }, { x: 308, y: 340 }, { x: 308, y: 445 },
  { x: 552, y: 220 }, { x: 552, y: 340 }, { x: 552, y: 445 },
  { x: 430, y: 455 }, { x: 190, y: 455 }, { x: 670, y: 455 },
].filter(p => !inFZ(p.x, p.y));

// ── Character class ────────────────────────────────────────────────────────────
class Character {
  constructor(id, x, y, ci, name, idleTexts) {
    this.id         = id;
    this.x          = x;  this.y  = y;
    this.tx         = x;  this.ty = y;
    this.ci         = ci;
    this.name       = name;
    this.idleTexts  = idleTexts || ['☕', '…', '✓'];
    this.dir        = DIR_DOWN;
    this.frame      = 0;
    this.ft         = 0;
    this.active     = false;
    this.done       = false;
    this.status     = '';
    this.zTimer     = 0;
    this._cb        = null;
    // Idle bubble state
    this._idleT     = Math.random() * 3;   // offset so all agents don't sync
    this._idleNext  = 2 + Math.random() * 3;
    this._idleBubble = null;               // {text, t, alpha}
    // Break bubble state (coffee / zzz alternating)
    this._breakBubble = null;
    this._breakT    = 0;
    this._breakNext = 3 + Math.random() * 4;
  }

  walkTo(tx, ty, cb) { this.tx = tx; this.ty = ty; this._cb = cb || null; }

  update(dt) {
    const dx = this.tx - this.x, dy = this.ty - this.y;
    const dist = Math.hypot(dx, dy);
    const moving = dist > 1.5;

    if (moving) {
      const step = Math.min(80 * dt, dist);
      this.x += dx / dist * step;
      this.y += dy / dist * step;
      this.dir = Math.abs(dx) > Math.abs(dy)
        ? (dx > 0 ? DIR_RIGHT : 3)
        : (dy > 0 ? DIR_DOWN : DIR_UP);
      this.ft += dt;
      if (this.ft >= 0.1) { this.ft = 0; this.frame = (this.frame + 1) % CFRAMES; }
    } else {
      this.x = this.tx; this.y = this.ty;
      if (this._cb) { const cb = this._cb; this._cb = null; cb(); }
      if (this.active) {
        // Working: animate faster
        this.ft += dt;
        if (this.ft >= 0.15) { this.ft = 0; this.frame = (this.frame + 1) % CFRAMES; }
      } else {
        // Idle/done: subtle slow breathing animation
        this.ft += dt;
        if (this.ft >= 0.45) { this.ft = 0; this.frame = (this.frame + 1) % CFRAMES; }
      }
    }

    // ── Idle bubble (desk, not working yet) ──
    if (!this.active && !this.done && !moving && this.idleTexts.length) {
      this._idleT += dt;
      if (this._idleBubble) {
        this._idleBubble.t += dt;
        const SHOW = 1.8, FADE = 0.35;
        this._idleBubble.alpha =
          this._idleBubble.t < FADE ? this._idleBubble.t / FADE :
          this._idleBubble.t > SHOW - FADE ? Math.max(0, (SHOW - this._idleBubble.t) / FADE) : 1;
        if (this._idleBubble.t >= SHOW) {
          this._idleBubble = null;
          this._idleNext = this._idleT + 2.5 + Math.random() * 3.5;
        }
      } else if (this._idleT >= this._idleNext) {
        const txt = this.idleTexts[Math.floor(Math.random() * this.idleTexts.length)];
        this._idleBubble = { text: txt, t: 0, alpha: 0 };
      }
    } else if (this.active || moving) {
      this._idleBubble = null;
    }

    // ── Break bubble (at rest area, ZZZ or ☕) ──
    if (this.done && !moving) {
      this._breakT += dt;
      this.zTimer  += dt;
      if (this._breakBubble) {
        this._breakBubble.t += dt;
        const SHOW = 2.2, FADE = 0.4;
        this._breakBubble.alpha =
          this._breakBubble.t < FADE ? this._breakBubble.t / FADE :
          this._breakBubble.t > SHOW - FADE ? Math.max(0, (SHOW - this._breakBubble.t) / FADE) : 1;
        if (this._breakBubble.t >= SHOW) {
          this._breakBubble = null;
          this._breakNext = this._breakT + 1.5 + Math.random() * 2.5;
        }
      } else if (this._breakT >= this._breakNext) {
        // Alternate: ☕ or 💤
        const isEven = Math.floor(this._breakT / 4) % 2 === 0;
        this._breakBubble = { text: isEven ? '☕' : '💤 Descansando', t: 0, alpha: 0 };
      }
    } else if (!this.done) {
      this._breakBubble = null; this._breakT = 0;
    }
  }

  draw() {
    const sp = sprC[this.ci];
    if (!sp?.complete || !sp.naturalWidth) return;

    const drawDir = this.dir === 3 ? DIR_RIGHT : this.dir;
    const mirror  = this.dir === 3;
    const dw = CFW * CS, dh = CFH * CS;
    const sx = this.frame * CFW, sy = drawDir * CFH;

    // Active glow
    if (this.active) {
      ctx.save();
      ctx.shadowBlur = 26; ctx.shadowColor = '#3b82f6';
      ctx.globalAlpha = 0.38;
      ctx.fillStyle = '#3b82f6';
      ctx.beginPath(); ctx.ellipse(this.x, this.y - 5, 22, 11, 0, 0, Math.PI * 2);
      ctx.fill(); ctx.restore();
    }

    ctx.save();
    if (mirror) {
      ctx.translate(this.x, this.y - dh);
      ctx.scale(-1, 1);
      ctx.drawImage(sp, sx, sy, CFW, CFH, -dw / 2, 0, dw, dh);
    } else {
      ctx.drawImage(sp, sx, sy, CFW, CFH, this.x - dw / 2, this.y - dh, dw, dh);
    }
    ctx.restore();

    // Name tag
    if (this.name) {
      const tagY = this.y - dh - 6;
      const col = this.done   ? '#4ade80'
                : this.active ? '#60a5fa'
                :               'rgba(185,200,228,0.85)';
      ctx.font = 'bold 11px Inter,sans-serif';
      const tw = ctx.measureText(this.name).width;
      ctx.fillStyle = 'rgba(5,7,18,0.80)';
      ctx.beginPath(); ctx.roundRect(this.x - tw / 2 - 7, tagY - 14, tw + 14, 17, 5); ctx.fill();
      ctx.fillStyle = col;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(this.name, this.x, tagY - 6);
    }

    // ── Bubble / ZZZ ──
    if (this.active && this.status) {
      // Working: speech bubble with task text
      drawBubble(this.x, this.y - dh - 22, this.status, '#3b82f6');
    } else if (this.done) {
      // Resting: ZZZ animation
      drawZzz(this.x, this.y - dh - 8, this.zTimer);
      // Break bubble (☕ / 💤) overlaid
      if (this._breakBubble) {
        drawIdleBubble(this.x + 24, this.y - dh - 16, this._breakBubble.text, this._breakBubble.alpha, '#4ade80');
      }
    } else if (this._idleBubble) {
      // Idle at desk: thought bubble
      drawIdleBubble(this.x + 20, this.y - dh - 14, this._idleBubble.text, this._idleBubble.alpha, 'rgba(160,180,220,0.9)');
    }

    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  }
}

// ── Speech bubble ──────────────────────────────────────────────────────────────
function drawBubble(cx, topY, text, borderCol) {
  ctx.font = '10px Inter,sans-serif';
  const maxW = 148, pad = 6, lh = 13;
  const words = text.split(' ');
  const lines = ['']; let li = 0;
  for (const w of words) {
    const test = (lines[li] ? lines[li] + ' ' : '') + w;
    if (ctx.measureText(test).width > maxW) { li++; lines.push(w); } else lines[li] = test;
  }
  const bw = Math.min(maxW + pad * 2, Math.max(...lines.map(l => ctx.measureText(l).width)) + pad * 2 + 10);
  const bh = lines.length * lh + pad * 2;
  const bx = cx - bw / 2, by = topY - bh;

  ctx.fillStyle = 'rgba(6,9,22,0.92)'; ctx.strokeStyle = borderCol; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 6); ctx.fill(); ctx.stroke();

  ctx.fillStyle = 'rgba(6,9,22,0.92)'; ctx.strokeStyle = borderCol; ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(cx - 5, by + bh); ctx.lineTo(cx + 5, by + bh); ctx.lineTo(cx, by + bh + 8);
  ctx.closePath(); ctx.fill(); ctx.stroke();

  ctx.fillStyle = 'rgba(185,215,255,0.92)'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  for (let i = 0; i < lines.length; i++) ctx.fillText(lines[i], cx, by + pad + i * lh);
}

// ── ZZZ bubble ─────────────────────────────────────────────────────────────────
function drawZzz(x, y, timer) {
  const ls = ['z', 'z', 'Z'];
  for (let i = 0; i < 3; i++) {
    const ph = ((timer * 0.5 + i * 0.33) % 1.0);
    const yOff = -ph * 38;
    const alpha = ph < 0.75 ? 0.88 - ph * 0.3 : (1 - ph) / 0.25 * 0.88;
    ctx.save();
    ctx.globalAlpha = Math.max(0, alpha);
    ctx.fillStyle = '#8888cc';
    ctx.font = `bold ${9 + i * 3}px Inter,sans-serif`;
    ctx.fillText(ls[i], x + 14 + i * 9, y + yOff);
    ctx.restore();
  }
}

// ── Idle / break bubble (small rounded, semi-transparent) ─────────────────────
function drawIdleBubble(x, y, text, alpha, col) {
  if (alpha <= 0) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.font = '11px Inter,sans-serif';
  const tw = ctx.measureText(text).width;
  const pad = 5, bw = tw + pad * 2 + 4, bh = 18;
  ctx.fillStyle   = 'rgba(6,9,22,0.82)';
  ctx.strokeStyle = col || 'rgba(160,180,220,0.8)';
  ctx.lineWidth   = 1.2;
  ctx.beginPath(); ctx.roundRect(x, y - bh, bw, bh, 6); ctx.fill(); ctx.stroke();
  // Small tail dot
  ctx.fillStyle = col || 'rgba(160,180,220,0.8)';
  ctx.beginPath(); ctx.arc(x + 4, y + 2, 2.5, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(x - 2, y + 6, 1.8, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(210,225,255,0.92)';
  ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  ctx.fillText(text, x + pad, y - bh / 2);
  ctx.restore();
}

// ── Furniture draw helper ──────────────────────────────────────────────────────
function dF(key, cx, cy, scale) {
  const f = FURN[key], img = sprF[key];
  if (!f || !img?.complete || !img.naturalWidth) return;
  const s = scale !== undefined ? scale : FS;
  ctx.drawImage(img, cx - f.w * s / 2, cy - f.h * s / 2, f.w * s, f.h * s);
}

// ── Room ───────────────────────────────────────────────────────────────────────
function drawRoom() {
  ctx.fillStyle = '#0b0d18'; ctx.fillRect(0, 0, CW, CH);
  // Side walls
  ctx.fillStyle = '#0e1220';
  ctx.fillRect(0, WALL_Y, 32, CH);
  ctx.fillRect(828, WALL_Y, 32, CH);
  // Floor
  ctx.fillStyle = '#18274a'; ctx.fillRect(32, WALL_Y, 796, CH - WALL_Y);
  // Floor grid
  ctx.strokeStyle = 'rgba(255,255,255,0.022)'; ctx.lineWidth = 1;
  for (let x = 32; x < 828; x += 32) { ctx.beginPath(); ctx.moveTo(x, WALL_Y); ctx.lineTo(x, CH); ctx.stroke(); }
  for (let y = WALL_Y; y < CH; y += 32)  { ctx.beginPath(); ctx.moveTo(32, y); ctx.lineTo(828, y); ctx.stroke(); }
  // Back wall band
  ctx.fillStyle = '#101c36'; ctx.fillRect(32, BACK_WALL_TOP, 796, WALL_Y - BACK_WALL_TOP);
  // Wall-floor divider
  ctx.fillStyle = '#1e3560'; ctx.fillRect(32, WALL_Y - 2, 796, 4);
}

// ── Scene (furniture) ─────────────────────────────────────────────────────────
function drawScene() {
  // ── Back wall decorations (FSW=2 so they fit in the wall band) ──
  dF('DOUBLE_BOOKSHELF',  75, WCY, FSW);
  dF('DOUBLE_BOOKSHELF', 785, WCY, FSW);
  dF('WHITEBOARD',       288, WCY, FSW);
  dF('HANGING_PLANT',    490, WCY + 4, FSW);
  dF('HANGING_PLANT',    560, WCY + 4, FSW);
  dF('SMALL_PAINTING',   390, WCY, FSW);

  // ── Desks, PCs, chairs for each agent ──
  for (const cfg of Object.values(AGENT_CFG)) {
    const x = cfg.deskX;
    dF('DESK_FRONT',         x,      DESK_CY);           // desk (FS=3)
    dF('PC_FRONT_OFF',       x + 10, DESK_CY - 20);     // PC slightly right + up on desk
    dF('WOODEN_CHAIR_FRONT', x,      CHAIR_CY);          // chair below desk
  }

  // ── Break area ──
  dF('SOFA_FRONT',            430, 356);
  dF('CUSHIONED_CHAIR_FRONT', 230, 362);
  dF('CUSHIONED_CHAIR_FRONT', 640, 362);
  dF('COFFEE_TABLE',          430, 420, 2);   // coffee table smaller scale

  // ── Floor decorations ──
  dF('PLANT',  55,  305);
  dF('CACTUS', 810, 295);
  dF('BIN',    810, 455, 2);
}

// ── Characters ─────────────────────────────────────────────────────────────────
const chars = {};

function initChars() {
  for (const [k, cfg] of Object.entries(AGENT_CFG)) {
    const c = new Character(+k, cfg.deskX, DESK_Y, cfg.ci, cfg.name, cfg.idleTexts);
    c.dir = DIR_UP;
    chars[+k] = c;
  }
  for (const [k, cfg] of Object.entries(AMBIENT_CFG)) {
    const ambientTexts = ['☕', '💬 …', '😊', '…', '☕ Café'];
    const c = new Character(+k, cfg.x, cfg.y, cfg.ci, '', ambientTexts);
    chars[+k] = c;
    scheduleWander(c);
  }
}

function scheduleWander(c) {
  const delay = 900 + Math.random() * 2100;
  setTimeout(() => {
    const reachable = WANDER.filter(p => Math.hypot(p.x - c.x, p.y - c.y) > 85);
    if (!reachable.length) { scheduleWander(c); return; }
    const pt = reachable[Math.floor(Math.random() * reachable.length)];
    c.walkTo(pt.x, pt.y, () => { c.dir = DIR_DOWN; scheduleWander(c); });
  }, delay);
}

// ── Game loop ──────────────────────────────────────────────────────────────────
let lastT = 0;
function loop(t) {
  const dt = Math.min((t - lastT) / 1000, 0.05);
  lastT = t;
  drawRoom();
  drawScene();
  const sorted = Object.values(chars).sort((a, b) => a.y - b.y);
  for (const c of sorted) { c.update(dt); c.draw(); }
  requestAnimationFrame(loop);
}

// ── Agent state ────────────────────────────────────────────────────────────────
const agentMsg = { 1: 'En espera…', 2: 'En espera…', 3: 'En espera…' };

function agentActive(id, toolName) {
  const c = chars[id], cfg = AGENT_CFG[id];
  if (!c || !cfg) return;
  c.active = true; c.done = false;
  c.status = (toolName || 'Trabajando…').slice(0, 32);
  c.walkTo(cfg.deskX, DESK_Y, () => { c.dir = DIR_UP; });
}

function agentDone(id) {
  const c = chars[id], cfg = AGENT_CFG[id];
  if (!c || !cfg) return;
  c.active = false; c.done = true; c.status = '';
  setTimeout(() => c.walkTo(cfg.breakX, BREAK_Y, () => { c.dir = DIR_DOWN; }), 500);
}

function agentError(id) {
  const c = chars[id]; if (!c) return;
  c.active = false; c.done = false; c.status = '';
}

// ── UI panels ─────────────────────────────────────────────────────────────────
function updateAgentUI(i, state, msg) {
  if (msg) agentMsg[i] = msg;
  const info = document.getElementById(`agent-${i}-info`);
  const stat = document.getElementById(`agent-${i}-status`);
  if (!info || !stat) return;
  info.className  = `agent-info ${state === 'idle' ? '' : state}`;
  stat.textContent = agentMsg[i];
}

// ── SSE ────────────────────────────────────────────────────────────────────────
function conectarSSE() {
  const es = new EventSource('/api/process/stream');

  es.addEventListener('agent_start', e => {
    const { agent, message } = JSON.parse(e.data);
    updateAgentUI(agent, 'active', message);
    agentActive(agent, message || 'Trabajando…');
  });

  es.addEventListener('agent_complete', e => {
    const { agent } = JSON.parse(e.data);
    updateAgentUI(agent, 'done', '¡Listo!');
    agentDone(agent);
  });

  es.addEventListener('agent_error', e => {
    const { agent, message } = JSON.parse(e.data);
    updateAgentUI(agent, 'error', message);
    agentError(agent);
    es.close();
    mostrarError(agent, message);
  });

  es.addEventListener('error_fatal', e => {
    const { message } = JSON.parse(e.data);
    es.close();
    mostrarError(null, message);
  });

  es.addEventListener('process_complete', e => {
    const { job_id } = JSON.parse(e.data);
    es.close();
    setTimeout(() => { window.location.href = `/results?job_id=${job_id}`; }, 1200);
  });

  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) return;
    es.close();
    mostrarError(null, 'Se perdió la conexión con el servidor.');
  };
}

// ── Error panel ────────────────────────────────────────────────────────────────
function mostrarError(agentIndex, mensaje) {
  const panel   = document.getElementById('error-panel');
  const titleEl = document.getElementById('error-panel-title');
  const msgEl   = document.getElementById('error-panel-msg');
  const names   = ['Analizador', 'Redactor', 'Optimizador CV'];
  titleEl.textContent = agentIndex ? `Error en el ${names[agentIndex - 1]}` : 'Ha ocurrido un error';
  msgEl.textContent   = mensaje || 'Error desconocido. Vuelve atrás e inténtalo de nuevo.';
  panel.classList.add('visible');
}

function reintentar() { window.location.href = '/processing'; }

// ── Boot ───────────────────────────────────────────────────────────────────────
(async function boot() {
  const all = [];
  // Character sprites
  for (let i = 0; i < 5; i++) {
    const img = new Image();
    const p   = new Promise(res => { img.onload = res; img.onerror = res; });
    img.src   = `/static/sprites/characters/char_${i}.png`;
    sprC.push(img); all.push(p);
  }
  // Furniture sprites
  for (const [key, f] of Object.entries(FURN)) {
    const img = new Image();
    const p   = new Promise(res => { img.onload = res; img.onerror = res; });
    img.src   = BASE_F + f.path;
    sprF[key] = img; all.push(p);
  }
  await Promise.all(all);
  initChars();
  requestAnimationFrame(loop);
})();

conectarSSE();
