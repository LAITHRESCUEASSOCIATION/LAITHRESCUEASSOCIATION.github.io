import "./fonts";
import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile } from "remotion";
import { About } from "./scenes/About";
import { Cta } from "./scenes/Cta";
import { Intro } from "./scenes/Intro";
import { StatsOne, StatsTwo } from "./scenes/Stats";
import { Volunteer } from "./scenes/Volunteer";
import { Works } from "./scenes/Works";
import { DURATION, SCENES } from "./theme";
import { Background, SceneFrame } from "./ui";

const COMPONENTS: Record<keyof typeof SCENES, React.FC> = {
  intro: Intro,
  about: About,
  works: Works,
  volunteer: Volunteer,
  stats1: StatsOne,
  stats2: StatsTwo,
  cta: Cta,
};

// Music sits under the voice and swells back up at the very end.
const musicVolume = (f: number) =>
  interpolate(f, [0, 10, DURATION - 150, DURATION - 100], [0, 0.32, 0.32, 0.6], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

export const LaithVideo: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#024361" }}>
    <Background />
    <Audio src={staticFile("audio/music.mp3")} volume={musicVolume} />
    {(Object.keys(SCENES) as (keyof typeof SCENES)[]).map((key) => {
      const s = SCENES[key];
      const Scene = COMPONENTS[key];
      const last = key === "cta";
      return (
        <Sequence key={key} from={s.from} durationInFrames={s.dur} name={key}>
          <SceneFrame dur={last ? s.dur + 20 : s.dur}>
            <Scene />
          </SceneFrame>
          <Sequence from={s.voAt} name={`${key} voice`}>
            <Audio src={staticFile(`audio/${s.vo}.mp3`)} volume={1} />
          </Sequence>
        </Sequence>
      );
    })}
  </AbsoluteFill>
);
