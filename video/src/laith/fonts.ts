import { continueRender, delayRender, staticFile } from "remotion";

// Thmanyah Serif Text is not redistributable, so it is not committed.
// Drop the files from Thmanyah's font package into public/fonts/ with these
// names (any of .woff2 / .otf / .ttf). See video/README.md.
// Any weight that is missing falls back to Amiri (OFL, bundled).
const FACES: [family: string, weight: string, name: string][] = [
  ["Thmanyah Serif Text", "400", "ThmanyahSerifText-Regular"],
  ["Thmanyah Serif Text", "500", "ThmanyahSerifText-Medium"],
  ["Thmanyah Serif Text", "700", "ThmanyahSerifText-Bold"],
  ["Thmanyah Serif Text", "900", "ThmanyahSerifText-Black"],
  ["Amiri", "400", "Amiri-Regular"],
  ["Amiri", "700", "Amiri-Bold"],
];
const EXTENSIONS = ["woff2", "otf", "ttf"];

const loadFirstAvailable = async (family: string, weight: string, name: string) => {
  for (const ext of EXTENSIONS) {
    try {
      const face = new FontFace(
        family,
        `url(${staticFile(`fonts/${name}.${ext}`)})`,
        { weight },
      );
      await face.load();
      document.fonts.add(face);
      return true;
    } catch {
      // try the next extension
    }
  }
  return false;
};

const handle = delayRender("Loading fonts");
Promise.all(FACES.map(([f, w, n]) => loadFirstAvailable(f, w, n).then((ok) => ok && f)))
  .then((found) => {
    if (!found.includes("Thmanyah Serif Text")) {
      console.warn("Thmanyah Serif Text not found in public/fonts — using Amiri instead.");
    }
  })
  .finally(() => continueRender(handle));
