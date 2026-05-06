// Q4 ↔ Q9 FEM educational animation
// Loops: Q4 -> mid-nodes appear -> centroid -> edges curve into Q9 -> back to Q4

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "estilo": "tecnico",
  "curvatura": 10,
  "ritmo": 1.0
} /*EDITMODE-END*/;

// Style presets — full palette + treatment swap
const STYLE_PRESETS = {
  tecnico: {
    bg: '#222233', panel: '#2b2b3c',
    edge: '#4fa3ff', edgeLight: '#7fc0ff',
    corner: '#4fc3f7', mid: '#6fb8ff', centroid: '#b86fff',
    text: '#dfdfdf', grid: '#404055', glow: '#ffeb3b',
    panelStroke: '#3a3a55',
    edgeWidth: 2.5, gridOp: 0.5, panelOp: 1,
    cornerR: 7, midR: 5.5, glowOp: 0.18,
    edgeFilter: 'drop-shadow(0 0 3px rgba(79,163,255,0.45))'
  },
  holografico: {
    bg: '#070815', panel: '#0c0d22',
    edge: '#00e5ff', edgeLight: '#a371ff',
    corner: '#00e5ff', mid: '#5ce1ff', centroid: '#ff4fdf',
    text: '#e8f0ff', grid: '#1c2046', glow: '#fff55a',
    panelStroke: '#1f235a',
    edgeWidth: 2, gridOp: 0.6, panelOp: 1,
    cornerR: 7.5, midR: 6, glowOp: 0.32,
    edgeFilter: 'drop-shadow(0 0 6px rgba(0,229,255,0.85)) drop-shadow(0 0 14px rgba(163,113,255,0.4))'
  },
  pizarra: {
    bg: '#1c2520', panel: '#243029',
    edge: '#f4ead0', edgeLight: '#fff8dc',
    corner: '#fff1b8', mid: '#e8c887', centroid: '#ff9f7a',
    text: '#f0e8c8', grid: '#3a4a3e', glow: '#fff1b8',
    panelStroke: '#3a4a3e',
    edgeWidth: 3.5, gridOp: 0.35, panelOp: 1,
    cornerR: 7, midR: 5.5, glowOp: 0.10,
    edgeFilter: 'none'
  }
};

// ── Geometry (physical coords) ──────────────────────────────────────────────
const PHYS = {
  N1: [0.40, 0.50],
  N2: [3.20, 0.20],
  N3: [3.80, 2.60],
  N4: [0.10, 2.10]
};
PHYS.N5 = [(PHYS.N1[0] + PHYS.N2[0]) / 2, (PHYS.N1[1] + PHYS.N2[1]) / 2];
PHYS.N6 = [(PHYS.N2[0] + PHYS.N3[0]) / 2, (PHYS.N2[1] + PHYS.N3[1]) / 2];
PHYS.N7 = [(PHYS.N3[0] + PHYS.N4[0]) / 2, (PHYS.N3[1] + PHYS.N4[1]) / 2];
PHYS.N8 = [(PHYS.N4[0] + PHYS.N1[0]) / 2, (PHYS.N4[1] + PHYS.N1[1]) / 2];
PHYS.N9 = [
(PHYS.N1[0] + PHYS.N2[0] + PHYS.N3[0] + PHYS.N4[0]) / 4,
(PHYS.N1[1] + PHYS.N2[1] + PHYS.N3[1] + PHYS.N4[1]) / 4];


// Map physical coords to canvas coords (1200x800). Center the element with margin.
const CANVAS_W = 1200,CANVAS_H = 800;
const PAD_X = 80,PAD_TOP = 100,PAD_BOT = 90;

// Find phys bounds with a small inset margin so curved edges don't get clipped
const PX_MIN = 0,PX_MAX = 4.0;
const PY_MIN = 0,PY_MAX = 2.9;

function toCanvas([x, y]) {
  const sx = (CANVAS_W - 2 * PAD_X) / (PX_MAX - PX_MIN);
  const sy = (CANVAS_H - PAD_TOP - PAD_BOT) / (PY_MAX - PY_MIN);
  const s = Math.min(sx, sy);
  // center the scaled phys box in the available area
  const usedW = (PX_MAX - PX_MIN) * s;
  const usedH = (PY_MAX - PY_MIN) * s;
  const offsetX = PAD_X + (CANVAS_W - 2 * PAD_X - usedW) / 2;
  const offsetY = PAD_TOP + (CANVAS_H - PAD_TOP - PAD_BOT - usedH) / 2;
  // y-flip: phys y up, canvas y down
  return [
  offsetX + (x - PX_MIN) * s,
  offsetY + (PY_MAX - y) * s];

}

// Pre-compute canvas coordinates
const C = {};
for (const k of Object.keys(PHYS)) C[k] = toCanvas(PHYS[k]);

// Edges as ordered pairs of corner labels
const EDGES = [
{ a: 'N1', b: 'N2', mid: 'N5' },
{ a: 'N2', b: 'N3', mid: 'N6' },
{ a: 'N3', b: 'N4', mid: 'N7' },
{ a: 'N4', b: 'N1', mid: 'N8' }];


// ── Palette ──────────────────────────────────────────────────────────────────
// PAL is a mutable object; tweaks rewrite its keys and trigger re-render via state bumps.
const PAL = { ...STYLE_PRESETS.tecnico };

// Curvature multiplier (1.0 = 10% bump per spec). Mutable; tweaks update.
const TWEAK_STATE = {
  curvatureMult: 1.0, // multiplies the 0.10 base
  tempoMult: 1.0 // multiplies playback speed (handled in App)
};

// Helper: vector ops
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const mul = (a, k) => [a[0] * k, a[1] * k];
const len = (a) => Math.hypot(a[0], a[1]);
const norm = (a) => {const l = len(a) || 1;return [a[0] / l, a[1] / l];};

// Compute outward perpendicular from edge midpoint (away from element centroid)
function outwardPerp(aC, bC, centroidC) {
  const d = sub(bC, aC);
  const n = norm([-d[1], d[0]]); // rotate 90 CCW
  const mid = mul(add(aC, bC), 0.5);
  const toCent = sub(centroidC, mid);
  // if perp points toward centroid, flip it
  const dot = n[0] * toCent[0] + n[1] * toCent[1];
  return dot > 0 ? [-n[0], -n[1]] : n;
}

// Pre-compute base geometry; bumped mid recomputed each frame using TWEAK_STATE.curvatureMult
const EDGE_GEOM = {};
for (const e of EDGES) {
  const aC = C[e.a],bC = C[e.b];
  const out = outwardPerp(aC, bC, C.N9);
  const edgeLen = len(sub(bC, aC));
  const midC = mul(add(aC, bC), 0.5);
  EDGE_GEOM[e.mid] = { baseMid: midC, outDir: out, edgeLen };
}
function bumpedMidFor(midKey) {
  const g = EDGE_GEOM[midKey];
  const bump = g.edgeLen * 0.10 * TWEAK_STATE.curvatureMult;
  return add(g.baseMid, mul(g.outDir, bump));
}

// ── Timing constants (seconds) ───────────────────────────────────────────────
const T = {
  total: 7.0,
  // Phase 0: 0.0 - 0.8
  // Phase 1 mid-nodes: 0.8 - 2.6 (cascade)
  midStart: 0.8,
  midSpacing: 0.15, // delay between successive edges starting
  midSparkDur: 0.45, // time for spark to traverse edge
  midPulseDur: 0.4, // pulse after deposit
  // Phase 2 centroid: 2.6 - 3.4
  centroidStart: 2.6,
  centroidGuideDur: 0.4,
  centroidPulseDur: 0.5,
  // Phase 3 curve: 3.4 - 4.6
  curveStart: 3.4,
  curveDur: 1.2,
  // Phase 4 hold Q9: 4.6 - 5.4
  // Phase 5 reverse: 5.4 - 6.6
  uncurveStart: 5.4,
  uncurveDur: 0.4,
  collapseStart: 5.8,
  collapseSpacing: 0.1, // reverse cascade
  collapseDur: 0.35
  // Phase 6: 6.6 - 7.0 stable Q4
};

// Per-edge spark start times
function sparkStartFor(idx) {
  return T.midStart + idx * T.midSpacing;
}
function midDepositTimeFor(idx) {
  return sparkStartFor(idx) + T.midSparkDur;
}

// Reverse cascade: first N9, then N7, N6, N5, N8 (per spec)
const COLLAPSE_ORDER = ['N9', 'N7', 'N6', 'N5', 'N8'];
function collapseStartFor(node) {
  const idx = COLLAPSE_ORDER.indexOf(node);
  return T.collapseStart + idx * T.collapseSpacing;
}

// ── Helpers to compute curve progress at time t ──────────────────────────────
function midNodeAt(time, idx) {
  // returns [pos, visible, opacity] for the mid-node center,
  // interpolating between straight midpoint and bumped position based on curve phase
  const e = EDGES[idx];
  const baseMid = mul(add(C[e.a], C[e.b]), 0.5);
  const bumped = bumpedMidFor(e.mid);

  // visibility: appears at deposit time, disappears at collapse start for that node
  const deposit = midDepositTimeFor(idx);
  const collapse = collapseStartFor(e.mid);
  const collapseEnd = collapse + T.collapseDur;

  let opacity = 0;
  if (time >= deposit && time < collapse) opacity = 1;else
  if (time >= collapse && time < collapseEnd) {
    opacity = 1 - Easing.easeInCubic((time - collapse) / T.collapseDur);
  }

  // position interpolation: straight mid -> bumped during curve phase, back during uncurve
  let curveT = 0;
  if (time >= T.curveStart && time < T.curveStart + T.curveDur) {
    curveT = Easing.easeInOutCubic((time - T.curveStart) / T.curveDur);
  } else if (time >= T.curveStart + T.curveDur && time < T.uncurveStart) {
    curveT = 1;
  } else if (time >= T.uncurveStart && time < T.uncurveStart + T.uncurveDur) {
    curveT = 1 - Easing.easeInOutCubic((time - T.uncurveStart) / T.uncurveDur);
  }

  // Subtle wobble during curve hold for "flexibility"
  let wobble = 0;
  if (time >= T.curveStart + T.curveDur && time < T.uncurveStart) {
    wobble = Math.sin((time - (T.curveStart + T.curveDur)) * 4) * 1.5;
  }

  const pos = [
  baseMid[0] + (bumped[0] - baseMid[0]) * curveT,
  baseMid[1] + (bumped[1] - baseMid[1]) * curveT + wobble * curveT];


  return { pos, opacity, deposit, collapse };
}

function centroidAt(time) {
  const deposit = T.centroidStart + T.centroidGuideDur;
  const collapse = collapseStartFor('N9');
  const collapseEnd = collapse + T.collapseDur;
  let opacity = 0;
  if (time >= deposit && time < collapse) opacity = 1;else
  if (time >= collapse && time < collapseEnd) {
    opacity = 1 - Easing.easeInCubic((time - collapse) / T.collapseDur);
  }
  return { pos: C.N9, opacity, deposit, collapse };
}

// ── Components ──────────────────────────────────────────────────────────────

function Background() {
  // subtle grid + ambient panel
  const lines = [];
  // Vertical
  for (let x = 0; x <= PX_MAX; x += 0.5) {
    const [x1, y1] = toCanvas([x, PY_MIN]);
    const [x2, y2] = toCanvas([x, PY_MAX]);
    lines.push(<line key={`vx${x}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke={PAL.grid} strokeWidth="1" opacity="0.5" />);
  }
  for (let y = 0; y <= PY_MAX; y += 0.5) {
    const [x1, y1] = toCanvas([PX_MIN, y]);
    const [x2, y2] = toCanvas([PX_MAX, y]);
    lines.push(<line key={`hy${y}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke={PAL.grid} strokeWidth="1" opacity="0.5" />);
  }
  return <g>{lines}</g>;
}

// SVG filter defs (glow)
function Defs() {
  return (
    <defs>
      <filter id="nodeGlow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
      <filter id="strongGlow" x="-100%" y="-100%" width="300%" height="300%">
        <feGaussianBlur stdDeviation="6" />
      </filter>
      <linearGradient id="edgeGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stopColor={PAL.edge} />
        <stop offset="50%" stopColor={PAL.edgeLight} />
        <stop offset="100%" stopColor={PAL.edge} />
      </linearGradient>
    </defs>);

}

// Compute edge path d attribute, given current curve interpolation
// curveT: 0 = straight, 1 = full curve through bumped mid
function edgePath(idx, time) {
  const e = EDGES[idx];
  const a = C[e.a],b = C[e.b];

  // Curve interpolation t (same logic as midNodeAt)
  let curveT = 0;
  if (time >= T.curveStart && time < T.curveStart + T.curveDur) {
    curveT = Easing.easeInOutCubic((time - T.curveStart) / T.curveDur);
  } else if (time >= T.curveStart + T.curveDur && time < T.uncurveStart) {
    curveT = 1;
  } else if (time >= T.uncurveStart && time < T.uncurveStart + T.uncurveDur) {
    curveT = 1 - Easing.easeInOutCubic((time - T.uncurveStart) / T.uncurveDur);
  }

  const baseMid = mul(add(a, b), 0.5);
  const bumped = bumpedMidFor(e.mid);

  // Quadratic Bezier control point: control C such that the curve passes through
  // the displayed mid. For quadratic Bezier, P(0.5) = (P0 + 2*Pc + P2)/4, so
  // Pc = 2*Pm - 0.5*(P0 + P2).
  const displayedMid = [
  baseMid[0] + (bumped[0] - baseMid[0]) * curveT,
  baseMid[1] + (bumped[1] - baseMid[1]) * curveT];

  const ctrl = [
  2 * displayedMid[0] - 0.5 * (a[0] + b[0]),
  2 * displayedMid[1] - 0.5 * (a[1] + b[1])];


  return {
    d: `M ${a[0]} ${a[1]} Q ${ctrl[0]} ${ctrl[1]} ${b[0]} ${b[1]}`,
    curveT
  };
}

function Edges() {
  const time = useTime();
  const paths = EDGES.map((e, idx) => {
    const { d, curveT } = edgePath(idx, time);
    return (
      <path
        key={idx}
        d={d}
        fill="none"
        stroke={curveT > 0.05 ? "url(#edgeGrad)" : PAL.edge}
        strokeWidth="2.5"
        strokeLinecap="round"
        opacity="0.95"
        style={{ filter: 'drop-shadow(0 0 3px rgba(79,163,255,0.45))' }} />);


  });
  return <g>{paths}</g>;
}

// Ghost outline of straight Q4 during curve phase
function GhostQuad() {
  const time = useTime();
  // Show during curve transition only
  let opacity = 0;
  if (time >= T.curveStart && time < T.curveStart + T.curveDur + 0.1) {
    const local = (time - T.curveStart) / (T.curveDur + 0.1);
    // opacity rises then fades
    if (local < 0.5) opacity = local * 2 * 0.5;else
    opacity = (1 - local) * 2 * 0.5;
    opacity = Math.max(0, opacity);
  }
  if (opacity <= 0.01) return null;
  const d = `M ${C.N1[0]} ${C.N1[1]} L ${C.N2[0]} ${C.N2[1]} L ${C.N3[0]} ${C.N3[1]} L ${C.N4[0]} ${C.N4[1]} Z`;
  return (
    <path d={d} fill="none" stroke={PAL.edgeLight} strokeWidth="1.5"
    strokeDasharray="4 5" opacity={opacity} />);

}

// Spark traveling along a straight edge from corner to mid (during phase 1)
function Sparks() {
  const time = useTime();
  return (
    <g>
      {EDGES.map((e, idx) => {
        const start = sparkStartFor(idx);
        const end = start + T.midSparkDur;
        if (time < start || time > end) return null;
        const local = (time - start) / T.midSparkDur;
        const eased = Easing.easeInOutCubic(local);
        const a = C[e.a],b = C[e.b];
        const baseMid = mul(add(a, b), 0.5);
        // travel from a to baseMid
        const head = [a[0] + (baseMid[0] - a[0]) * eased, a[1] + (baseMid[1] - a[1]) * eased];

        // Trail: ~30% of path behind head
        const trailLen = 0.3;
        const tailEased = Math.max(0, eased - trailLen);
        const tail = [a[0] + (baseMid[0] - a[0]) * tailEased, a[1] + (baseMid[1] - a[1]) * tailEased];

        return (
          <g key={idx}>
            <line x1={tail[0]} y1={tail[1]} x2={head[0]} y2={head[1]}
            stroke={PAL.glow} strokeWidth="3" strokeLinecap="round"
            opacity="0.7"
            style={{ filter: 'drop-shadow(0 0 6px rgba(255,235,59,0.9))' }} />
            <circle cx={head[0]} cy={head[1]} r="5" fill={PAL.glow}
            style={{ filter: 'drop-shadow(0 0 8px rgba(255,235,59,1))' }} />
          </g>);

      })}
    </g>);

}

// Radial pulse rings (yellow + node-color combined)
function PulseRing({ cx, cy, startTime, dur, time, maxR = 40, color = PAL.glow, second }) {
  if (time < startTime || time > startTime + dur) return null;
  const t = (time - startTime) / dur;
  const eased = Easing.easeOutCubic(t);
  const r = eased * maxR;
  const opacity = (1 - t) * 0.9;
  return (
    <g>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color}
      strokeWidth="2" opacity={opacity} />
      {second &&
      <circle cx={cx} cy={cy} r={r * 0.7} fill="none" stroke={second}
      strokeWidth="2" opacity={opacity * 0.8} />
      }
    </g>);

}

// Guide lines from mid-nodes to centroid
function CentroidGuides() {
  const time = useTime();
  const start = T.centroidStart;
  const end = start + T.centroidGuideDur;
  if (time < start || time > end + 0.1) return null;
  const local = clamp((time - start) / T.centroidGuideDur, 0, 1);
  const eased = Easing.easeInOutCubic(local);

  // fade in then out at end
  let opacity;
  if (local < 0.6) opacity = local / 0.6 * 0.7;else
  opacity = (1 - (local - 0.6) / 0.4) * 0.7;
  opacity = Math.max(0, opacity);

  return (
    <g>
      {['N5', 'N6', 'N7', 'N8'].map((m) => {
        const mp = C[m];
        const head = [mp[0] + (C.N9[0] - mp[0]) * eased, mp[1] + (C.N9[1] - mp[1]) * eased];
        return (
          <line key={m} x1={mp[0]} y1={mp[1]} x2={head[0]} y2={head[1]}
          stroke={PAL.centroid} strokeWidth="1.2"
          strokeDasharray="3 4" opacity={opacity} />);

      })}
    </g>);

}

// A single node circle with glow + label
function Node({ cx, cy, r, color, label, labelOffset, opacity = 1, breathing = 0 }) {
  if (opacity <= 0.01) return null;
  const breathScale = 1 + breathing * 0.15;
  return (
    <g style={{ opacity }}>
      {/* outer soft glow */}
      <circle cx={cx} cy={cy} r={r * 2.2 * breathScale} fill={color} opacity="0.18"
      style={{ filter: 'blur(6px)' }} />
      {/* core */}
      <circle cx={cx} cy={cy} r={r} fill={color}
      stroke="#ffffff" strokeWidth="1.2" opacity="1" />
      {/* highlight specular */}
      <circle cx={cx - r * 0.3} cy={cy - r * 0.3} r={r * 0.35} fill="#ffffff" opacity="0.35" />
      {label &&
      <text x={cx + labelOffset[0]} y={cy + labelOffset[1]}
      fill={PAL.text} fontFamily="Inter, system-ui, sans-serif"
      fontSize="13" fontWeight="500"
      opacity={opacity}>
          {label}
        </text>
      }
    </g>);

}

// Determine label offset by direction from centroid
function labelOffsetFor(nodePos, away = 18) {
  const d = sub(nodePos, C.N9);
  const n = norm(d);
  return [n[0] * away - 4, n[1] * away + 5];
}

function Corners() {
  const time = useTime();
  // Corners always visible
  const corners = ['N1', 'N2', 'N3', 'N4'];
  return (
    <g>
      {corners.map((k, i) => {
        const p = C[k];
        const off = labelOffsetFor(p, 22);
        return (
          <Node key={k} cx={p[0]} cy={p[1]} r={7} color={PAL.corner}
          label={String(i + 1)} labelOffset={off} />);

      })}
    </g>);

}

function MidNodes() {
  const time = useTime();
  return (
    <g>
      {EDGES.map((e, idx) => {
        const { pos, opacity, deposit, collapse } = midNodeAt(time, idx);
        const labelIdx = idx + 5; // N5..N8
        // Label fade-in: 0.25s after deposit
        let labelOp = 0;
        if (time >= deposit) labelOp = clamp((time - deposit) / 0.25, 0, 1);
        labelOp = Math.min(labelOp, opacity);
        const off = labelOffsetFor(pos, 20);
        return (
          <g key={e.mid}>
            {/* deposit pulse */}
            <PulseRing cx={pos[0]} cy={pos[1]} startTime={deposit}
            dur={T.midPulseDur} time={time} maxR={40} color={PAL.glow}
            second={PAL.mid} />
            {/* collapse pulse (radial inverse): use shrinking ring */}
            {time >= collapse && time <= collapse + T.collapseDur &&
            <CollapseRing cx={pos[0]} cy={pos[1]} startTime={collapse}
            dur={T.collapseDur} time={time} color={PAL.mid} />
            }
            <Node cx={pos[0]} cy={pos[1]} r={5.5} color={PAL.mid}
            label={String(labelIdx)} labelOffset={off} opacity={opacity} />
          </g>);

      })}
    </g>);

}

function CollapseRing({ cx, cy, startTime, dur, time, color }) {
  const t = clamp((time - startTime) / dur, 0, 1);
  const r = (1 - Easing.easeInQuad(t)) * 30 + 5;
  const opacity = (1 - t) * 0.7;
  return <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="2" opacity={opacity} />;
}

function Centroid() {
  const time = useTime();
  const { pos, opacity, deposit, collapse } = centroidAt(time);
  // Breathing pulse during phase 4 stable
  let breathing = 0;
  if (time >= T.curveStart + T.curveDur && time < T.uncurveStart) {
    breathing = (Math.sin((time - (T.curveStart + T.curveDur)) * 2 * Math.PI / 0.8) + 1) / 2;
  }
  const off = [12, -10];
  return (
    <g>
      {/* combined deposit pulse: yellow + violet */}
      <PulseRing cx={pos[0]} cy={pos[1]} startTime={deposit}
      dur={T.centroidPulseDur} time={time} maxR={60} color={PAL.glow}
      second={PAL.centroid} />
      <PulseRing cx={pos[0]} cy={pos[1]} startTime={deposit + 0.05}
      dur={T.centroidPulseDur} time={time} maxR={45} color={PAL.centroid} />
      {/* breathing pulse during Q9 hold */}
      {breathing > 0.01 && opacity > 0.5 &&
      <circle cx={pos[0]} cy={pos[1]} r={9 + breathing * 6} fill="none"
      stroke={PAL.centroid} strokeWidth="1.5" opacity={(1 - breathing) * 0.5} />
      }
      {time >= collapse && time <= collapse + T.collapseDur &&
      <CollapseRing cx={pos[0]} cy={pos[1]} startTime={collapse}
      dur={T.collapseDur} time={time} color={PAL.centroid} />
      }
      <Node cx={pos[0]} cy={pos[1]} r={5.5} color={PAL.centroid}
      label="9" labelOffset={off} opacity={opacity} breathing={breathing} />
    </g>);

}

// ── Text overlays (badge, subtitle, header, footer) ─────────────────────────

function Badge() {
  const time = useTime();
  // Q4 label until edges have curved enough (around middle of curve phase)
  // We swap label at curveStart + curveDur*0.5
  const swapTime = T.curveStart + T.curveDur * 0.5;
  const reverseSwap = T.uncurveStart + T.uncurveDur * 0.5;

  let isQ9 = false;
  if (time >= swapTime && time < reverseSwap) isQ9 = true;

  const text = isQ9 ? 'Q9 · 9 nodos · interpolación bicuadrática' :
  'Q4 · 4 nodos · interpolación bilineal';

  // Crossfade opacity around swap moments
  const fadeWindow = 0.2;
  let opacity = 1;
  const distToSwap = Math.min(
    Math.abs(time - swapTime),
    Math.abs(time - reverseSwap)
  );
  if (distToSwap < fadeWindow) {
    opacity = distToSwap / fadeWindow;
  }

  return (
    <g style={{ opacity }}>
      <rect x="40" y="36" width="380" height="40" rx="8"
      fill="#1a1a2a" stroke="#3a3a55" strokeWidth="1" opacity="0.8" />
      <circle cx="60" cy="56" r="5" fill={isQ9 ? PAL.centroid : PAL.corner} />
      <text x="76" y="60" fill={PAL.text} fontFamily="Inter, system-ui, sans-serif"
      fontSize="15" fontWeight="500" letterSpacing="0.01em">
        {text}
      </text>
    </g>);

}

function Subtitle() {
  const time = useTime();
  const swapTime = T.curveStart + T.curveDur * 0.5;
  const reverseSwap = T.uncurveStart + T.uncurveDur * 0.5;
  let isQ9 = time >= swapTime && time < reverseSwap;
  const text = isQ9 ? '18 grados de libertad — aristas pueden ser curvas' :
  '8 grados de libertad — aristas estrictamente rectas';

  const fadeWindow = 0.2;
  let opacity = 1;
  const distToSwap = Math.min(
    Math.abs(time - swapTime),
    Math.abs(time - reverseSwap)
  );
  if (distToSwap < fadeWindow) opacity = distToSwap / fadeWindow;

  return (
    <text x={CANVAS_W / 2} y={CANVAS_H - 80} textAnchor="middle"
    fill={PAL.text} fontFamily="Inter, system-ui, sans-serif"
    fontSize="17" fontWeight="400" opacity={opacity * 0.9}
    letterSpacing="0.01em">
      {text}
    </text>);

}

function Header() {
  return (
    <text x={CANVAS_W - 40} y={62} textAnchor="end"
    fill={PAL.text} fontFamily="Inter, system-ui, sans-serif"
    fontSize="14" fontWeight="300" opacity="0.6"
    letterSpacing="0.04em">
      EduFEM · Tipo de Elemento Q4 ↔ Q9
    </text>);

}

function Footer() {
  return (
    <text x={CANVAS_W / 2} y={CANVAS_H - 36} textAnchor="middle"
    fill={PAL.text} fontFamily="Inter, system-ui, sans-serif"
    fontSize="12" fontWeight="300" opacity="0.5"
    letterSpacing="0.02em">
      Demostración educativa — los 5 nodos extra de Q9 enriquecen la interpolación geométrica y de campo dentro del elemento.
    </text>);

}

// Greek symbol legend bottom-left, italic, very subtle
function GreekHint() {
  const time = useTime();
  // appears during Q9 hold
  const start = T.curveStart + T.curveDur;
  const end = T.uncurveStart;
  let opacity = 0;
  if (time >= start && time < end) {
    const fadeIn = 0.4;
    if (time < start + fadeIn) opacity = (time - start) / fadeIn;else
    if (time > end - fadeIn) opacity = (end - time) / fadeIn;else
    opacity = 1;
    opacity *= 0.5;
  }
  if (opacity <= 0.01) return null;
  return (
    <g style={{ opacity }}>
      <text x="60" y={CANVAS_H - 110} fill={PAL.text}
      fontFamily="Inter, system-ui, sans-serif" fontSize="13"
      fontStyle="italic" fontWeight="400">
        Nᵢ(ξ, η) — funciones de forma bicuadráticas
      </text>
    </g>);

}

// ── Main scene ──────────────────────────────────────────────────────────────

function Scene() {
  return (
    <svg width={CANVAS_W} height={CANVAS_H}
    style={{ position: 'absolute', inset: 0, background: PAL.bg, display: 'block' }}>
      <Defs />
      {/* inner panel */}
      <rect x="20" y="20" width={CANVAS_W - 40} height={CANVAS_H - 40}
      rx="14" fill={PAL.panel} stroke="#3a3a55" strokeWidth="1" style={{ fill: "rgb(22, 23, 22)", stroke: "rgb(42, 42, 223)" }} />
      <Background />
      <GhostQuad />
      <CentroidGuides />
      <Edges />
      <Sparks />
      <Corners />
      <MidNodes />
      <Centroid />
    </svg>);

}

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [, bumpRender] = React.useReducer(x => x + 1, 0);

  React.useEffect(() => {
    const preset = STYLE_PRESETS[tweaks.estilo] || STYLE_PRESETS.tecnico;
    Object.assign(PAL, preset);
    TWEAK_STATE.curvatureMult = (tweaks.curvatura || 10) / 10;
    TWEAK_STATE.tempoMult = tweaks.ritmo || 1;
    bumpRender();
  }, [tweaks.estilo, tweaks.curvatura, tweaks.ritmo]);

  const duration = T.total / (tweaks.ritmo || 1);

  return (
    <React.Fragment>
      <Stage width={CANVAS_W} height={CANVAS_H} duration={duration}
        background={PAL.bg} loop={true} autoplay={true}
        persistKey={`q4q9-${tweaks.estilo}`}>
        <Scene />
      </Stage>
      <TweaksPanel title="Tweaks">
        <TweakSection label="Estilo visual" />
        <TweakRadio label="Tema" value={tweaks.estilo}
          options={['tecnico', 'holografico', 'pizarra']}
          onChange={(v) => setTweak('estilo', v)} />
        <TweakSection label="Geometría" />
        <TweakSlider label="Curvatura Q9" value={tweaks.curvatura}
          min={0} max={28} step={1} unit="%"
          onChange={(v) => setTweak('curvatura', v)} />
        <TweakSection label="Animación" />
        <TweakSlider label="Ritmo" value={tweaks.ritmo}
          min={0.4} max={2.2} step={0.1} unit="×"
          onChange={(v) => setTweak('ritmo', Math.round(v * 10) / 10)} />
      </TweaksPanel>
    </React.Fragment>);
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);