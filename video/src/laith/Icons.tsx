import React from "react";
import { WHITE } from "./theme";

const ICONS = {
  siren:
    "M6 18h12 M8 18v-5a4 4 0 0 1 8 0v5 M12 3v2 M4.2 6.2l1.4 1.4 M19.8 6.2l-1.4 1.4 M3 21h18",
  search: "M11 4a7 7 0 1 0 0.01 0 M16 16l5 5",
  aid: "M3 8h18v12H3z M9 8V5h6v3 M12 11v6 M9 14h6",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z M8.5 12l2.5 2.5 4.5-5",
  mountain: "M2 20l7-12 4 6 3-4 6 10z",
  wadi: "M2 9c2-2 4-2 6 0s4 2 6 0 4-2 6 0 M2 15c2-2 4-2 6 0s4 2 6 0 4-2 6 0",
  dunes: "M2 19c4-6 8-6 12 0 M10 19c3-4 7-5 12-2 M17 4a2 2 0 1 0 0.01 0",
  clock: "M12 3a9 9 0 1 0 0.01 0 M12 7v5l3.5 2",
  people:
    "M8 5a3 3 0 1 0 0.01 0 M2.5 19a5.5 5.5 0 0 1 11 0 M17 7a2.5 2.5 0 1 0 0.01 0 M14.5 13.5a4.5 4.5 0 0 1 7 3.5",
  person: "M12 4a3.2 3.2 0 1 0 0.01 0 M5.5 20a6.5 6.5 0 0 1 13 0",
  hours: "M7 3h10 M7 21h10 M8 3c0 5 8 5 8 9s-8 4-8 9 M16 3c0 5-8 5-8 9",
  heart:
    "M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z",
  book: "M3 5h7a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H3z M21 5h-7a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h7z",
  link: "M9 7a5 5 0 1 0 0.01 0 M15 7a5 5 0 1 0 0.01 0",
  flag: "M5 21V4 M5 4h12l-2.5 4L17 12H5",
} as const;

export type IconName = keyof typeof ICONS;

export const Icon: React.FC<{
  name: IconName;
  size?: number;
  progress?: number;
  stroke?: number;
  color?: string;
}> = ({ name, size = 96, progress = 1, stroke = 1.6, color = WHITE }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    {ICONS[name].split(" M").map((seg, i) => (
      <path
        key={i}
        d={i === 0 ? seg : `M${seg}`}
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - progress}
      />
    ))}
  </svg>
);
