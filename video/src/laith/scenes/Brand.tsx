import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { CUT, clamp, Fill, Logo, MaskWords, Particles, Photo, Rings, Sweep, Track, useLinear, useSnap } from "../kit";
import { NajranSkyline, TriangleBand } from "../Najran";
import { FONT, NAVY, NAVY_DEEP, WHITE } from "../theme";

// 0–6 s: a line of light opens onto the Emara palace in Najran, the camera
// keeps pushing in and carries straight into the logo (zoom-through).
export const NajranOpener: React.FC = () => {
  const frame = useCurrentFrame();
  const line = useLinear(2, 20, Easing.inOut(Easing.cubic));
  const open = useLinear(16, 44, Easing.inOut(Easing.cubic));
  return (
    <Fill color={NAVY_DEEP}>
      <AbsoluteFill style={{ clipPath: `inset(${50 - open * 50}% 0 ${50 - open * 50}% 0)` }}>
        <Photo src="photos/najran-palace.jpg" focus="68% 60%" dur={200} zoom={[1.0, 1.22]} />
        <AbsoluteFill style={{ background: NAVY, mixBlendMode: "color", opacity: 0.3 }} />
        <AbsoluteFill
          style={{
            background: `linear-gradient(180deg, ${NAVY_DEEP}f0 0%, ${NAVY_DEEP}55 34%, transparent 50%, ${NAVY_DEEP}aa 80%, ${NAVY_DEEP} 100%)`,
          }}
        />
        <Particles count={30} opacity={0.4} />
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
      <div style={{ position: "absolute", top: 230, width: "100%", opacity: interpolate(frame, [150, 185], [1, 0], clamp) }}>
        <Track text="من قلب" delay={40} size={70} style={{ opacity: 0.9 }} />
        <MaskWords text="نجران" delay={52} size={280} style={{ marginTop: -30 }} />
        <TriangleBand y={430} progress={useLinear(66, 110)} opacity={0.5} />
      </div>
      <div style={{ position: "absolute", top: 1660, width: "100%" }}>
        <MaskWords text="أرض الأصالة والتاريخ" delay={84} stagger={4} size={62} weight={400} />
      </div>
      <Sweep delay={100} dur={30} />
    </Fill>
  );
};

// Logo reveal behind a light sweep, with radar rings.
export const LogoReveal: React.FC = () => {
  const p = useSnap(CUT, 200, 120);
  const reveal = useLinear(CUT - 4, CUT + 26, Easing.inOut(Easing.cubic));
  return (
    <Fill>
      <Rings y={820} opacity={0.3} />
      <Particles count={30} opacity={0.4} />
      <AbsoluteFill style={{ opacity: 0.9 }}>
        <NajranSkyline baseY={1700} delay={CUT} />
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: 480,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          transform: `scale(${0.85 + 0.15 * p})`,
          clipPath: `inset(0 0 0 ${100 - reveal * 100}%)`,
        }}
      >
        <Logo width={780} />
      </div>
      <Sweep delay={CUT + 34} dur={30} />
    </Fill>
  );
};

// Final card: logo, call to action, site.
export const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const logo = useSnap(CUT, 200, 100);
  const pill = useLinear(CUT + 30, CUT + 50, Easing.out(Easing.back(1.6)));
  const url = useLinear(CUT + 45, CUT + 75);
  const fadeOut = interpolate(frame, [168, 192], [1, 0], clamp);
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
            transform: `scale(${0.8 + 0.2 * logo})`,
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
            opacity: Math.min(1, pill),
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
