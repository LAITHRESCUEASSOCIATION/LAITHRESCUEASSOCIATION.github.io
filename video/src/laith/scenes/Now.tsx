import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { CUT, clamp, Fill, Punch } from "../kit";
import { NAVY_DEEP, WHITE } from "../theme";

// Breakdown before the drop: a heartbeat pulse and "والآن.. دورك".
export const Now: React.FC = () => {
  const frame = useCurrentFrame();
  const beat = (f: number) => Math.max(0, 1 - Math.abs(frame - f) / 6);
  const pulse = Math.max(beat(CUT + 2), beat(CUT + 17), beat(CUT + 32), beat(CUT + 40), beat(CUT + 47), beat(CUT + 52));
  const zoom = interpolate(frame, [0, 67], [1, 1.25], clamp);
  return (
    <Fill color={NAVY_DEEP}>
      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
        <svg width={1080} height={1920} style={{ position: "absolute" }}>
          <circle cx={540} cy={960} r={260 + pulse * 60} fill="none" stroke={WHITE} strokeWidth={3} opacity={0.15 + pulse * 0.5} />
          <circle cx={540} cy={960} r={420 + pulse * 90} fill="none" stroke={WHITE} strokeWidth={2} opacity={0.08 + pulse * 0.25} />
        </svg>
        <div style={{ position: "absolute", top: 760, width: "100%" }}>
          <div style={{ opacity: interpolate(frame, [CUT + 24, CUT + 34], [1, 0.35], clamp) }}>
            <Punch text="والآن.." delay={CUT} size={120} weight={400} />
          </div>
          <Punch text="دورك" delay={CUT + 28} size={240} />
        </div>
      </AbsoluteFill>
    </Fill>
  );
};
