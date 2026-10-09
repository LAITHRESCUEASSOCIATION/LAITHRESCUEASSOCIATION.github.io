import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Icon, IconName } from "../Icons";
import { CUT, clamp, Fill, MaskWords, Particles, Sweep, useLinear, useSnap } from "../kit";
import { TriangleBand } from "../Najran";
import { FONT, NAVY, WHITE } from "../theme";

export const WORKS: { icon: IconName; title: string; sub: string }[] = [
  { icon: "siren", title: "مباشرة البلاغات", sub: "استجابة ميدانية سريعة" },
  { icon: "search", title: "البحث عن المفقودين", sub: "في الجبال والأودية والصحراء" },
  { icon: "aid", title: "إسعاف المصابين", sub: "إسعافات أولية في موقع الحادث" },
  { icon: "shield", title: "التدريب والتوعية", sub: "نشر ثقافة السلامة في المجتمع" },
];

// Outlined title that fills with white from right to left.
export const WorksTitle: React.FC = () => {
  const fill = useLinear(CUT + 10, CUT + 34, Easing.inOut(Easing.cubic));
  const p = useSnap(CUT, 14, 160);
  const style: React.CSSProperties = {
    fontFamily: FONT,
    fontSize: 280,
    fontWeight: 700,
    direction: "rtl",
    textAlign: "center",
    lineHeight: 1.4,
  };
  return (
    <Fill>
      <Particles count={30} opacity={0.4} />
      <div style={{ position: "absolute", top: 640, width: "100%", transform: `scale(${1.3 - 0.3 * p})` }}>
        <div style={{ ...style, color: "transparent", WebkitTextStroke: `3px ${WHITE}` }}>أعمالنا</div>
        <div
          style={{
            ...style,
            color: WHITE,
            position: "absolute",
            inset: 0,
            clipPath: `inset(0 0 0 ${100 - fill * 100}%)`,
          }}
        >
          أعمالنا
        </div>
      </div>
      <TriangleBand y={1120} progress={useLinear(CUT + 10, CUT + 40)} opacity={0.4} />
    </Fill>
  );
};

export const WorkCard: React.FC<{ index: number }> = ({ index }) => {
  const frame = useCurrentFrame();
  const w = WORKS[index];
  const light = index % 2 === 1;
  const fg = light ? NAVY : WHITE;
  const ring = useSnap(CUT, 14, 180);
  const draw = useLinear(CUT + 2, CUT + 22);
  const spin = interpolate(frame, [0, 74], [-30, 10], clamp);
  return (
    <Fill color={light ? WHITE : NAVY}>
      {!light && <Particles count={20} opacity={0.3} />}
      <div
        style={{
          position: "absolute",
          top: 230,
          right: 90,
          fontFamily: FONT,
          fontSize: 150,
          fontWeight: 700,
          color: "transparent",
          WebkitTextStroke: `2px ${fg}`,
          opacity: 0.5,
          transform: `translateY(${(1 - ring) * -80}px)`,
        }}
      >
        0{index + 1}
      </div>
      <div
        style={{
          position: "absolute",
          top: 520,
          width: "100%",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: 440,
            height: 440,
            borderRadius: 220,
            border: `4px solid ${fg}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${ring}) rotate(${spin}deg)`,
          }}
        >
          <div style={{ transform: `rotate(${-spin}deg)` }}>
            <Icon name={w.icon} size={250} progress={draw} color={fg} stroke={1.4} />
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", top: 1080, width: "100%" }}>
        <MaskWords text={w.title} delay={CUT + 6} stagger={3} size={112} color={fg} />
        <MaskWords text={w.sub} delay={CUT + 16} stagger={2} size={56} weight={400} color={fg} style={{ opacity: 0.8 }} />
      </div>
      {!light && <Sweep delay={CUT + 26} dur={18} />}
    </Fill>
  );
};

export const Work: React.FC<{ index: number }> = ({ index }) => (
  <AbsoluteFill>
    <WorkCard index={index} />
  </AbsoluteFill>
);
