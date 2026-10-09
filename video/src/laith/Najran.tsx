import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { NAVY_DEEP, WHITE } from "./theme";

// Line-art motifs from Najran: the multi-storey mud tower houses with their
// white lime crenellations, palm groves, the Wadi Najran mountains, and the
// triangle pattern painted around Najrani windows and rooftops.

type TowerProps = {
  x: number;
  y: number;
  w: number;
  h: number;
  floors: number;
  cols?: number;
  delay?: number;
};

export const MudTower: React.FC<TowerProps> = ({
  x,
  y,
  w,
  h,
  floors,
  cols = 2,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 22, stiffness: 170 } });
  const top = w * 0.44;
  const half = (yy: number) => w / 2 - ((w / 2 - top) * -yy) / h;

  const ridges = [];
  for (let yy = -16; yy > -h + 20; yy -= 16) {
    ridges.push(
      <line
        key={yy}
        x1={-half(yy)}
        x2={half(yy)}
        y1={yy}
        y2={yy}
        stroke={WHITE}
        strokeOpacity={0.1}
        strokeWidth={2}
      />,
    );
  }

  const crenW = 16;
  const crenN = Math.floor((top * 2) / crenW);
  const crenStart = -(crenN * crenW) / 2;
  const crenellations = [];
  for (let i = 0; i < crenN; i++) {
    const cx = crenStart + i * crenW;
    crenellations.push(
      <path
        key={i}
        d={`M${cx} ${-h} L${cx + crenW / 2} ${-h - 16} L${cx + crenW} ${-h} Z`}
        fill={WHITE}
      />,
    );
  }

  const windows = [];
  const floorH = (h - 60) / floors;
  for (let f = 0; f < floors; f++) {
    const wy = -h + 50 + f * floorH;
    for (let c = 0; c < cols; c++) {
      const wx = ((c + 0.5) / cols - 0.5) * half(wy) * 1.3;
      windows.push(
        <g key={`${f}-${c}`} transform={`translate(${wx} ${wy})`}>
          <rect
            x={-8}
            y={0}
            width={16}
            height={22}
            fill={NAVY_DEEP}
            stroke={WHITE}
            strokeWidth={2.5}
          />
          <path d="M-10 -4 L0 -14 L10 -4 Z" fill={WHITE} />
        </g>,
      );
    }
  }

  return (
    <g
      transform={`translate(${x} ${y + (1 - p) * (h + 40)})`}
      opacity={Math.min(1, p * 1.5)}
    >
      <path
        d={`M${-w / 2} 0 L${w / 2} 0 L${top} ${-h} L${-top} ${-h} Z`}
        fill={NAVY_DEEP}
        stroke={WHITE}
        strokeWidth={3}
        strokeLinejoin="round"
      />
      {ridges}
      <path
        d={`M${-top} ${-h} L${top} ${-h} L${top - 1} ${-h + 12} L${-top + 1} ${-h + 12} Z`}
        fill={WHITE}
      />
      {crenellations}
      <path
        d={`M${-top} ${-h} l0 -26 l12 0 l0 26 Z M${top} ${-h} l0 -26 l-12 0 l0 26 Z`}
        fill={WHITE}
      />
      {windows}
      <path
        d={`M-12 0 L-12 -30 Q0 -44 12 -30 L12 0`}
        fill={NAVY_DEEP}
        stroke={WHITE}
        strokeWidth={2.5}
      />
    </g>
  );
};

export const Palm: React.FC<{
  x: number;
  y: number;
  h: number;
  lean?: number;
  phase?: number;
  delay?: number;
}> = ({ x, y, h, lean = 20, phase = 0, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 22, stiffness: 170 } });
  const sway = Math.sin(frame / 22 + phase) * 2.5;
  const cx = lean;
  const cy = -h;
  const fronds = [-150, -120, -95, -70, -40, -15, 15].map((a, i) => {
    const r = (a * Math.PI) / 180;
    const len = 70 + (i % 2) * 14;
    const ex = cx + Math.cos(r) * len;
    const ey = cy + Math.sin(r) * len * 0.75 + len * 0.35;
    const mx = cx + Math.cos(r) * len * 0.55;
    const my = cy + Math.sin(r) * len * 0.75 - 12;
    return (
      <path
        key={a}
        d={`M${cx} ${cy} Q${mx} ${my} ${ex} ${ey}`}
        stroke={WHITE}
        strokeWidth={3}
        fill="none"
        strokeLinecap="round"
      />
    );
  });
  return (
    <g
      transform={`translate(${x} ${y}) scale(${p}) rotate(${sway} 0 0)`}
      opacity={p}
    >
      <path
        d={`M0 0 Q${lean * 0.2} ${-h * 0.6} ${cx} ${cy}`}
        stroke={WHITE}
        strokeWidth={5}
        fill="none"
        strokeLinecap="round"
      />
      {[0.2, 0.35, 0.5, 0.65, 0.8].map((t) => (
        <line
          key={t}
          x1={lean * t * t - 5}
          x2={lean * t * t + 5}
          y1={-h * t}
          y2={-h * t - 3}
          stroke={NAVY_DEEP}
          strokeWidth={2}
        />
      ))}
      {fronds}
      <circle cx={cx - 6} cy={cy + 10} r={4} fill={WHITE} />
      <circle cx={cx + 4} cy={cy + 12} r={4} fill={WHITE} />
    </g>
  );
};

export const Mountains: React.FC<{ y: number; progress: number }> = ({
  y,
  progress,
}) => {
  const ridge =
    "M-20 0 L80 -170 L150 -110 L250 -260 L340 -150 L420 -210 L520 -90 L610 -230 L700 -140 L790 -300 L900 -160 L980 -220 L1100 -80";
  return (
    <g transform={`translate(0 ${y})`}>
      <path d={`${ridge} L1100 0 Z`} fill={NAVY_DEEP} fillOpacity={0.55} />
      <path
        d={ridge}
        fill="none"
        stroke={WHITE}
        strokeOpacity={0.35}
        strokeWidth={2.5}
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - progress}
      />
    </g>
  );
};

// Full skyline: mountains, tower houses and palms, anchored to `baseY`.
export const NajranSkyline: React.FC<{ baseY: number; delay?: number }> = ({
  baseY,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const m = interpolate(frame - delay, [0, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <svg
      width={1080}
      height={1920}
      viewBox="0 0 1080 1920"
      style={{ position: "absolute", inset: 0 }}
    >
      <Mountains y={baseY - 120} progress={m} />
      <Palm x={60} y={baseY} h={250} lean={30} phase={1} delay={delay + 30} />
      <MudTower x={200} y={baseY} w={170} h={360} floors={4} delay={delay + 10} />
      <MudTower x={390} y={baseY} w={210} h={520} floors={6} cols={3} delay={delay + 18} />
      <Palm x={530} y={baseY} h={300} lean={-26} phase={2} delay={delay + 36} />
      <MudTower x={680} y={baseY} w={190} h={440} floors={5} delay={delay + 24} />
      <MudTower x={880} y={baseY} w={160} h={330} floors={4} delay={delay + 14} />
      <Palm x={1010} y={baseY} h={270} lean={-30} phase={3} delay={delay + 40} />
      <rect x={0} y={baseY} width={1080} height={1920 - baseY} fill={NAVY_DEEP} />
      <line x1={0} x2={1080} y1={baseY} y2={baseY} stroke={WHITE} strokeWidth={3} />
    </svg>
  );
};

// Najrani triangle band (as painted around windows and roof edges).
export const TriangleBand: React.FC<{
  y: number;
  progress?: number;
  opacity?: number;
}> = ({ y, progress = 1, opacity = 0.5 }) => {
  const size = 30;
  const n = Math.ceil(1080 / size) + 1;
  const shown = Math.floor(n * progress);
  return (
    <svg
      width={1080}
      height={size + 10}
      style={{ position: "absolute", left: 0, top: y }}
      opacity={opacity}
    >
      {Array.from({ length: shown }).map((_, i) => {
        const x = i * size;
        return (
          <g key={i}>
            <path d={`M${x} ${size} L${x + size / 2} 4 L${x + size} ${size} Z`} fill={WHITE} />
            <circle cx={x + size} cy={10} r={3} fill={WHITE} />
          </g>
        );
      })}
    </svg>
  );
};
