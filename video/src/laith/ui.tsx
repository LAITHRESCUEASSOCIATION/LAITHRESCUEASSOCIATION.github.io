import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONT, NAVY, NAVY_DEEP, WHITE } from "./theme";

export const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export const Background: React.FC = () => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse 90% 70% at 50% 38%, ${NAVY} 0%, ${NAVY} 45%, ${NAVY_DEEP} 100%)`,
    }}
  />
);

// Fades a scene in and out over `edge` frames, with a gentle zoom.
export const SceneFrame: React.FC<{
  dur: number;
  edge?: number;
  children: React.ReactNode;
}> = ({ dur, edge = 10, children }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, edge, dur - edge, dur],
    [0, 1, 1, 0],
    clamp,
  );
  const scale = interpolate(frame, [0, dur], [1.02, 1], clamp);
  return (
    <AbsoluteFill style={{ opacity, transform: `scale(${scale})` }}>
      {children}
    </AbsoluteFill>
  );
};

export const useEnter = (delay: number, damping = 16) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping } });
};

// Arabic text that rises and un-blurs into place.
export const RiseText: React.FC<{
  delay: number;
  size: number;
  weight?: number;
  opacity?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ delay, size, weight = 700, opacity = 1, style, children }) => {
  const p = useEnter(delay);
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: size,
        fontWeight: weight,
        color: WHITE,
        direction: "rtl",
        textAlign: "center",
        lineHeight: 1.35,
        opacity: p * opacity,
        transform: `translateY(${(1 - p) * 40}px)`,
        filter: `blur(${(1 - p) * 8}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

// The logo artwork already sits on the brand navy, so it blends into the frame.
export const Logo: React.FC<{ width: number; style?: React.CSSProperties }> = ({
  width,
  style,
}) => (
  <Img src={staticFile("laith-logo.png")} style={{ width, ...style }} />
);

export const SmallLogo: React.FC = () => {
  const p = useEnter(4);
  return (
    <div
      style={{
        position: "absolute",
        top: 120,
        width: "100%",
        display: "flex",
        justifyContent: "center",
        opacity: p,
      }}
    >
      <Logo width={190} />
    </div>
  );
};

export const Divider: React.FC<{ delay: number; width?: number }> = ({
  delay,
  width = 420,
}) => {
  const p = useEnter(delay, 22);
  return (
    <div
      style={{
        height: 4,
        width: width * p,
        background: WHITE,
        margin: "28px auto",
        borderRadius: 2,
      }}
    />
  );
};
