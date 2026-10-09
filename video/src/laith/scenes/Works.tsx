import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Icon, IconName } from "../Icons";
import { TriangleBand } from "../Najran";
import { FONT, WHITE } from "../theme";
import { clamp, RiseText, SmallLogo, useEnter } from "../ui";

// `at` follows the voiceover: each card lands as its action is spoken.
const WORKS: { icon: IconName; title: string; sub: string; at: number }[] = [
  { icon: "siren", title: "مباشرة البلاغات", sub: "استجابة ميدانية سريعة", at: 12 },
  { icon: "search", title: "البحث عن المفقودين", sub: "في الجبال والأودية والصحراء", at: 68 },
  { icon: "aid", title: "إسعاف المصابين", sub: "إسعافات أولية في موقع الحادث", at: 130 },
  { icon: "shield", title: "التدريب والتوعية", sub: "نشر ثقافة السلامة في المجتمع", at: 186 },
];

const Card: React.FC<(typeof WORKS)[number]> = ({ icon, title, sub, at }) => {
  const frame = useCurrentFrame();
  const p = useEnter(at, 15);
  const draw = interpolate(frame, [at + 4, at + 30], [0, 1], clamp);
  const active = interpolate(frame, [at, at + 10, at + 56, at + 70], [0, 1, 1, 0], clamp);
  return (
    <div
      style={{
        width: 900,
        height: 196,
        borderRadius: 32,
        border: `3px solid rgba(255,255,255,${0.35 + active * 0.65})`,
        background: `rgba(255,255,255,${0.05 + active * 0.07})`,
        display: "flex",
        flexDirection: "row-reverse",
        alignItems: "center",
        padding: "0 44px",
        gap: 36,
        opacity: p,
        transform: `translateX(${(1 - p) * 140}px)`,
        boxSizing: "border-box",
      }}
    >
      <Icon name={icon} size={112} progress={draw} />
      <div style={{ direction: "rtl", fontFamily: FONT, color: WHITE, flex: 1 }}>
        <div style={{ fontSize: 64, fontWeight: 700, lineHeight: 1.3 }}>{title}</div>
        <div style={{ fontSize: 38, fontWeight: 400, opacity: 0.8 }}>{sub}</div>
      </div>
    </div>
  );
};

export const Works: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <SmallLogo />
      <div style={{ position: "absolute", top: 400, width: "100%" }}>
        <RiseText delay={0} size={120} weight={900}>
          أعمالنا
        </RiseText>
      </div>
      <TriangleBand y={600} progress={interpolate(frame, [5, 60], [0, 1], clamp)} opacity={0.3} />
      <div
        style={{
          position: "absolute",
          top: 690,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 34,
        }}
      >
        {WORKS.map((w) => (
          <Card key={w.title} {...w} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
