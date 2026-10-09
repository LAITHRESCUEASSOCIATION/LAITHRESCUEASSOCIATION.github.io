import "./fonts";
import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { Grain, Vignette } from "./kit";
import { About } from "./scenes/About";
import { EndCard, LogoReveal, Opener } from "./scenes/Brand";
import { Now } from "./scenes/Now";
import { JoinPhoto, RescuerPhoto, TeamPhoto } from "./scenes/Photos";
import { Response, StatsA, StatsB, StatsTitle } from "./scenes/Stats";
import { Volunteer } from "./scenes/Volunteer";
import { WorkCard, WorksTitle } from "./scenes/Works";
import { IMPACTS, NAVY, SHOTS, ShotId, TransitionType, WHITE } from "./theme";
import { Shot } from "./transitions";

const SCENES: Record<ShotId, React.FC> = {
  opener: Opener,
  team: TeamPhoto,
  logo: LogoReveal,
  about: About,
  rescuer: RescuerPhoto,
  worksTitle: WorksTitle,
  work1: () => <WorkCard index={0} />,
  work2: () => <WorkCard index={1} />,
  work3: () => <WorkCard index={2} />,
  work4: () => <WorkCard index={3} />,
  volunteer: Volunteer,
  statsTitle: StatsTitle,
  statsA: StatsA,
  statsB: StatsB,
  response: Response,
  now: Now,
  join: JoinPhoto,
  end: EndCard,
};

// Sound design: each transition type gets its own effect, timed so the
// loudest part lands on the cut.
type Sfx = "whoosh" | "swish" | "impact" | "glitch" | "shimmer" | "pop" | "tick";
const TRANSITION_SFX: Record<TransitionType, [Sfx, number, number][]> = {
  none: [],
  flash: [["impact", 0, 0.55], ["whoosh", -11, 0.35]],
  zoom: [["whoosh", -11, 0.75]],
  push: [["swish", -5, 0.7]],
  pushX: [["swish", -5, 0.7]],
  wipe: [["swish", -5, 0.7]],
  iris: [["whoosh", -11, 0.6]],
  split: [["whoosh", -11, 0.6], ["pop", 0, 0.5]],
  glitch: [["glitch", -3, 0.6]],
};

const EXTRA_SFX: [Sfx, number, number][] = [
  ["shimmer", 252, 0.6], // logo reveal
  ["shimmer", 1640, 0.7], // end card
  ...[0, 1, 2, 3].map((i): [Sfx, number, number] => ["pop", 660 + i * 60 + 4, 0.45]), // work icons
  ...[0, 1, 2].flatMap((i): [Sfx, number, number][] => [
    ["tick", 1080 + 2 + i * 15, 0.5],
    ["tick", 1200 + 2 + i * 15, 0.5],
  ]),
  ...[0, 1, 2].map((i): [Sfx, number, number] => ["pop", 1320 + 60 + i * 8, 0.4]),
  ["pop", 1320 + 34, 0.5],
  ["pop", 1500 + 34, 0.55],
  ["pop", 1620 + 30, 0.5],
];

const CUES: [Sfx, number, number][] = [
  ...SHOTS.flatMap((s) => TRANSITION_SFX[s.in].map(([n, off, v]): [Sfx, number, number] => [n, s.from + off, v])),
  ...EXTRA_SFX,
];

const FLASHES: number[] = SHOTS.filter((s) => s.in === "flash").map((s) => s.from);

const Flash: React.FC = () => {
  const f = useCurrentFrame();
  const o = Math.max(0, ...FLASHES.map((c) => 1 - Math.abs(f - c) / 7));
  return o > 0 ? <AbsoluteFill style={{ background: WHITE, opacity: o * 0.9 }} /> : null;
};

const Shake: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const f = useCurrentFrame();
  let x = 0;
  let y = 0;
  for (const i of IMPACTS) {
    const t = f - i;
    if (t >= 0 && t < 18) {
      const a = 14 * Math.exp(-t / 4);
      x += Math.sin(t * 2.1) * a;
      y += Math.cos(t * 2.7) * a;
    }
  }
  return <AbsoluteFill style={{ transform: `translate(${x}px, ${y}px) scale(1.02)` }}>{children}</AbsoluteFill>;
};

export const LaithVideo: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: NAVY }}>
    <Shake>
      {SHOTS.map((s, i) => {
        const Scene = SCENES[s.id];
        const next = SHOTS[i + 1];
        return (
          <Shot key={s.id} name={s.id} from={s.from} to={s.to} inType={s.in} outType={next ? next.in : null}>
            <Scene />
          </Shot>
        );
      })}
    </Shake>
    <Flash />
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
