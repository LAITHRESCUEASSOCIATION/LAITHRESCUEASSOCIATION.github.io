import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { Icon, IconName } from "../Icons";
import { CUT, clamp, Fill, MaskWords, Particles, useLinear } from "../kit";
import { TriangleBand } from "../Najran";
import { FONT, WHITE } from "../theme";

const WORKS: { icon: IconName; title: string }[] = [
  { icon: "siren", title: "مباشرة البلاغات" },
  { icon: "search", title: "البحث عن المفقودين" },
  { icon: "aid", title: "إسعاف المصابين" },
  { icon: "shield", title: "التدريب والتوعية" },
];
// The aid card (index 2) sits bottom-right; the next shot irises open from it
// (origin in theme.ts).
const HERO = 2;

const Card: React.FC<{ i: number; icon: IconName; title: string }> = ({ i, icon, title }) => {
  const frame = useCurrentFrame();
  const at = CUT + 10 + i * 15;
  const p = useLinear(at, at + 18, Easing.out(Easing.cubic));
  const draw = useLinear(at + 4, at + 28);
  const hero = i === HERO ? interpolate(frame, [150, 192], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) }) : 0;
  const dim = i !== HERO ? interpolate(frame, [150, 185], [1, 0.35], clamp) : 1;
  return (
    <div
      style={{
        width: 440,
        height: 460,
        borderRadius: 36,
        border: `3px solid rgba(255,255,255,${0.5 + hero * 0.5})`,
        background: `rgba(255,255,255,${0.06 + hero * 0.12})`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 24,
        opacity: p * dim,
        transform: `translateY(${(1 - p) * 60}px) scale(${1 + hero * 0.08})`,
        boxSizing: "border-box",
      }}
    >
      <Icon name={icon} size={150} progress={draw} stroke={1.4} />
      <div style={{ fontFamily: FONT, fontSize: 52, fontWeight: 700, color: WHITE, direction: "rtl", textAlign: "center", padding: "0 20px" }}>
        {title}
      </div>
    </div>
  );
};

export const WorksGrid: React.FC = () => (
  <Fill>
    <Particles count={30} opacity={0.4} />
    <div style={{ position: "absolute", top: 250, width: "100%" }}>
      <MaskWords text="أعمالنا" delay={CUT + 2} size={150} />
    </div>
    <TriangleBand y={490} progress={useLinear(CUT + 6, CUT + 40)} opacity={0.35} />
    <div
      style={{
        position: "absolute",
        top: 600,
        left: 80,
        width: 920,
        display: "flex",
        flexWrap: "wrap",
        direction: "rtl",
        gap: 40,
      }}
    >
      {WORKS.map((w, i) => (
        <Card key={w.title} i={i} {...w} />
      ))}
    </div>
  </Fill>
);
