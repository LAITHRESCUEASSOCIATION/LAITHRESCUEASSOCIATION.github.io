import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Icon, IconName } from "../Icons";
import { CUT, clamp, Fill, Particles } from "../kit";
import { TriangleBand } from "../Najran";
import { FONT, NAVY, NAVY_DEEP, T, WHITE } from "../theme";

// One continuous camera move down a column of targets. These are the
// association's proposed targets, so the column opens with "مستهدفاتنا".
// Each number counts up as it scrolls into place, so nothing cuts.

type Stat = { icon: IconName; to: number; label: string; suffix?: string };
const STATS: Stat[] = [
  { icon: "people", to: 1500, label: "متطوع مسجل" },
  { icon: "person", to: 600, label: "متطوع نشط" },
  { icon: "hours", to: 25000, label: "ساعة تطوع" },
  { icon: "heart", to: 10000, label: "مستفيد" },
  { icon: "siren", to: 750, label: "بلاغ نباشره سنويًا" },
  { icon: "book", to: 80, label: "دورة وبرنامج تدريبي" },
  { icon: "shield", to: 2000, label: "مشارك في التدريب" },
  { icon: "link", to: 30, label: "شراكة" },
  { icon: "flag", to: 12, label: "فريقًا ميدانيًا", suffix: "" },
];

const ROW0 = 760;
const GAP = 290;
const RING_Y = ROW0 + STATS.length * GAP + 60;
const END_Y = RING_Y + 1180;
const DUR = 300 + T;
const TRIGGER = 1560; // screen y where a row has fully counted up by

const scrollAt = (frame: number) =>
  interpolate(frame, [CUT + 34, DUR - 20], [0, END_Y - 1920], {
    ...clamp,
    easing: Easing.bezier(0.45, 0, 0.4, 1),
  });

const countAt = (screenY: number) =>
  Easing.out(Easing.cubic)(interpolate(-screenY, [-(TRIGGER + 330), -TRIGGER], [0, 1], clamp));

// Local frames where each row starts counting (for the tick sound).
export const STAT_TICKS: number[] = STATS.map((_, i) => {
  for (let f = 0; f < DUR; f++) {
    if (ROW0 + i * GAP - scrollAt(f) < TRIGGER + 330) return f;
  }
  return DUR;
});

const Row: React.FC<Stat & { y: number; scroll: number }> = ({ icon, to, label, suffix = "+", y, scroll }) => {
  const screenY = y - scroll;
  const p = countAt(screenY);
  return (
    <div style={{ position: "absolute", top: y, left: 90, width: 900, opacity: 0.25 + 0.75 * p }}>
      <div style={{ display: "flex", flexDirection: "row-reverse", alignItems: "center", gap: 40 }}>
        <Icon name={icon} size={120} progress={p} stroke={1.5} />
        <div style={{ flex: 1, textAlign: "right" }}>
          <div style={{ fontFamily: FONT, fontSize: 140, fontWeight: 700, color: WHITE, direction: "ltr", lineHeight: 1.05 }}>
            {Math.round(to * p).toLocaleString("en-US")}
            {suffix}
          </div>
          <div style={{ fontFamily: FONT, fontSize: 50, color: WHITE, opacity: 0.85, direction: "rtl" }}>{label}</div>
        </div>
      </div>
      <div style={{ height: 3, background: WHITE, opacity: 0.3, width: `${p * 100}%`, marginLeft: "auto", marginTop: 18 }} />
    </div>
  );
};

const Response: React.FC<{ scroll: number }> = ({ scroll }) => {
  const t = countAt(RING_Y + 300 - scroll);
  const r = 230;
  const c = 2 * Math.PI * r;
  const card = countAt(RING_Y + 760 - scroll);
  return (
    <div style={{ position: "absolute", top: RING_Y, left: 0, width: 1080 }}>
      <div style={{ position: "relative", margin: "0 auto", width: 560, height: 560 }}>
        <svg width={560} height={560} style={{ position: "absolute" }}>
          {Array.from({ length: 60 }).map((_, i) => {
            const a = (i / 60) * Math.PI * 2;
            return (
              <line
                key={i}
                x1={280 + Math.sin(a) * 262}
                y1={280 - Math.cos(a) * 262}
                x2={280 + Math.sin(a) * 274}
                y2={280 - Math.cos(a) * 274}
                stroke={WHITE}
                strokeWidth={3}
                opacity={i / 60 <= t * 0.95 ? 0.9 : 0.2}
              />
            );
          })}
          <circle cx={280} cy={280} r={r} stroke={WHITE} strokeOpacity={0.15} strokeWidth={24} fill="none" />
          <circle
            cx={280}
            cy={280}
            r={r}
            stroke={WHITE}
            strokeWidth={24}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={c * (1 - t * 0.95)}
            transform="rotate(-90 280 280)"
          />
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: FONT,
            fontSize: 170,
            fontWeight: 700,
            color: WHITE,
            direction: "ltr",
          }}
        >
          {Math.round(t * 95)}%
        </div>
      </div>
      <div style={{ fontFamily: FONT, fontSize: 64, fontWeight: 700, color: WHITE, textAlign: "center", direction: "rtl", marginTop: 20 }}>
        نسبة الاستجابة للبلاغات
      </div>
      <div
        style={{
          margin: "60px auto 0",
          width: 900,
          height: 200,
          borderRadius: 100,
          background: WHITE,
          display: "flex",
          flexDirection: "row-reverse",
          alignItems: "center",
          padding: "0 50px",
          gap: 30,
          boxSizing: "border-box",
          opacity: card,
          transform: `scale(${0.85 + 0.15 * card})`,
        }}
      >
        <div style={{ transform: `rotate(${card * 360}deg)` }}>
          <Icon name="clock" size={120} color={NAVY} stroke={1.8} />
        </div>
        <div style={{ fontFamily: FONT, color: NAVY, direction: "rtl" }}>
          <div style={{ fontSize: 80, fontWeight: 700, lineHeight: 1.15 }}>أقل من 10 دقائق</div>
          <div style={{ fontSize: 40 }}>متوسط زمن التعامل الأولي</div>
        </div>
      </div>
    </div>
  );
};

export const StatsScroll: React.FC = () => {
  const frame = useCurrentFrame();
  const scroll = scrollAt(frame);
  const title = interpolate(frame, [CUT, CUT + 24], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const pinned = interpolate(scroll, [380, 520], [0, 1], clamp);
  return (
    <Fill>
      <Particles count={30} opacity={0.35} />
      <AbsoluteFill style={{ transform: `translateY(${-scroll}px)` }}>
        <div
          style={{
            position: "absolute",
            top: 300,
            width: "100%",
            textAlign: "center",
            fontFamily: FONT,
            color: WHITE,
            direction: "rtl",
            opacity: title,
            transform: `translateY(${(1 - title) * 50}px)`,
            filter: `blur(${(1 - title) * 8}px)`,
          }}
        >
          <div style={{ fontSize: 170, fontWeight: 700, lineHeight: 1.3 }}>مستهدفاتنا</div>
          <div style={{ fontSize: 60, opacity: 0.8 }}>أرقام نعمل للوصول إليها</div>
        </div>
        {STATS.map((s, i) => (
          <Row key={s.label} {...s} y={ROW0 + i * GAP} scroll={scroll} />
        ))}
        <Response scroll={scroll} />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, ${NAVY_DEEP} 0%, ${NAVY_DEEP} 15%, ${NAVY_DEEP}00 27%, ${NAVY_DEEP}00 84%, ${NAVY_DEEP} 100%)`,
          opacity: pinned,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 130,
          width: "100%",
          textAlign: "center",
          fontFamily: FONT,
          fontSize: 60,
          color: WHITE,
          opacity: pinned * 0.85,
          direction: "rtl",
        }}
      >
        مستهدفاتنا
      </div>
      <div style={{ opacity: pinned }}>
        <TriangleBand y={235} opacity={0.35} />
      </div>
    </Fill>
  );
};
