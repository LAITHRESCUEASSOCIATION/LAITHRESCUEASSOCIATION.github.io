import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Icon, IconName } from "../Icons";
import { Mountains, TriangleBand } from "../Najran";
import { FONT, WHITE } from "../theme";
import { clamp, Divider, RiseText, SmallLogo, useEnter } from "../ui";

const TERRAIN: { icon: IconName; label: string; at: number }[] = [
  { icon: "mountain", label: "الجبال", at: 150 },
  { icon: "wadi", label: "الأودية", at: 170 },
  { icon: "dunes", label: "الصحراء", at: 190 },
];

const Terrain: React.FC<{ icon: IconName; label: string; at: number }> = ({
  icon,
  label,
  at,
}) => {
  const p = useEnter(at, 14);
  const frame = useCurrentFrame();
  const draw = interpolate(frame, [at, at + 25], [0, 1], clamp);
  return (
    <div
      style={{
        width: 280,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 18,
        opacity: p,
        transform: `translateY(${(1 - p) * 50}px)`,
      }}
    >
      <div
        style={{
          width: 190,
          height: 190,
          borderRadius: 95,
          border: `3px solid ${WHITE}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Icon name={icon} size={110} progress={draw} />
      </div>
      <div style={{ fontFamily: FONT, fontSize: 58, fontWeight: 700, color: WHITE }}>
        {label}
      </div>
    </div>
  );
};

export const About: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        <Mountains y={1920} progress={interpolate(frame, [0, 60], [0, 1], clamp)} />
      </svg>
      <SmallLogo />
      <div style={{ position: "absolute", top: 470, width: "100%" }}>
        <RiseText delay={8} size={128} weight={900}>
          جمعية تطوعية
        </RiseText>
        <Divider delay={30} />
        <RiseText delay={62} size={74} weight={500}>
          في الصفوف الأولى
        </RiseText>
        <RiseText delay={80} size={74} weight={500}>
          لنجدة الإنسان
        </RiseText>
      </div>
      <div
        style={{
          position: "absolute",
          top: 1130,
          width: "100%",
          display: "flex",
          flexDirection: "row-reverse",
          justifyContent: "center",
          gap: 30,
        }}
      >
        {TERRAIN.map((t) => (
          <Terrain key={t.label} {...t} />
        ))}
      </div>
      <TriangleBand y={1500} progress={interpolate(frame, [150, 240], [0, 1], clamp)} opacity={0.3} />
    </AbsoluteFill>
  );
};
