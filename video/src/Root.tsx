import { Composition } from "remotion";
import { LaithVideo } from "./laith/LaithVideo";
import { DURATION, FPS, HEIGHT, WIDTH } from "./laith/theme";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      // Render with: npx remotion render LaithRescue out/laith.mp4
      id="LaithRescue"
      component={LaithVideo}
      durationInFrames={DURATION}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  );
};
