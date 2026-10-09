import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { CUT, clamp, Marker, MaskWords, Photo, Punch, Sweep, useLinear } from "../kit";
import { FONT, NAVY, NAVY_DEEP, T, WHITE } from "../theme";

// Real photos of Laith volunteers. Landscape photos play as a cinematic band
// over a blurred, graded copy of themselves; portrait photos fill the frame.

const Band: React.FC<{ src: string; focus: string; top: number; height: number; dur: number }> = ({
  src,
  focus,
  top,
  height,
  dur,
}) => {
  const frame = useCurrentFrame();
  const open = interpolate(frame, [CUT - 4, CUT + 18], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  return (
    <>
      <AbsoluteFill>
        <Photo src={src} focus={focus} dur={dur} zoom={[1.3, 1.12]} style={{ filter: "blur(30px) brightness(0.5)" }} />
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
        <Photo src={src} focus={focus} dur={dur} zoom={[1.2, 1.02]} />
        <AbsoluteFill style={{ background: NAVY, mixBlendMode: "color", opacity: 0.22 }} />
      </div>
      <div style={{ position: "absolute", top: top - 3, height: 3, width: 1080 * open, right: 0, background: WHITE }} />
      <div style={{ position: "absolute", top: top + height, height: 3, width: 1080 * open, left: 0, background: WHITE }} />
    </>
  );
};

const Full: React.FC<{ src: string; focus: string; dur: number; zoom?: [number, number]; text: "top" | "bottom" }> = ({
  src,
  focus,
  dur,
  zoom = [1.04, 1.2],
  text,
}) => (
  <>
    <Photo src={src} focus={focus} dur={dur} zoom={zoom} />
    <AbsoluteFill style={{ background: NAVY, mixBlendMode: "color", opacity: 0.25 }} />
    <AbsoluteFill
      style={{
        background:
          text === "top"
            ? `linear-gradient(180deg, ${NAVY_DEEP}f2 0%, ${NAVY_DEEP}88 26%, transparent 45%)`
            : `linear-gradient(0deg, ${NAVY_DEEP}f5 0%, ${NAVY_DEEP}aa 26%, transparent 48%)`,
      }}
    />
  </>
);

export const TeamPhoto: React.FC = () => (
  <AbsoluteFill style={{ background: NAVY_DEEP }}>
    <Band src="photos/laith-team.jpg" focus="55% 50%" top={620} height={740} dur={180 + T} />
    <div style={{ position: "absolute", top: 150, width: "100%" }}>
      <MaskWords text="جمعية" delay={CUT + 6} size={170} />
      <div style={{ display: "flex", justifyContent: "center", marginTop: -40 }}>
        <Marker text="تطوعية" delay={CUT + 26} sweep={16} size={150} />
      </div>
    </div>
    <div style={{ position: "absolute", top: 1420, width: "100%" }}>
      <MaskWords text="في الصفوف الأولى" delay={CUT + 50} stagger={4} size={76} weight={400} />
      <MaskWords text="لنجدة الإنسان" delay={CUT + 66} stagger={4} size={96} />
    </div>
    <Sweep delay={CUT + 110} dur={30} />
  </AbsoluteFill>
);

export const LeaderPhoto: React.FC = () => (
  <AbsoluteFill style={{ background: NAVY_DEEP }}>
    <Full src="photos/laith-leader.jpg" focus="50% 60%" dur={120 + T} zoom={[1.16, 1.02]} text="top" />
    <div style={{ position: "absolute", top: 190, width: "100%" }}>
      <Punch text="سريعون.." delay={CUT + 2} size={170} />
      <div style={{ display: "flex", justifyContent: "center", marginTop: 10 }}>
        <Marker text="لأجل الإنسانية" delay={CUT + 26} sweep={16} size={92} />
      </div>
    </div>
  </AbsoluteFill>
);

const Caption: React.FC<{ title: string; sub: string; top: number }> = ({ title, sub, top }) => {
  const bar = useLinear(CUT + 4, CUT + 24, Easing.inOut(Easing.cubic));
  return (
    <div style={{ position: "absolute", top, width: "100%" }}>
      <div style={{ width: 140 * bar, height: 5, background: WHITE, margin: "0 auto 18px", borderRadius: 3 }} />
      <MaskWords text={title} delay={CUT + 8} stagger={4} size={112} />
      <MaskWords text={sub} delay={CUT + 22} stagger={3} size={56} weight={400} style={{ opacity: 0.9 }} />
    </div>
  );
};

export const AidPhoto: React.FC = () => (
  <AbsoluteFill style={{ background: NAVY_DEEP }}>
    <Full src="photos/laith-aid.jpg" focus="50% 40%" dur={120 + T} text="bottom" />
    <Caption title="إسعاف المصابين" sub="إسعافات أولية في موقع الحدث" top={1430} />
  </AbsoluteFill>
);

export const HaramPhoto: React.FC = () => (
  <AbsoluteFill style={{ background: NAVY_DEEP }}>
    <Full src="photos/laith-haram.jpg" focus="40% 35%" dur={120 + T} zoom={[1.18, 1.04]} text="bottom" />
    <Caption title="مسعفون متطوعون" sub="في خدمة ضيوف الرحمن" top={1430} />
  </AbsoluteFill>
);

export const HajjPhoto: React.FC = () => (
  <AbsoluteFill style={{ background: NAVY_DEEP }}>
    <Band src="photos/laith-hajj.jpg" focus="38% 50%" top={560} height={800} dur={120 + T} />
    <div style={{ position: "absolute", top: 200, width: "100%" }}>
      <MaskWords text="التطوع" delay={CUT + 6} size={150} />
      <div style={{ display: "flex", justifyContent: "center", marginTop: -40 }}>
        <Marker text="رسالة" delay={CUT + 24} sweep={14} size={130} />
      </div>
    </div>
    <div style={{ position: "absolute", top: 1440, width: "100%" }}>
      <MaskWords text="لكل من يحمل روح العطاء" delay={CUT + 40} stagger={4} size={70} weight={400} />
    </div>
  </AbsoluteFill>
);

export const JoinPhoto: React.FC = () => {
  const pill = useLinear(CUT + 30, CUT + 50, Easing.out(Easing.back(1.6)));
  return (
    <AbsoluteFill style={{ background: NAVY_DEEP }}>
      <Band src="photos/laith-team.jpg" focus="100% 50%" top={470} height={760} dur={120 + T} />
      <div style={{ position: "absolute", top: 160, width: "100%" }}>
        <Punch text="كن ليثًا" delay={CUT} size={230} />
      </div>
      <div
        style={{
          position: "absolute",
          top: 1330,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          opacity: Math.min(1, pill),
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
