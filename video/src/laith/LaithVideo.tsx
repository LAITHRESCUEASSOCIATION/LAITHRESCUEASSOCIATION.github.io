import "./fonts";
import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { Grain, Vignette } from "./kit";
import { EndCard, LogoReveal, NajranOpener } from "./scenes/Brand";
import { Now } from "./scenes/Now";
import { AidPhoto, HajjPhoto, HaramPhoto, JoinPhoto, LeaderPhoto, TeamPhoto } from "./scenes/Photos";
import { STAT_TICKS, StatsScroll } from "./scenes/Stats";
import { WorksGrid } from "./scenes/Works";
import { IMPACTS, NAVY, SHOTS, ShotId, T, TransitionType, WHITE } from "./theme";
import { Shot } from "./transitions";

const SCENES: Record<ShotId, React.FC> = {
  najran: NajranOpener,
  logo: LogoReveal,
  team: TeamPhoto,
  leader: LeaderPhoto,
  works: WorksGrid,
  aid: AidPhoto,
  haram: HaramPhoto,
  hajj: HajjPhoto,
  stats: StatsScroll,
  now: Now,
  join: JoinPhoto,
  end: EndCard,
};

// Sound design: soft air movement under every transition, timed so its peak
// lands on the cut; a single impact on the musical drop.
type Sfx = "whoosh" | "swish" | "impact" | "shimmer" | "pop" | "tick";
const TRANSITION_SFX: Record<TransitionType, [Sfx, number, number][]> = {
  none: [],
  zoom: [["whoosh", -11, 0.5]],
  rise: [["whoosh", -11, 0.4]],
  slide: [["swish", -5, 0.45]],
  iris: [["whoosh", -11, 0.35], ["shimmer", -6, 0.25]],
  fade: [["swish", -5, 0.25]],
  leak: [["impact", 0, 0.55], ["shimmer", 0, 0.4]],
};

const shotStart = (id: ShotId) => SHOTS.find((s) => s.id === id)!.from - T / 2;

const CUES: [Sfx, number, number][] = [
  ...SHOTS.flatMap((s) => TRANSITION_SFX[s.in].map(([n, off, v]): [Sfx, number, number] => [n, s.from + off, v])),
  ["shimmer", 196, 0.5], // logo reveal
  ["shimmer", 1640, 0.6], // end card
  ...[0, 1, 2, 3].map((i): [Sfx, number, number] => ["pop", shotStart("works") + 7 + 10 + i * 15, 0.3]),
  ...STAT_TICKS.map((f): [Sfx, number, number] => ["tick", shotStart("stats") + f, 0.35]),
  ["pop", shotStart("join") + 7 + 30, 0.4],
  ["pop", 1620 + 30, 0.4],
];

// Light leak that blooms across the frame on "leak" cuts.
const LEAKS: number[] = SHOTS.filter((s) => s.in === "leak").map((s) => s.from);
const Leak: React.FC = () => {
  const f = useCurrentFrame();
  const o = Math.max(0, ...LEAKS.map((c) => 1 - Math.abs(f - c) / 14));
  if (o <= 0) return null;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 70% 50% at ${30 + o * 40}% 45%, ${WHITE} 0%, rgba(255,255,255,0.4) 40%, transparent 75%)`,
        opacity: o * 0.85,
        mixBlendMode: "screen",
      }}
    />
  );
};

const Shake: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const f = useCurrentFrame();
  let x = 0;
  let y = 0;
  for (const i of IMPACTS) {
    const t = f - i;
    if (t >= 0 && t < 20) {
      const a = 9 * Math.exp(-t / 5);
      x += Math.sin(t * 1.7) * a;
      y += Math.cos(t * 2.3) * a;
    }
  }
  return <AbsoluteFill style={{ transform: `translate(${x}px, ${y}px) scale(1.02)` }}>{children}</AbsoluteFill>;
};

export const LaithVideo: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: NAVY }}>
    <Shake>
      {SHOTS.map((s, i) => {
        const Scene = SCENES[s.id];
        return (
          <Shot key={s.id} spec={s} next={SHOTS[i + 1] ?? null}>
            <Scene />
          </Shot>
        );
      })}
    </Shake>
    <Leak />
    <Vignette />
    <Grain />
    <Audio
      src={staticFile("audio/music.mp3")}
      volume={(f) => interpolate(f, [0, 6], [0, 0.6], { extrapolateRight: "clamp" })}
    />
    {CUES.filter(([, at]) => at >= 0).map(([name, at, vol], i) => (
      <Sequence key={i} from={at} durationInFrames={90} name={`sfx ${name}`} layout="none">
        <Audio src={staticFile(`audio/sfx-${name}.mp3`)} volume={vol * 0.8} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
