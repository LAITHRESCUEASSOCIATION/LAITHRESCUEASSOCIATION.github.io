import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  random,
  Sequence,
  useCurrentFrame,
} from "remotion";
import { T, TransitionType, WHITE } from "./theme";

// Each shot is mounted T/2 frames before its cut and stays T/2 frames after the
// next one, so the outgoing and incoming shots overlap. The incoming shot's
// `in` type decides how both halves move. Inside a shot, frame T/2 is the cut.

const ease = Easing.bezier(0.77, 0, 0.18, 1);

const progress = (frame: number, at: number) =>
  interpolate(frame, [at - T / 2, at + T / 2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });

const layerStyle = (
  type: TransitionType,
  p: number,
  dir: "in" | "out",
): React.CSSProperties => {
  const k = dir === "in" ? 1 - p : p; // 0 = settled, 1 = fully off
  if (k === 0 || type === "none") return {};
  const motionBlur = Math.sin(Math.PI * k) * 10;
  switch (type) {
    case "zoom":
      return dir === "in"
        ? { transform: `scale(${0.6 + 0.4 * p})`, opacity: p, filter: `blur(${k * 18}px)` }
        : { transform: `scale(${1 + 1.2 * p})`, opacity: 1 - p, filter: `blur(${k * 18}px)` };
    case "push":
      return {
        transform: `translateY(${dir === "in" ? k * 1920 : -k * 1920}px)`,
        filter: `blur(${motionBlur}px)`,
      };
    case "pushX":
      return {
        transform: `translateX(${dir === "in" ? -k * 1080 : k * 1080}px)`,
        filter: `blur(${motionBlur}px)`,
      };
    case "iris":
      return dir === "in"
        ? { clipPath: `circle(${p * 120}% at 50% 50%)` }
        : { transform: `scale(${1 + 0.12 * p})`, filter: `brightness(${1 - 0.6 * p})` };
    case "wipe": {
      if (dir === "out") return { transform: `translateX(${-p * 160}px)` };
      const top = 100 - p * 140;
      return {
        clipPath: `polygon(${top}% 0, 100% 0, 100% 100%, ${top + 40}% 100%)`,
      };
    }
    case "flash":
      return dir === "in"
        ? { transform: `scale(${1.12 - 0.12 * p})`, opacity: Math.min(1, p * 2) }
        : { transform: `scale(${1 + 0.15 * p})` };
    case "split":
      return dir === "in" ? { transform: `scale(${1.15 - 0.15 * p})` } : {};
    case "glitch":
      return {};
  }
};

const Split: React.FC<{ p: number; children: React.ReactNode }> = ({ p, children }) => (
  <AbsoluteFill style={{ zIndex: 2 }}>
    <AbsoluteFill style={{ clipPath: "inset(0 0 50% 0)", transform: `translateY(${-p * 980}px)` }}>
      {children}
    </AbsoluteFill>
    <AbsoluteFill style={{ clipPath: "inset(50% 0 0 0)", transform: `translateY(${p * 980}px)` }}>
      {children}
    </AbsoluteFill>
    <AbsoluteFill
      style={{
        top: 958,
        height: 4,
        background: WHITE,
        opacity: Math.sin(Math.PI * p) * 0.9,
      }}
    />
  </AbsoluteFill>
);

const BANDS = 7;
const Glitch: React.FC<{ k: number; seed: string; children: React.ReactNode }> = ({
  k,
  seed,
  children,
}) => {
  const frame = useCurrentFrame();
  const step = Math.floor(frame / 2);
  return (
    <AbsoluteFill style={{ opacity: k > 0.85 ? 0 : 1 }}>
      {Array.from({ length: BANDS }).map((_, i) => {
        const top = (i / BANDS) * 100;
        const bottom = 100 - ((i + 1) / BANDS) * 100;
        const dx = (random(`${seed}${i}${step}`) - 0.5) * 260 * k;
        return (
          <AbsoluteFill
            key={i}
            style={{
              clipPath: `inset(${top}% 0 ${bottom}% 0)`,
              transform: `translateX(${dx}px)`,
            }}
          >
            {children}
          </AbsoluteFill>
        );
      })}
      <AbsoluteFill
        style={{
          transform: `translateX(${18 * k}px)`,
          opacity: 0.35 * k,
          mixBlendMode: "screen",
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Shot: React.FC<{
  from: number;
  to: number;
  inType: TransitionType;
  outType: TransitionType | null;
  name: string;
  children: React.ReactNode;
}> = ({ from, to, inType, outType, name, children }) => {
  const start = Math.max(0, from - T / 2);
  const end = outType ? to + T / 2 : to;
  return (
    <Sequence from={start} durationInFrames={end - start} name={name}>
      <ShotBody from={from} to={to} start={start} inType={inType} outType={outType} name={name}>
        {children}
      </ShotBody>
    </Sequence>
  );
};

const ShotBody: React.FC<{
  from: number;
  to: number;
  start: number;
  inType: TransitionType;
  outType: TransitionType | null;
  name: string;
  children: React.ReactNode;
}> = ({ from, to, start, inType, outType, name, children }) => {
  const abs = useCurrentFrame() + start;
  const pIn = inType === "none" ? 1 : progress(abs, from);
  const pOut = outType ? progress(abs, to) : 0;
  const entering = pIn < 1;
  const leaving = pOut > 0;

  let content = <AbsoluteFill>{children}</AbsoluteFill>;
  if (entering && inType === "glitch") {
    content = <Glitch k={1 - pIn} seed={`${name}in`}>{content}</Glitch>;
  }
  if (leaving && outType === "glitch") {
    content = <Glitch k={pOut} seed={`${name}out`}>{content}</Glitch>;
  }
  if (leaving && outType === "split") {
    return <Split p={pOut}>{content}</Split>;
  }
  return (
    <AbsoluteFill style={entering ? layerStyle(inType, pIn, "in") : {}}>
      <AbsoluteFill style={leaving && outType ? layerStyle(outType, pOut, "out") : {}}>
        {content}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
