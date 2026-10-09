import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { NajranSkyline } from "../Najran";
import { FONT, NAVY, WHITE } from "../theme";
import { clamp, Logo, RiseText, useEnter } from "../ui";

export const Cta: React.FC = () => {
  const frame = useCurrentFrame();
  const call = interpolate(frame, [150, 168], [1, 0], clamp);
  const end = useEnter(162, 16);
  const pill = useEnter(58, 12);
  return (
    <AbsoluteFill>
      <NajranSkyline baseY={1640} delay={0} />
      <div style={{ position: "absolute", top: 380, width: "100%", opacity: call }}>
        <RiseText delay={12} size={210} weight={900}>
          كن ليثًا
        </RiseText>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            marginTop: 30,
            opacity: pill,
            transform: `scale(${0.7 + pill * 0.3})`,
          }}
        >
          <div
            style={{
              background: WHITE,
              color: NAVY,
              fontFamily: FONT,
              fontSize: 72,
              fontWeight: 900,
              padding: "14px 70px 24px",
              borderRadius: 80,
              direction: "rtl",
            }}
          >
            انضم إلينا
          </div>
        </div>
        <div style={{ marginTop: 60 }}>
          <RiseText delay={96} size={64} weight={500}>
            فكل دقيقة قد تنقذ حياة
          </RiseText>
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          top: 330,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          opacity: end,
          transform: `scale(${0.9 + end * 0.1})`,
        }}
      >
        <Logo width={720} />
        <div
          style={{
            marginTop: 40,
            fontFamily: FONT,
            fontSize: 44,
            color: WHITE,
            opacity: 0.9,
            direction: "ltr",
            letterSpacing: 1,
          }}
        >
          laithrescueassociation.github.io
        </div>
      </div>
    </AbsoluteFill>
  );
};
