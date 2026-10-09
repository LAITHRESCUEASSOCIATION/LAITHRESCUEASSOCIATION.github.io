import React from "react";
import { AbsoluteFill, Easing, interpolate, Sequence, useCurrentFrame } from "remotion";
import { ShotSpec, T, TransitionType } from "./theme";

// Each shot is mounted T/2 frames before its cut and stays T/2 frames after the
// next one, so outgoing and incoming shots overlap and move together. The
// incoming shot's `in` type decides how both halves move. Inside a shot, frame
// T/2 is the cut.

const ease = Easing.bezier(0.65, 0, 0.35, 1);

const progress = (frame: number, at: number) =>
  interpolate(frame, [at - T / 2, at + T / 2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });

const incoming = (type: TransitionType, p: number, origin: string): React.CSSProperties => {
  const k = 1 - p;
  if (k === 0) return {};
  switch (type) {
    case "none":
      return {};
    case "zoom":
      return { transform: `scale(${1.35 - 0.35 * p})`, opacity: Math.min(1, p * 1.4), filter: `blur(${k * 16}px)` };
    case "rise":
      return { transform: `translateY(${k * 1920}px)`, boxShadow: "0 -40px 90px rgba(0,0,0,0.5)" };
    case "slide":
      return { transform: `translateX(${-k * 1080}px)`, boxShadow: "40px 0 90px rgba(0,0,0,0.5)" };
    case "iris": {
      const r = p * 150;
      const mask = `radial-gradient(circle at ${origin}, #000 ${r}%, transparent ${r + 12}%)`;
      return { WebkitMaskImage: mask, maskImage: mask, transform: `scale(${1.08 - 0.08 * p})` };
    }
    case "fade":
      return { opacity: p, filter: `blur(${k * 10}px)`, transform: `scale(${1.04 - 0.04 * p})` };
    case "leak":
      return { opacity: p, transform: `scale(${1.06 - 0.06 * p})`, filter: `brightness(${1 + k * 0.8})` };
  }
};

const outgoing = (type: TransitionType, p: number): React.CSSProperties => {
  if (p === 0) return {};
  switch (type) {
    case "none":
      return {};
    case "zoom":
      return { transform: `scale(${1 + 1.1 * p})`, opacity: 1 - p, filter: `blur(${p * 14}px)` };
    case "rise":
      return { transform: `translateY(${-p * 520}px) scale(${1 - 0.06 * p})`, filter: `brightness(${1 - 0.55 * p})` };
    case "slide":
      return { transform: `translateX(${p * 420}px)`, filter: `brightness(${1 - 0.55 * p})` };
    case "iris":
      return { transform: `scale(${1 + 0.15 * p})`, filter: `brightness(${1 - 0.5 * p})` };
    case "fade":
      return { filter: `blur(${p * 10}px)` };
    case "leak":
      return { transform: `scale(${1 + 0.08 * p})`, filter: `brightness(${1 + p * 1.2})` };
  }
};

export const Shot: React.FC<{
  spec: ShotSpec;
  next: ShotSpec | null;
  children: React.ReactNode;
}> = ({ spec, next, children }) => {
  const start = Math.max(0, spec.from - T / 2);
  const end = next ? spec.to + T / 2 : spec.to;
  return (
    <Sequence from={start} durationInFrames={end - start} name={spec.id}>
      <ShotBody spec={spec} next={next} start={start}>
        {children}
      </ShotBody>
    </Sequence>
  );
};

const ShotBody: React.FC<{
  spec: ShotSpec;
  next: ShotSpec | null;
  start: number;
  children: React.ReactNode;
}> = ({ spec, next, start, children }) => {
  const abs = useCurrentFrame() + start;
  const pIn = spec.in === "none" ? 1 : progress(abs, spec.from);
  const pOut = next ? progress(abs, spec.to) : 0;
  return (
    <AbsoluteFill style={incoming(spec.in, pIn, spec.origin ?? "50% 50%")}>
      <AbsoluteFill style={next ? outgoing(next.in, pOut) : {}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};
