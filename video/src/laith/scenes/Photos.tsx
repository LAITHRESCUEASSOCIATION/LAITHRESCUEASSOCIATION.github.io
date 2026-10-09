import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { CUT, clamp, Grade, Marker, MaskWords, Photo, Punch, Sweep, useSnap } from "../kit";
import { NAVY, NAVY_DEEP, WHITE, FONT } from "../theme";

// The team photo is landscape, so it plays as a cinematic band over a blurred,
// graded copy of itself that fills the vertical frame.
const Band: React.FC<{ focus: string; top: number; height: number; dur: number }> = ({
  focus,
  top,
  height,
  dur,
}) => {
  const frame = useCurrentFrame();
  const open = interpolate(frame, [CUT - 2, CUT + 12], [0, 1], clamp);
  return (
    <>
      <AbsoluteFill>
        <Photo src="photos/team-najran.jpg" focus={focus} dur={dur} zoom={[1.25, 1.1]} style={{ filter: "blur(28px) brightness(0.55)" }} />
        <AbsoluteFill style={{ background: NAVY, opacity: 0.55 }} />
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top,
          left: 0,
          width: 1080,
          height,
          overflow: "hidden",
          clipPath: `inset(${(1 - open) * 50}% 0 ${(1 - open) * 50}% 0)`,
          boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
        }}
      >
        <Photo src="photos/team-najran.jpg" focus={focus} dur={dur} zoom={[1.18, 1]} />
        <AbsoluteFill style={{ background: NAVY, mixBlendMode: "color", opacity: 0.25 }} />
      </div>
      <div style={{ position: "absolute", top: top - 3, height: 3, width: 1080 * open, right: 0, background: WHITE }} />
      <div style={{ position: "absolute", top: top + height, height: 3, width: 1080 * open, left: 0, background: WHITE }} />
    </>
  );
};

export const TeamPhoto: React.FC = () => (
  <AbsoluteFill style={{ background: NAVY_DEEP }}>
    <Band focus="30% 60%" top={560} height={800} dur={134} />
    <div style={{ position: "absolute", top: 260, width: "100%" }}>
      <MaskWords text="فرق ميدانية" delay={CUT + 4} size={130} />
    </div>
    <div style={{ position: "absolute", top: 1440, width: "100%", display: "flex", justifyContent: "center" }}>
      <MaskWords text="في الجبال والأودية والصحراء" delay={CUT + 16} stagger={3} size={64} weight={400} />
    </div>
    <Sweep delay={CUT + 40} />
  </AbsoluteFill>
);

export const RescuerPhoto: React.FC = () => (
  <AbsoluteFill style={{ background: NAVY_DEEP }}>
    <Photo src="photos/rescuer.jpg" focus="45% 30%" dur={134} zoom={[1.2, 1.04]} />
    <Grade />
    <div style={{ position: "absolute", top: 1290, width: "100%" }}>
      <Punch text="سريعون.." delay={CUT + 2} size={170} />
      <div style={{ display: "flex", justifyContent: "center", marginTop: 10 }}>
        <Marker text="لأجل الإنسانية" delay={CUT + 22} size={92} />
      </div>
    </div>
  </AbsoluteFill>
);

export const JoinPhoto: React.FC = () => {
  const pill = useSnap(CUT + 34, 12, 220);
  return (
    <AbsoluteFill style={{ background: NAVY_DEEP }}>
      <Band focus="95% 50%" top={470} height={760} dur={134} />
      <div style={{ position: "absolute", top: 170, width: "100%" }}>
        <Punch text="كن ليثًا" delay={CUT} size={230} />
      </div>
      <div
        style={{
          position: "absolute",
          top: 1330,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          opacity: pill,
          transform: `scale(${0.5 + 0.5 * pill})`,
        }}
      >
        <div
          style={{
            background: WHITE,
            color: NAVY,
            fontFamily: FONT,
            fontSize: 72,
            fontWeight: 700,
            padding: "6px 80px 20px",
            borderRadius: 90,
            direction: "rtl",
          }}
        >
          انضم إلينا
        </div>
      </div>
      <div style={{ position: "absolute", top: 1510, width: "100%" }}>
        <MaskWords text="فكل دقيقة قد تنقذ حياة" delay={CUT + 50} stagger={3} size={64} weight={400} />
      </div>
      <Sweep delay={CUT + 20} />
    </AbsoluteFill>
  );
};
