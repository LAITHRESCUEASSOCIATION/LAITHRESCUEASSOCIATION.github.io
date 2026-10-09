import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { CUT, clamp, Fill, Marker, MaskWords, Particles, Punch, Rings } from "../kit";
import { Mountains } from "../Najran";

// Kinetic type on the beat (15 frames).
export const About: React.FC = () => {
  const frame = useCurrentFrame();
  const lift = interpolate(frame, [CUT + 48, CUT + 62], [0, 1], {
    ...clamp,
    easing: Easing.inOut(Easing.cubic),
  });
  return (
    <Fill>
      <Rings y={1920} opacity={0.15} />
      <Particles count={25} opacity={0.35} />
      <svg width={1080} height={1920} style={{ position: "absolute" }}>
        <Mountains y={1940} progress={interpolate(frame, [CUT, CUT + 40], [0, 1], clamp)} />
      </svg>
      <div
        style={{
          position: "absolute",
          top: 560,
          width: "100%",
          transform: `translateY(${-lift * 260}px) scale(${1 - lift * 0.3})`,
        }}
      >
        <MaskWords text="جمعية" delay={CUT + 2} size={210} />
        <div style={{ display: "flex", justifyContent: "center", marginTop: -40 }}>
          <Marker text="تطوعية" delay={CUT + 17} size={190} />
        </div>
      </div>
      <AbsoluteFill style={{ top: 1010 }}>
        <MaskWords text="في الصفوف الأولى" delay={CUT + 56} stagger={3} size={96} weight={400} />
        <Punch text="لنجدة الإنسان" delay={CUT + 74} size={120} style={{ marginTop: 10 }} />
      </AbsoluteFill>
    </Fill>
  );
};
