export const NAVY = "#024361"; // logo background
export const NAVY_DEEP = "#012d42"; // darker shade of the same navy, for depth
export const WHITE = "#ffffff";

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const DURATION = 60 * FPS;

export const FONT = '"Thmanyah Serif Text", "Amiri", serif';

// The music (tools/audio.py) is 120 BPM: one beat = 15 frames, one bar = 60.
// Every cut below sits on a bar line so picture and music hit together.
export const BEAT = 15;
export const T = 14; // transition length, centred on each cut

export type TransitionType =
  | "none"
  | "zoom"
  | "push"
  | "pushX"
  | "iris"
  | "wipe"
  | "split"
  | "flash"
  | "glitch";

export const SHOTS = [
  { id: "opener", from: 0, to: 120, in: "none" },
  { id: "team", from: 120, to: 240, in: "flash" },
  { id: "logo", from: 240, to: 360, in: "iris" },
  { id: "about", from: 360, to: 480, in: "push" },
  { id: "rescuer", from: 480, to: 600, in: "flash" },
  { id: "worksTitle", from: 600, to: 660, in: "glitch" },
  { id: "work1", from: 660, to: 720, in: "pushX" },
  { id: "work2", from: 720, to: 780, in: "split" },
  { id: "work3", from: 780, to: 840, in: "iris" },
  { id: "work4", from: 840, to: 900, in: "pushX" },
  { id: "volunteer", from: 900, to: 1020, in: "zoom" },
  { id: "statsTitle", from: 1020, to: 1080, in: "wipe" },
  { id: "statsA", from: 1080, to: 1200, in: "push" },
  { id: "statsB", from: 1200, to: 1320, in: "pushX" },
  { id: "response", from: 1320, to: 1440, in: "zoom" },
  { id: "now", from: 1440, to: 1500, in: "glitch" },
  { id: "join", from: 1500, to: 1620, in: "flash" },
  { id: "end", from: 1620, to: 1800, in: "zoom" },
] as const satisfies readonly {
  id: string;
  from: number;
  to: number;
  in: TransitionType;
}[];

export type ShotId = (typeof SHOTS)[number]["id"];

// Frames where the picture gets a camera shake (impacts in the music / sfx).
export const IMPACTS = [120, 480, 1500, 1620];
