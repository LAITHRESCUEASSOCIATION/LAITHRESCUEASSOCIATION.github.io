import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { CUT, clamp, Fill, Logo, MaskWords, Particles, Rings, Sweep, Track, useLinear, useSnap } from "../kit";
import { NajranSkyline, TriangleBand } from "../Najran";
import { FONT, NAVY, NAVY_DEEP, WHITE } from "../theme";

// 0–4 s: a light line opens the frame, then "من قلب نجران".
export const Opener: React.FC = () => {
  const frame = useCurrentFrame();
  const line = useLinear(4, 22, Easing.inOut(Easing.cubic));
  const open = useLinear(18, 34, Easing.inOut(Easing.cubic));
  const push = interpolate(frame, [0, 127], [1, 1.1]);
  return (
    <Fill color={NAVY_DEEP}>
      <AbsoluteFill style={{ transform: `scale(${push})` }}>
        <AbsoluteFill style={{ clipPath: `inset(${50 - open * 50}% 0 ${50 - open * 50}% 0)` }}>
          <Fill />
          <Particles count={50} opacity={0.6} />
          <AbsoluteFill style={{ opacity: 0.35, transform: `translateY(${(1 - open) * 200}px)` }}>
            <NajranSkyline baseY={1700} delay={20} />
          </AbsoluteFill>
        </AbsoluteFill>
        <div
          style={{
            position: "absolute",
            top: 959,
            left: 540 - line * 540,
            width: line * 1080,
            height: 2,
            background: WHITE,
            opacity: 1 - open,
            boxShadow: "0 0 30px 6px rgba(255,255,255,0.6)",
          }}
        />
        <div style={{ position: "absolute", top: 640, width: "100%" }}>
          <Track text="مـن قـلـب" delay={30} size={70} style={{ opacity: 0.85 }} />
          <MaskWords text="نجران" delay={40} size={300} weight={700} style={{ marginTop: -30 }} />
          <TriangleBand y={470} progress={useLinear(56, 90)} opacity={0.45} />
        </div>
      </AbsoluteFill>
      <Sweep delay={70} />
    </Fill>
  );
};

// Logo reveal behind a light sweep, with radar rings.
export const LogoReveal: React.FC = () => {
  const p = useSnap(CUT + 2, 16, 140);
  const reveal = useLinear(CUT + 2, CUT + 26, Easing.inOut(Easing.cubic));
  return (
    <Fill>
      <Rings y={860} opacity={0.3} />
      <Particles count={30} opacity={0.4} />
      <AbsoluteFill style={{ opacity: 0.9 }}>
        <NajranSkyline baseY={1640} delay={CUT} />
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: 520,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          transform: `scale(${0.8 + 0.2 * p})`,
          clipPath: `inset(0 0 0 ${100 - reveal * 100}%)`,
        }}
      >
        <Logo width={780} />
      </div>
      <Sweep delay={CUT + 30} dur={26} />
    </Fill>
  );
};

// Final card: logo, call to action, site.
export const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const logo = useSnap(CUT, 15, 120);
  const pill = useSnap(CUT + 30, 12, 200);
  const url = useLinear(CUT + 45, CUT + 70);
  const fadeOut = interpolate(frame, [168, 187], [1, 0], clamp);
  return (
    <Fill>
      <Rings y={760} opacity={0.18} />
      <Particles count={45} opacity={0.5} />
      <NajranSkyline baseY={1900} delay={CUT + 6} />
      <AbsoluteFill style={{ opacity: fadeOut }}>
        <div
          style={{
            position: "absolute",
            top: 300,
            width: "100%",
            display: "flex",
            justifyContent: "center",
            opacity: logo,
            transform: `scale(${0.7 + 0.3 * logo})`,
          }}
        >
          <Logo width={760} />
        </div>
        <div
          style={{
            position: "absolute",
            top: 1060,
            width: "100%",
            display: "flex",
            justifyContent: "center",
            opacity: pill,
            transform: `scale(${0.6 + 0.4 * pill})`,
          }}
        >
          <div
            style={{
              background: WHITE,
              color: NAVY,
              fontFamily: FONT,
              fontSize: 64,
              fontWeight: 700,
              padding: "6px 80px 18px",
              borderRadius: 80,
              direction: "rtl",
            }}
          >
            انضم إلينا
          </div>
        </div>
        <div
          style={{
            position: "absolute",
            top: 1215,
            width: "100%",
            textAlign: "center",
            fontFamily: FONT,
            fontSize: 40,
            color: WHITE,
            opacity: url * 0.9,
            letterSpacing: (1 - url) * 20 + 1,
          }}
        >
          laithrescueassociation.github.io
        </div>
      </AbsoluteFill>
      <Sweep delay={CUT + 20} dur={30} />
    </Fill>
  );
};
