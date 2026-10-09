import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  random,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONT, NAVY, NAVY_DEEP, T, WHITE } from "./theme";

// Building blocks shared by the scenes: snappy springs, kinetic type,
// photo treatment and finishing layers (grain, vignette, particles).

export const CUT = T / 2; // frame inside a shot where its cut lands

export const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export const useSnap = (delay: number, damping = 200, stiffness = 260) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping, stiffness, mass: 0.6 } });
};

export const useLinear = (a: number, b: number, easing = Easing.out(Easing.cubic)) => {
  const frame = useCurrentFrame();
  return interpolate(frame, [a, b], [0, 1], { ...clamp, easing });
};

export const Fill: React.FC<{ color?: string; children?: React.ReactNode }> = ({
  color = NAVY,
  children,
}) => (
  <AbsoluteFill
    style={{
      background:
        color === NAVY
          ? `radial-gradient(ellipse 100% 75% at 50% 40%, ${NAVY} 0%, ${NAVY} 40%, ${NAVY_DEEP} 100%)`
          : color,
    }}
  >
    {children}
  </AbsoluteFill>
);

type TextProps = {
  size: number;
  weight?: number;
  color?: string;
  style?: React.CSSProperties;
};

const textBase = (size: number, weight: number, color: string): React.CSSProperties => ({
  fontFamily: FONT,
  fontSize: size,
  fontWeight: weight,
  color,
  direction: "rtl",
  lineHeight: 1.45,
  whiteSpace: "nowrap",
});

// Words rise out of an invisible mask one after another.
export const MaskWords: React.FC<
  TextProps & { text: string; delay: number; stagger?: number; out?: number }
> = ({ text, delay, stagger = 4, size, weight = 700, color = WHITE, style, out }) => {
  const frame = useCurrentFrame();
  const words = text.split(" ");
  return (
    <div
      style={{
        display: "flex",
        direction: "rtl",
        justifyContent: "center",
        gap: size * 0.25,
        ...style,
      }}
    >
      {words.map((w, i) => {
        const p = spring({
          frame: frame - delay - i * stagger,
          fps: 30,
          config: { damping: 200, stiffness: 220, mass: 0.6 },
        });
        const o =
          out === undefined
            ? 0
            : interpolate(frame, [out + i * 2, out + i * 2 + 8], [0, 1], {
                ...clamp,
                easing: Easing.in(Easing.cubic),
              });
        return (
          <span key={i} style={{ overflow: "hidden", display: "inline-block", padding: "0 4px" }}>
            <span
              style={{
                ...textBase(size, weight, color),
                display: "inline-block",
                transform: `translateY(${(1 - p) * 110 - o * 110}%)`,
              }}
            >
              {w}
            </span>
          </span>
        );
      })}
    </div>
  );
};

// Text with a white marker bar sweeping across it right-to-left; the text
// flips to navy where the bar covers it.
export const Marker: React.FC<
  TextProps & { text: string; delay: number; sweep?: number }
> = ({ text, delay, sweep = 12, size, weight = 700, style }) => {
  const p = useLinear(delay, delay + sweep, Easing.inOut(Easing.cubic));
  const clip = `inset(0 0 0 ${100 - p * 100}%)`;
  return (
    <div style={{ position: "relative", display: "inline-block", padding: "0 28px", ...style }}>
      <div style={textBase(size, weight, WHITE)}>{text}</div>
      <div style={{ position: "absolute", inset: "12% 0 8% 0", background: WHITE, clipPath: clip }} />
      <div
        style={{
          ...textBase(size, weight, NAVY),
          position: "absolute",
          inset: 0,
          padding: "0 28px",
          clipPath: clip,
        }}
      >
        {text}
      </div>
    </div>
  );
};

// Large text that settles in from a slightly larger scale out of a blur.
export const Punch: React.FC<TextProps & { text: string; delay: number }> = ({
  text,
  delay,
  size,
  weight = 700,
  color = WHITE,
  style,
}) => {
  const p = useLinear(delay, delay + 22, Easing.out(Easing.cubic));
  return (
    <div
      style={{
        ...textBase(size, weight, color),
        textAlign: "center",
        opacity: p,
        transform: `scale(${1.25 - 0.25 * p})`,
        filter: `blur(${(1 - p) * 10}px)`,
        ...style,
      }}
    >
      {text}
    </div>
  );
};

// Letters spread in from wide tracking.
export const Track: React.FC<TextProps & { text: string; delay: number }> = ({
  text,
  delay,
  size,
  weight = 400,
  color = WHITE,
  style,
}) => {
  const p = useLinear(delay, delay + 24);
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: size,
        fontWeight: weight,
        color,
        textAlign: "center",
        letterSpacing: (1 - p) * 40,
        opacity: p,
        ...style,
      }}
    >
      {text}
    </div>
  );
};

export const Logo: React.FC<{ width: number; style?: React.CSSProperties }> = ({ width, style }) => (
  <Img src={staticFile("laith-logo.png")} style={{ width, ...style }} />
);

// Photo with a slow push-in. `focus` is the CSS object-position.
export const Photo: React.FC<{
  src: string;
  focus?: string;
  zoom?: [number, number];
  dur: number;
  style?: React.CSSProperties;
}> = ({ src, focus = "50% 50%", zoom = [1.12, 1], dur, style }) => {
  const frame = useCurrentFrame();
  const s = interpolate(frame, [0, dur], zoom, clamp);
  return (
    <Img
      src={staticFile(src)}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        objectPosition: focus,
        transform: `scale(${s})`,
        transformOrigin: focus,
        ...style,
      }}
    />
  );
};

// Brand grade over a photo: navy tint + darker top and bottom for type.
export const Grade: React.FC<{ strength?: number }> = ({ strength = 1 }) => (
  <>
    <AbsoluteFill style={{ background: NAVY, mixBlendMode: "color", opacity: 0.35 * strength }} />
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, ${NAVY_DEEP}ee 0%, ${NAVY_DEEP}00 32%, ${NAVY_DEEP}00 55%, ${NAVY_DEEP}f2 88%)`,
        opacity: strength,
      }}
    />
  </>
);

export const Particles: React.FC<{ count?: number; opacity?: number }> = ({
  count = 40,
  opacity = 0.5,
}) => {
  const frame = useCurrentFrame();
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      {Array.from({ length: count }).map((_, i) => {
        const x = random(`px${i}`) * 1080 + Math.sin(frame / 40 + i) * 20;
        const speed = 0.4 + random(`ps${i}`) * 1.4;
        const y = (((random(`py${i}`) * 2100 - frame * speed) % 2100) + 2100) % 2100 - 90;
        return (
          <circle
            key={i}
            cx={x}
            cy={y}
            r={1 + random(`pr${i}`) * 3}
            fill={WHITE}
            opacity={opacity * (0.3 + 0.7 * random(`po${i}`))}
          />
        );
      })}
    </svg>
  );
};

export const Rings: React.FC<{ y?: number; opacity?: number }> = ({ y = 960, opacity = 0.25 }) => {
  const frame = useCurrentFrame();
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      {[0, 1, 2, 3].map((i) => {
        const t = ((frame / 70 + i / 4) % 1);
        return (
          <circle
            key={i}
            cx={540}
            cy={y}
            r={120 + t * 700}
            fill="none"
            stroke={WHITE}
            strokeWidth={2}
            opacity={(1 - t) * opacity}
          />
        );
      })}
    </svg>
  );
};

// Light streak that crosses the frame once.
export const Sweep: React.FC<{ delay: number; dur?: number }> = ({ delay, dur = 22 }) => {
  const p = useLinear(delay, delay + dur, Easing.inOut(Easing.quad));
  if (p <= 0 || p >= 1) return null;
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(105deg, transparent ${p * 140 - 30}%, rgba(255,255,255,0.35) ${p * 140 - 15}%, transparent ${p * 140}%)`,
        mixBlendMode: "screen",
        pointerEvents: "none",
      }}
    />
  );
};

export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const x = -Math.floor(random(`gx${frame}`) * 120);
  const y = -Math.floor(random(`gy${frame}`) * 120);
  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity: 0.05, mixBlendMode: "overlay" }}>
      <Img src={staticFile("grain.jpg")} style={{ position: "absolute", left: x, top: y, width: 1200, height: 2040 }} />
    </AbsoluteFill>
  );
};

export const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background: "radial-gradient(ellipse 85% 70% at 50% 50%, transparent 55%, rgba(0,20,32,0.55) 100%)",
    }}
  />
);

export const Counter: React.FC<{
  to: number;
  delay: number;
  dur?: number;
  suffix?: string;
  prefix?: string;
  size: number;
  color?: string;
}> = ({ to, delay, dur = 30, suffix = "+", prefix = "", size, color = WHITE }) => {
  const p = useLinear(delay, delay + dur, Easing.out(Easing.poly(4)));
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: size,
        fontWeight: 700,
        color,
        direction: "ltr",
        lineHeight: 1.05,
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {prefix}
      {Math.round(to * p).toLocaleString("en-US")}
      {suffix}
    </div>
  );
};
