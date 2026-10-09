import React from "react";
import { AbsoluteFill, Easing, interpolate, random, spring, useCurrentFrame } from "remotion";
import { Icon } from "../Icons";
import { CUT, clamp, Fill, Marker, MaskWords, Sweep } from "../kit";

// A crowd of volunteers pops in from the centre outward, then the camera
// pulls back as the message lands.
const COLS = 9;
const ROWS = 7;

export const Volunteer: React.FC = () => {
  const frame = useCurrentFrame();
  const pull = interpolate(frame, [CUT, 127], [1.25, 1], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  return (
    <Fill>
      <AbsoluteFill style={{ transform: `scale(${pull})` }}>
        <div
          style={{
            position: "absolute",
            top: 730,
            left: 0,
            width: 1080,
            display: "grid",
            gridTemplateColumns: `repeat(${COLS}, 1fr)`,
            rowGap: 16,
            justifyItems: "center",
          }}
        >
          {Array.from({ length: COLS * ROWS }).map((_, i) => {
            const c = i % COLS;
            const r = Math.floor(i / COLS);
            const dist = Math.hypot(c - (COLS - 1) / 2, r - (ROWS - 1) / 2);
            const delay = CUT + 4 + dist * 5 + random(`v${i}`) * 4;
            const p = spring({ frame: frame - delay, fps: 30, config: { damping: 12, stiffness: 220 } });
            const hero = c === 4 && r === 3;
            return (
              <div key={i} style={{ transform: `scale(${p})`, opacity: hero ? 1 : 0.35 + 0.65 * (1 - dist / 6) }}>
                <Icon name="person" size={hero ? 110 : 84} stroke={hero ? 2.2 : 1.6} />
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, #012d42 0%, #012d42cc 22%, transparent 36%, transparent 70%, #012d42 92%)",
        }}
      />
      <div style={{ position: "absolute", top: 230, width: "100%" }}>
        <MaskWords text="التطوع" delay={CUT + 2} size={190} />
        <div style={{ display: "flex", justifyContent: "center", marginTop: -30 }}>
          <Marker text="رسالة" delay={CUT + 20} size={150} />
        </div>
      </div>
      <div style={{ position: "absolute", top: 1450, width: "100%" }}>
        <MaskWords text="لكل من يحمل روح العطاء" delay={CUT + 50} stagger={3} size={74} weight={400} />
      </div>
      <Sweep delay={CUT + 60} />
    </Fill>
  );
};
