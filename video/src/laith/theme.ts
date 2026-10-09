export const NAVY = "#024361"; // logo background
export const NAVY_DEEP = "#012d42"; // darker shade of the same navy, for depth
export const WHITE = "#ffffff";

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const DURATION = 60 * FPS;

export const FONT = '"Thmanyah Serif Text", "Amiri", serif';

// Scene timeline (frames). `voAt` is the voiceover offset inside the scene.
// The music bed (public/audio/music.mp3) has its transitions on these cuts.
export const SCENES = {
  intro: { from: 0, dur: 210, vo: "vo1", voAt: 15 },
  about: { from: 210, dur: 270, vo: "vo2", voAt: 6 },
  works: { from: 480, dur: 270, vo: "vo3", voAt: 9 },
  volunteer: { from: 750, dur: 250, vo: "vo4", voAt: 6 },
  stats1: { from: 1000, dur: 330, vo: "vo5", voAt: 9 },
  stats2: { from: 1330, dur: 230, vo: "vo6", voAt: 6 },
  cta: { from: 1560, dur: 240, vo: "vo7", voAt: 12 },
} as const;
