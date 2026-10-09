import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { NajranSkyline, TriangleBand } from "../Najran";
import { WHITE } from "../theme";
import { clamp, Logo, RiseText, useEnter } from "../ui";

const Stars: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <svg width={1080} height={1100} style={{ position: "absolute", top: 0 }}>
      {Array.from({ length: 70 }).map((_, i) => {
        const x = random(`x${i}`) * 1080;
        const y = random(`y${i}`) * 1000;
        const tw = 0.35 + 0.65 * Math.abs(Math.sin(frame / 18 + i));
        const appear = interpolate(frame, [i * 0.6, i * 0.6 + 20], [0, 1], clamp);
        return (
          <circle
            key={i}
            cx={x}
            cy={y}
            r={1 + random(`r${i}`) * 2.2}
            fill={WHITE}
            opacity={tw * appear * 0.8}
          />
        );
      })}
    </svg>
  );
};

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const logo = useEnter(70, 14);
  const moon = useEnter(0, 30);
  return (
    <AbsoluteFill>
      <Stars />
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        <circle
          cx={860}
          cy={260 + (1 - moon) * 60}
          r={64}
          fill={WHITE}
          opacity={0.9 * moon}
        />
        <circle cx={884} cy={244 + (1 - moon) * 60} r={58} fill="#023a55" opacity={moon} />
      </svg>
      <NajranSkyline baseY={1500} delay={6} />
      <div style={{ position: "absolute", top: 250, width: "100%" }}>
        <RiseText delay={20} size={64} weight={400} opacity={0.85}>
          من نجران
        </RiseText>
      </div>
      <div
        style={{
          position: "absolute",
          top: 380,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          opacity: logo,
          transform: `scale(${0.85 + logo * 0.15})`,
        }}
      >
        <Logo width={640} />
      </div>
      <TriangleBand
        y={1545}
        progress={interpolate(frame, [40, 110], [0, 1], clamp)}
        opacity={0.35}
      />
      <div style={{ position: "absolute", top: 1640, width: "100%" }}>
        <RiseText delay={95} size={62} weight={500}>
          أرض الأصالة والتاريخ
        </RiseText>
      </div>
    </AbsoluteFill>
  );
};
