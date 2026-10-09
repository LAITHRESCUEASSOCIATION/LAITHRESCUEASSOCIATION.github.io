import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Icon } from "../Icons";
import { NAVY_DEEP, WHITE } from "../theme";
import { clamp, RiseText, SmallLogo, useEnter } from "../ui";

// A Najrani doorway: pointed arch, triangle trim, two wooden leaves that open
// ("نفتح أبوابنا") to let volunteers walk in.
const Doorway: React.FC = () => {
  const frame = useCurrentFrame();
  const open = interpolate(frame, [82, 120], [0, 1], clamp);
  const glow = interpolate(frame, [90, 140], [0, 0.1], clamp);
  const W = 520;
  const H = 640;
  const arch = `M0 ${H} L0 150 Q0 0 ${W / 2} 0 Q${W} 0 ${W} 150 L${W} ${H}`;
  const leaf = (side: -1 | 1) => (
    <g
      transform={`translate(${side === -1 ? 0 : W} 0) scale(${side * (1 - open * 0.82)} 1)`}
    >
      <rect x={0} y={150} width={W / 2} height={H - 150} fill={NAVY_DEEP} stroke={WHITE} strokeWidth={3} />
      {[230, 340, 450, 560].map((yy) => (
        <line key={yy} x1={0} x2={W / 2} y1={yy} y2={yy} stroke={WHITE} strokeOpacity={0.35} strokeWidth={2} />
      ))}
      {[200, 300, 410, 520].map((yy) => (
        <path key={yy} d={`M${W / 4 - 26} ${yy + 22} L${W / 4} ${yy} L${W / 4 + 26} ${yy + 22} Z`} fill={WHITE} fillOpacity={0.8} />
      ))}
    </g>
  );
  return (
    <svg width={W + 80} height={H + 80} viewBox={`-40 -40 ${W + 80} ${H + 80}`}>
      <path d={arch + " Z"} fill={WHITE} fillOpacity={glow} />
      {leaf(-1)}
      {leaf(1)}
      <path d={arch} fill="none" stroke={WHITE} strokeWidth={6} />
      {Array.from({ length: 9 }).map((_, i) => {
        const x = 40 + i * 55;
        return <path key={i} d={`M${x - 16} -14 L${x} -38 L${x + 16} -14 Z`} fill={WHITE} />;
      })}
    </svg>
  );
};

const Walker: React.FC<{ i: number }> = ({ i }) => {
  const p = useEnter(112 + i * 9, 14);
  return (
    <div style={{ opacity: p, transform: `translateY(${(1 - p) * 60}px) scale(${0.6 + p * 0.4})` }}>
      <Icon name="person" size={i === 2 ? 130 : 96} stroke={1.8} />
    </div>
  );
};

export const Volunteer: React.FC = () => {
  const hero = useEnter(190, 12);
  return (
    <AbsoluteFill>
      <SmallLogo />
      <div style={{ position: "absolute", top: 400, width: "100%" }}>
        <RiseText delay={6} size={150} weight={900}>
          التطوع رسالة
        </RiseText>
      </div>
      <div
        style={{
          position: "absolute",
          top: 680,
          width: "100%",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <Doorway />
      </div>
      <div
        style={{
          position: "absolute",
          top: 1080,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-end",
          gap: 8,
        }}
      >
        {[0, 1, 2, 3, 4].map((i) => (
          <Walker key={i} i={i} />
        ))}
      </div>
      <div style={{ position: "absolute", top: 1430, width: "100%" }}>
        <RiseText delay={88} size={56} weight={400} opacity={0.9}>
          لكل من يحمل روح العطاء
        </RiseText>
      </div>
      <div
        style={{
          position: "absolute",
          top: 1560,
          width: "100%",
          opacity: hero,
          transform: `scale(${0.8 + hero * 0.2})`,
        }}
      >
        <RiseText delay={190} size={104} weight={900}>
          ليكون منقذًا
        </RiseText>
      </div>
    </AbsoluteFill>
  );
};
