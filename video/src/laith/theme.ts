export const NAVY = "#024361"; // logo background
export const NAVY_DEEP = "#012d42"; // darker shade of the same navy, for depth
export const WHITE = "#ffffff";

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const DURATION = 60 * FPS;

export const FONT = '"Thmanyah Serif Text", "Amiri", serif';

// The music (tools/audio.py) is 120 BPM: one beat = 15 frames, one bar = 60.
// Every cut below sits on a bar line so picture and music move together.
export const BEAT = 15;
export const T = 24; // transition length, centred on each cut

export type TransitionType =
  | "none"
  | "zoom" // zoom-through: outgoing flies at the camera, incoming settles back from close up
  | "rise" // incoming card rises over the outgoing one (parallax)
  | "slide" // horizontal parallax slide, right-to-left reading order
  | "iris" // soft-edged circle opening from `origin`
  | "fade" // dissolve with focus pull
  | "leak"; // light-leak dissolve (used on the musical drop)

export type ShotSpec = {
  id: string;
  from: number;
  to: number;
  in: TransitionType;
  origin?: string; // iris centre, CSS position
};

export const SHOTS = [
  { id: "najran", from: 0, to: 180, in: "none" },
  { id: "logo", from: 180, to: 300, in: "zoom" },
  { id: "team", from: 300, to: 480, in: "rise" },
  { id: "leader", from: 480, to: 600, in: "iris" },
  { id: "works", from: 600, to: 780, in: "slide" },
  // Opens out of the "إسعاف المصابين" card (bottom-right of the grid).
  { id: "aid", from: 780, to: 900, in: "iris", origin: "72% 69%" },
  { id: "haram", from: 900, to: 1020, in: "slide" },
  { id: "hajj", from: 1020, to: 1140, in: "rise" },
  { id: "stats", from: 1140, to: 1440, in: "zoom" },
  { id: "now", from: 1440, to: 1500, in: "fade" },
  { id: "join", from: 1500, to: 1620, in: "leak" },
  { id: "end", from: 1620, to: 1800, in: "zoom" },
] as const satisfies readonly ShotSpec[];

export type ShotId = (typeof SHOTS)[number]["id"];

// Camera shake only on the drop.
export const IMPACTS = [1500];
