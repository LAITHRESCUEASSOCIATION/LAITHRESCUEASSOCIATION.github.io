import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { Icon, IconName } from "../Icons";
import { CUT, clamp, Counter, Fill, MaskWords, Particles, Punch, useLinear, useSnap } from "../kit";
import { TriangleBand } from "../Najran";
import { FONT, NAVY, WHITE } from "../theme";

// These are the association's proposed targets, so they sit under
// "مستهدفاتنا" (our targets) rather than being presented as achievements.

const Ticker: React.FC<{ y: number; dir: 1 | -1; text: string }> = ({ y, dir, text }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: "absolute",
        top: y,
        left: -400,
        whiteSpace: "nowrap",
        fontFamily: FONT,
        fontSize: 170,
        fontWeight: 700,
        color: "transparent",
        WebkitTextStroke: `2px ${WHITE}`,
        opacity: 0.16,
        transform: `translateX(${dir * (frame * 9 - 300)}px)`,
      }}
    >
      {text}
    </div>
  );
};

export const StatsTitle: React.FC = () => (
  <Fill>
    <Ticker y={260} dir={1} text="1,500+  600+  25,000+  10,000+" />
    <Ticker y={1430} dir={-1} text="95%  80+  2,000+  30+  12  750+" />
    <div style={{ position: "absolute", top: 720, width: "100%" }}>
      <Punch text="مستهدفاتنا" delay={CUT} size={190} />
      <MaskWords text="أرقام نعمل للوصول إليها" delay={CUT + 14} stagger={3} size={62} weight={400} />
    </div>
  </Fill>
);

type Stat = { icon: IconName; to: number; label: string; suffix?: string };

const Row: React.FC<Stat & { delay: number }> = ({ icon, to, label, suffix = "+", delay }) => {
  const p = useSnap(delay, 18, 200);
  const line = useLinear(delay, delay + 20, Easing.inOut(Easing.cubic));
  return (
    <div style={{ width: 920, margin: "0 auto", opacity: p, transform: `translateX(${(1 - p) * -200}px)` }}>
      <div style={{ display: "flex", flexDirection: "row-reverse", alignItems: "center", gap: 34 }}>
        <Icon name={icon} size={120} progress={line} stroke={1.5} />
        <div style={{ flex: 1, textAlign: "right" }}>
          <Counter to={to} delay={delay} dur={32} suffix={suffix} size={150} />
          <div style={{ fontFamily: FONT, fontSize: 52, color: WHITE, opacity: 0.85, direction: "rtl" }}>{label}</div>
        </div>
      </div>
      <div style={{ height: 3, background: WHITE, opacity: 0.35, width: `${line * 100}%`, marginRight: 0, marginLeft: "auto", marginTop: 20 }} />
    </div>
  );
};

const StatsList: React.FC<{ stats: Stat[] }> = ({ stats }) => (
  <Fill>
    <Particles count={25} opacity={0.35} />
    <div style={{ position: "absolute", top: 210, width: "100%" }}>
      <MaskWords text="مستهدفاتنا" delay={CUT - 4} size={70} weight={400} style={{ opacity: 0.7 }} />
    </div>
    <TriangleBand y={350} progress={useLinear(CUT, CUT + 30)} opacity={0.3} />
    <div style={{ position: "absolute", top: 480, width: "100%", display: "flex", flexDirection: "column", gap: 70 }}>
      {stats.map((s, i) => (
        <Row key={s.label} {...s} delay={CUT + 2 + i * 15} />
      ))}
    </div>
  </Fill>
);

export const StatsA: React.FC = () => (
  <StatsList
    stats={[
      { icon: "people", to: 1500, label: "متطوع مسجل" },
      { icon: "person", to: 600, label: "متطوع نشط" },
      { icon: "hours", to: 25000, label: "ساعة تطوع" },
    ]}
  />
);

export const StatsB: React.FC = () => (
  <StatsList
    stats={[
      { icon: "heart", to: 10000, label: "مستفيد" },
      { icon: "shield", to: 2000, label: "مشارك في التدريب" },
      { icon: "book", to: 80, label: "دورة وبرنامج تدريبي" },
    ]}
  />
);

const Mini: React.FC<Stat & { delay: number }> = ({ icon, to, label, suffix = "+", delay }) => {
  const p = useSnap(delay, 14, 220);
  return (
    <div style={{ width: 300, display: "flex", flexDirection: "column", alignItems: "center", opacity: p, transform: `translateY(${(1 - p) * 60}px)` }}>
      <Icon name={icon} size={70} />
      <Counter to={to} delay={delay} dur={24} suffix={suffix} size={92} />
      <div style={{ fontFamily: FONT, fontSize: 40, color: WHITE, opacity: 0.85, direction: "rtl" }}>{label}</div>
    </div>
  );
};

export const Response: React.FC = () => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [CUT, CUT + 40], [0, 1], { ...clamp, easing: Easing.out(Easing.poly(4)) });
  const r = 230;
  const c = 2 * Math.PI * r;
  const clock = useSnap(CUT + 34, 14, 200);
  return (
    <Fill>
      <Particles count={25} opacity={0.35} />
      <div style={{ position: "absolute", top: 230, left: 540 - 280, width: 560, height: 560 }}>
        <svg width={560} height={560} style={{ position: "absolute" }}>
          {Array.from({ length: 60 }).map((_, i) => {
            const a = (i / 60) * Math.PI * 2;
            const lit = i / 60 <= t * 0.95;
            return (
              <line
                key={i}
                x1={280 + Math.sin(a) * 262}
                y1={280 - Math.cos(a) * 262}
                x2={280 + Math.sin(a) * 274}
                y2={280 - Math.cos(a) * 274}
                stroke={WHITE}
                strokeWidth={3}
                opacity={lit ? 0.9 : 0.2}
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
      <div style={{ position: "absolute", top: 820, width: "100%" }}>
        <MaskWords text="نسبة الاستجابة للبلاغات" delay={CUT + 10} stagger={3} size={64} />
      </div>
      <div
        style={{
          position: "absolute",
          top: 1000,
          left: 90,
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
          opacity: clock,
          transform: `scale(${0.6 + 0.4 * clock})`,
        }}
      >
        <div style={{ transform: `rotate(${interpolate(frame, [CUT + 34, 127], [0, 360], clamp)}deg)` }}>
          <Icon name="clock" size={120} color={NAVY} stroke={1.8} />
        </div>
        <div style={{ fontFamily: FONT, color: NAVY, direction: "rtl" }}>
          <div style={{ fontSize: 80, fontWeight: 700, lineHeight: 1.15 }}>أقل من 10 دقائق</div>
          <div style={{ fontSize: 40 }}>متوسط زمن التعامل الأولي</div>
        </div>
      </div>
      <AbsoluteFill style={{ top: 1330, display: "flex", flexDirection: "row-reverse", justifyContent: "center", gap: 20 }}>
        <Mini icon="siren" to={750} label="بلاغ سنويًا" delay={CUT + 60} />
        <Mini icon="flag" to={12} suffix="" label="فريقًا ميدانيًا" delay={CUT + 68} />
        <Mini icon="link" to={30} label="شراكة" delay={CUT + 76} />
      </AbsoluteFill>
    </Fill>
  );
};
