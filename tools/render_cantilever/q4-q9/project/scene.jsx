// scene.jsx — Cantilever Q4 vs Q9 FEM animation
// Cinematic CAD / Editorial Engineering aesthetic.

// ── Geometry constants ──────────────────────────────────────────────────────
const PANEL_W = 450;
const PANEL_H = 600;
const BEAM_L = 320;
const BEAM_H = 80;
const BEAM_X0 = 60;          // beam emerges from anchor block's right face
const BEAM_Y0 = 300;         // undeformed centerline y (panel-local)
const MAX_DEFL = 80;         // px at tip when load = 1

// ── Euler–Bernoulli cantilever, normalised so w(1) = 1 ──────────────────────
// v(x) = P x² (3L − x) / (6EI), so w(u) = u²(3 − u) / 2 with u = x/L.
const W_FN  = (u) => (u * u * (3 - u)) / 2;
const WP_FN = (u) => (6 * u - 3 * u * u) / 2; // dw/du

// ── Timeline curves (all times in seconds, total 4.0) ───────────────────────
function loadProgress(t) {
  // 0 → 1 between 0.20–1.80 with material ease, settle 1.80–2.00,
  // hold to 3.30, ramp down 3.30–3.90, zero after.
  if (t < 0.20) return 0;
  if (t < 1.80) return Easing.easeInOutCubic((t - 0.20) / 1.60);
  if (t < 2.00) {
    const u = (t - 1.80) / 0.20;
    const damp = Math.exp(-3 * u);
    const osc  = Math.sin(u * Math.PI * 4); // 2 cycles
    return 1 + (osc * damp * 0.5) / MAX_DEFL; // 0.5 px tip amplitude
  }
  if (t < 3.30) return 1;
  if (t < 3.90) return 1 - Easing.easeInOutCubic((t - 3.30) / 0.60);
  return 0;
}

function arrowAlpha(t) {
  if (t < 0.20) return 0;
  if (t < 0.36) {
    // micro-bounce in
    const u = (t - 0.20) / 0.16;
    return Math.min(1, Easing.easeOutBack(u));
  }
  if (t < 3.90) return 1;
  if (t < 4.00) return 1 - (t - 3.90) / 0.10;
  return 0;
}

function ratioProgress(t) {
  if (t < 2.00) return 0;
  if (t < 2.30) return Easing.easeOutCubic((t - 2.00) / 0.30);
  if (t < 3.30) return 1;
  if (t < 3.90) return 1 - Easing.easeInOutCubic((t - 3.30) / 0.60);
  return 0;
}

function ghostAlpha(t) {
  if (t < 2.30) return 0;
  if (t < 2.60) return 0.6 * ((t - 2.30) / 0.30);
  if (t < 3.30) return 0.6;
  if (t < 3.60) return 0.6 * (1 - (t - 3.30) / 0.30);
  return 0;
}

function q9Pulse(t) {
  // 2.30 → 2.50: scale 1 → 1.05 → 1
  if (t < 2.30 || t > 2.50) return 1;
  const u = (t - 2.30) / 0.20;
  return 1 + 0.05 * Math.sin(u * Math.PI);
}

// ── Beam geometry helpers ───────────────────────────────────────────────────
function computeBeamGeometry(uSamples, scale, withRotation) {
  return uSamples.map((u) => {
    const x = u * BEAM_L;
    const y = W_FN(u) * MAX_DEFL * scale;
    let nx = 0, ny = -1;
    if (withRotation) {
      const slope = (WP_FN(u) * MAX_DEFL * scale) / BEAM_L;
      const tLen = Math.hypot(1, slope);
      nx = slope / tLen;
      ny = -1 / tLen;
    }
    return {
      u, x, y,
      top: { x: x + (nx * BEAM_H) / 2, y: y + (ny * BEAM_H) / 2 },
      bot: { x: x - (nx * BEAM_H) / 2, y: y - (ny * BEAM_H) / 2 },
    };
  });
}

function buildOutlinePath(geom) {
  const top = geom.map((g) => g.top);
  const bot = geom.map((g) => g.bot).slice().reverse();
  const parts = [`M ${top[0].x.toFixed(2)} ${top[0].y.toFixed(2)}`];
  for (let i = 1; i < top.length; i++) parts.push(`L ${top[i].x.toFixed(2)} ${top[i].y.toFixed(2)}`);
  for (let i = 0; i < bot.length; i++) parts.push(`L ${bot[i].x.toFixed(2)} ${bot[i].y.toFixed(2)}`);
  parts.push("Z");
  return parts.join(" ");
}

function buildEdgePath(points) {
  if (!points.length) return "";
  let d = `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  for (let i = 1; i < points.length; i++) d += ` L ${points[i].x.toFixed(2)} ${points[i].y.toFixed(2)}`;
  return d;
}

// ── FEM node positions ──────────────────────────────────────────────────────
// Q4 4×1 mesh: 5 columns × 2 rows of nodes (corner-only) = 10 nodes.
// Q9 4×1 mesh: 9 columns × 3 rows (corners + midside + centers) = 27 nodes.
// Returns array of {x, y, kind} in beam-local coords (origin at left-end centerline).
function computeNodes(type, scale) {
  const cols = type === "q9"
    ? [0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
    : [0, 0.25, 0.5, 0.75, 1.0];
  const rows = type === "q9" ? [-1, 0, 1] : [-1, 1]; // -1=top, 0=center, 1=bot
  const out = [];
  for (const u of cols) {
    const x0 = u * BEAM_L;
    const y0 = W_FN(u) * MAX_DEFL * scale;
    let nx = 0, ny = -1;
    if (type === "q9") {
      const slope = (WP_FN(u) * MAX_DEFL * scale) / BEAM_L;
      const tLen = Math.hypot(1, slope);
      nx = slope / tLen;
      ny = -1 / tLen;
    }
    for (const r of rows) {
      // r=-1 → top, +1 → bottom, 0 → center
      const off = (r * BEAM_H) / 2;
      // For top/bottom, displace along normal; for center, stay on centerline.
      const px = x0 + nx * off;
      const py = y0 + ny * off;
      // Classify: corner / midside / center for Q9 — corner-only for Q4.
      let kind;
      if (type === "q4") {
        kind = "corner";
      } else {
        const isHalfCol = Math.abs((u * 8) - Math.round(u * 8)) < 1e-6 && Math.round(u * 8) % 2 === 1; // 0.125, 0.375, 0.625, 0.875
        const isCenterRow = r === 0;
        if (isHalfCol && isCenterRow) kind = "center";
        else if (isHalfCol || isCenterRow) kind = "midside";
        else kind = "corner";
      }
      out.push({ x: px, y: py, kind });
    }
  }
  return out;
}

function FemNodes({ nodes, type }) {
  // Corner nodes: solid filled, ring around. Midside / center: smaller, hollow-ish.
  const accent = type === "q9" ? "#ffb066" : "#dde0e4";
  return (
    <g>
      {nodes.map((n, i) => {
        if (n.kind === "corner") {
          return (
            <g key={i}>
              <circle cx={n.x} cy={n.y} r={4.2} fill={accent} stroke="#1c1e22" strokeWidth={1.2} />
              <circle cx={n.x} cy={n.y} r={1.4} fill="#1c1e22" />
            </g>
          );
        }
        if (n.kind === "midside") {
          return (
            <circle key={i} cx={n.x} cy={n.y} r={2.8}
              fill="#1c1e22" stroke={accent} strokeWidth={1.2} />
          );
        }
        // center
        return (
          <g key={i}>
            <circle cx={n.x} cy={n.y} r={2.6} fill={accent} opacity={0.92} />
            <circle cx={n.x} cy={n.y} r={4.6} fill="none" stroke={accent} strokeWidth={0.8} opacity={0.5} />
          </g>
        );
      })}
    </g>
  );
}

// ── Blueprint grid (background) ─────────────────────────────────────────────
function BlueprintGrid() {
  const lines = [];
  for (let x = 30; x < 900; x += 30) {
    lines.push(<line key={"v" + x} x1={x} y1={0} x2={x} y2={600} stroke="#2a2d33" strokeWidth={1} opacity={0.4} />);
  }
  for (let y = 30; y < 600; y += 30) {
    lines.push(<line key={"h" + y} x1={0} y1={y} x2={900} y2={y} stroke="#2a2d33" strokeWidth={1} opacity={0.4} />);
  }
  return <g>{lines}</g>;
}

// ── Anchor block ────────────────────────────────────────────────────────────
function AnchorBlock({ accentColor, type }) {
  return (
    <g>
      <rect x={0} y={190} width={60} height={220} fill={`url(#anchor-${type})`} />
      {/* small wedge glyph, bottom-left */}
      <path
        d="M 8 392 L 22 398 L 14 404 Z"
        fill="#cfd2d8"
        opacity={0.35}
      />
      {/* insertion-interface hairline */}
      <line x1={60} y1={190} x2={60} y2={410} stroke={accentColor} strokeWidth={1} opacity={0.6} />
    </g>
  );
}

// ── Force arrow with glow + serif P ─────────────────────────────────────────
function ForceArrow({ tipX, tipY, alpha, idSuffix }) {
  const headH = 18;
  const headW = 14;
  const shaftTop = tipY - 78;
  const shaftBot = tipY - headH;
  if (alpha <= 0.001) return null;
  return (
    <g opacity={alpha} style={{ transformBox: "fill-box", transformOrigin: `${tipX}px ${tipY}px` }}>
      {/* Outer glow */}
      <g filter={`url(#arrow-glow-${idSuffix})`} opacity={0.55}>
        <line x1={tipX} y1={shaftTop} x2={tipX} y2={shaftBot} stroke="#4fc3f7" strokeWidth={3} />
        <polygon
          points={`${tipX - headW / 2},${shaftBot} ${tipX + headW / 2},${shaftBot} ${tipX},${tipY}`}
          fill="#4fc3f7"
        />
      </g>
      {/* Shaft with vertical gradient */}
      <line
        x1={tipX} y1={shaftTop} x2={tipX} y2={shaftBot}
        stroke={`url(#arrow-shaft-${idSuffix})`}
        strokeWidth={3}
        strokeLinecap="round"
      />
      {/* Solid arrowhead */}
      <polygon
        points={`${tipX - headW / 2},${shaftBot} ${tipX + headW / 2},${shaftBot} ${tipX},${tipY}`}
        fill="#4fc3f7"
      />
      {/* Editorial italic label */}
      <text
        x={tipX + 13}
        y={shaftTop + 16}
        fill="#4fc3f7"
        fontFamily="'EB Garamond', Georgia, 'Times New Roman', serif"
        fontStyle="italic"
        fontSize={20}
        fontWeight={500}
      >
        P
      </text>
    </g>
  );
}

// ── Ratio display (counter + label) ─────────────────────────────────────────
function RatioDisplay({ value, color, pulse }) {
  const fixed = value.toFixed(2);
  return (
    <g transform={`translate(${PANEL_W / 2}, 540)`}>
      <text
        textAnchor="middle"
        y={-30}
        fill="#7a7e86"
        fontSize={11}
        letterSpacing="3"
        fontFamily="'JetBrains Mono', ui-monospace, monospace"
      >
        δ / δ_TEÓRICA
      </text>
      <g transform={`scale(${pulse})`} style={{ transformBox: "fill-box", transformOrigin: "center" }}>
        <text
          textAnchor="middle"
          fill={color}
          fontFamily="Inter, system-ui, sans-serif"
          fontSize={30}
          fontWeight={700}
          letterSpacing="0.5"
          style={{ fontVariantNumeric: "tabular-nums" }}
          dy={2}
        >
          {fixed}
        </text>
      </g>
    </g>
  );
}

// ── Single beam panel (Q4 or Q9) ────────────────────────────────────────────
function Panel({ type, title, dofLabel, ratioTarget, ratioColor, beamColors, accentColor, dx }) {
  const time = useTime();
  const load = loadProgress(time);
  const ratio = ratioProgress(time);
  const ghost = ghostAlpha(time);
  const arrowA = arrowAlpha(time);
  const pulse = type === "q9" ? q9Pulse(time) : 1;

  const baseScale = type === "q9" ? 0.99 : 0.62;
  const scale = baseScale * load;

  // Q9: many samples for a clean spline curve; Q4: only the four element joints.
  const uSamples = React.useMemo(
    () => (type === "q9" ? Array.from({ length: 33 }, (_, i) => i / 32) : [0, 0.25, 0.5, 0.75, 1.0]),
    [type]
  );

  const geom = computeBeamGeometry(uSamples, scale, type === "q9");
  const outline = buildOutlinePath(geom);
  const topEdge = buildEdgePath(geom.map((g) => g.top));
  const tip = geom[geom.length - 1];

  // Internal divisions at the 3 interior knots (u = 0.25, 0.5, 0.75).
  // For Q4 these come straight from the knot list (indices 1,2,3).
  // For Q9 we pick the matching sample indices.
  const interiorUs = [0.25, 0.5, 0.75];
  const divisionLines = interiorUs.map((u) => {
    const idx = uSamples.findIndex((v) => Math.abs(v - u) < 1e-6);
    if (idx === -1) return null;
    return geom[idx];
  });

  // Ghost (undeformed) line — the original beam outline + faint vertical division marks.
  const ghostDivisions = interiorUs.map((u) => u * BEAM_L);

  return (
    <g transform={`translate(${dx}, 0)`}>
      {/* Anchor block sits behind beam */}
      <AnchorBlock accentColor={accentColor} type={type} />

      {/* Beam + shadow + ghost — all positioned by translate to panel-local (BEAM_X0, BEAM_Y0) */}
      <g transform={`translate(${BEAM_X0}, ${BEAM_Y0})`}>
        {/* Ghost rectangle of the undeformed beam */}
        <g opacity={ghost}>
          <rect
            x={0} y={-BEAM_H / 2} width={BEAM_L} height={BEAM_H}
            fill="none" stroke="#3a3e44" strokeWidth={1}
            strokeDasharray="4 2"
          />
          {ghostDivisions.map((gx, i) => (
            <line key={i} x1={gx} y1={-BEAM_H / 2} x2={gx} y2={BEAM_H / 2}
                  stroke="#3a3e44" strokeWidth={1} strokeDasharray="3 2" />
          ))}
        </g>

        {/* Shadow follows the deformed silhouette */}
        <g transform="translate(0, 10)" filter={`url(#shadow-${type})`} opacity={0.55}>
          <path d={outline} fill="#000" />
        </g>

        {/* Beam fill */}
        <path d={outline} fill={`url(#grad-${type})`} />

        {/* Internal division lines */}
        {divisionLines.map((g, i) =>
          g ? (
            <line
              key={i}
              x1={g.top.x}
              y1={g.top.y}
              x2={g.bot.x}
              y2={g.bot.y}
              stroke="#6a7078"
              strokeWidth={1}
              opacity={0.45}
            />
          ) : null
        )}

        {/* Outline (subtle) */}
        <path d={outline} fill="none" stroke="rgba(0,0,0,0.45)" strokeWidth={0.75} />

        {/* Top-edge highlight (1px white-ish) */}
        <path d={topEdge} fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth={1} strokeLinejoin="round" />

        {/* FEM nodes — drawn on top so they sit ON the elements */}
        <FemNodes nodes={computeNodes(type, scale)} type={type} />
      </g>

      {/* Force arrow attached to the deformed top-tip */}
      <ForceArrow
        tipX={BEAM_X0 + tip.top.x}
        tipY={BEAM_Y0 + tip.top.y}
        alpha={arrowA}
        idSuffix={type}
      />

      {/* Title — "Q4 — 8 DOF" / "Q9 — 18 DOF" */}
      <text
        x={PANEL_W / 2}
        y={48}
        textAnchor="middle"
        fill="#cfd2d8"
        fontFamily="Inter, system-ui, sans-serif"
        fontSize={22}
        fontWeight={600}
        letterSpacing="0.3"
      >
        <tspan fill={accentColor}>{title}</tspan>
        <tspan fill="#7a7e86" dx={10} fontWeight={500}>— {dofLabel}</tspan>
      </text>

      <RatioDisplay value={ratio * ratioTarget} color={ratioColor} pulse={pulse} />
    </g>
  );
}

// ── SVG defs shared between panels ──────────────────────────────────────────
function SceneDefs() {
  return (
    <defs>
      {/* Q4 beam fill */}
      <linearGradient id="grad-q4" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#b8bec6" />
        <stop offset="55%" stopColor="#aab0b8" />
        <stop offset="100%" stopColor="#7a8088" />
      </linearGradient>
      {/* Q9 beam fill */}
      <linearGradient id="grad-q9" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#ff912e" />
        <stop offset="55%" stopColor="#fd7e14" />
        <stop offset="100%" stopColor="#b85408" />
      </linearGradient>
      {/* Anchor block gradients — dark at frame edge, panel-bg at beam interface */}
      <linearGradient id="anchor-q4" x1="100%" y1="0%" x2="0%" y2="0%">
        <stop offset="0%" stopColor="#1c1e22" />
        <stop offset="100%" stopColor="#06080b" />
      </linearGradient>
      <linearGradient id="anchor-q9" x1="100%" y1="0%" x2="0%" y2="0%">
        <stop offset="0%" stopColor="#1c1e22" />
        <stop offset="100%" stopColor="#06080b" />
      </linearGradient>
      {/* Shadow filters */}
      <filter id="shadow-q4" x="-20%" y="-20%" width="140%" height="180%">
        <feGaussianBlur stdDeviation="7" />
      </filter>
      <filter id="shadow-q9" x="-20%" y="-20%" width="140%" height="180%">
        <feGaussianBlur stdDeviation="7" />
      </filter>
      {/* Arrow glow */}
      <filter id="arrow-glow-q4" x="-100%" y="-50%" width="300%" height="200%">
        <feGaussianBlur stdDeviation="4" />
      </filter>
      <filter id="arrow-glow-q9" x="-100%" y="-50%" width="300%" height="200%">
        <feGaussianBlur stdDeviation="4" />
      </filter>
      {/* Arrow shaft gradient */}
      <linearGradient id="arrow-shaft-q4" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#4fc3f7" stopOpacity={0.4} />
        <stop offset="100%" stopColor="#4fc3f7" stopOpacity={1} />
      </linearGradient>
      <linearGradient id="arrow-shaft-q9" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#4fc3f7" stopOpacity={0.4} />
        <stop offset="100%" stopColor="#4fc3f7" stopOpacity={1} />
      </linearGradient>
    </defs>
  );
}

// ── Scene root ──────────────────────────────────────────────────────────────
function Scene() {
  const time = useTime();
  // Push a current-second label onto the host so comments can reference it.
  React.useEffect(() => {
    const root = document.getElementById("video-root");
    if (root) root.setAttribute("data-screen-label", `t=${time.toFixed(2)}s`);
  }, [time]);

  return (
    <div
      id="video-root"
      data-screen-label="t=0.00s"
      style={{ position: "absolute", inset: 0, background: "#1c1e22" }}
    >
      <svg
        width={900}
        height={600}
        viewBox="0 0 900 600"
        style={{ display: "block", background: "#1c1e22" }}
      >
        <SceneDefs />
        <BlueprintGrid />

        {/* Q4 — left panel (gray) */}
        <Panel
          dx={0}
          type="q4"
          title="Q4"
          dofLabel="8 DOF"
          ratioTarget={0.62}
          ratioColor="#d68545"
          beamColors={{ top: "#b8bec6", bot: "#8a9098" }}
          accentColor="#aab0b8"
        />

        {/* Hairline divider */}
        <line x1={450} y1={0} x2={450} y2={600} stroke="#3a3e44" strokeWidth={1} />

        {/* Q9 — right panel (orange) */}
        <Panel
          dx={450}
          type="q9"
          title="Q9"
          dofLabel="18 DOF"
          ratioTarget={0.99}
          ratioColor="#1fa363"
          beamColors={{ top: "#fd7e14", bot: "#c45e0a" }}
          accentColor="#fd7e14"
        />
      </svg>
    </div>
  );
}

Object.assign(window, { Scene });
