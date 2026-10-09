import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Icon, IconName } from "../Icons";
import { TriangleBand } from "../Najran";
import { FONT, WHITE } from "../theme";
import { clamp, RiseText, SmallLogo, useEnter } from "../ui";

// These are the association's proposed targets (مستهدفات), so they are
// labelled as goals on screen and in the voiceover.

const fmt = (n: number) => Math.round(n).toLocaleString("en-US");

const Counter: React.FC<{
  to: number;
  at: number;
  prefix?: string;
  suffix?: string;
  size: number;
}> = ({ to, at, prefix = "", suffix = "", size }) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [at, at + 40], [0, 1], clamp);
  const eased = 1 - Math.pow(1 - t, 3);
  return (
    <div
      style={{
        fontFamily: FONT,
        fontSize: size,
        fontWeight: 900,
        color: WHITE,
        direction: "ltr",
        lineHeight: 1.1,
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {prefix}
      {fmt(to * eased)}
      {suffix}
    </div>
  );
};

const StatCard: React.FC<{
  icon: IconName;
  to: number;
  suffix?: string;
  label: string;
  at: number;
}> = ({ icon, to, suffix = "+", label, at }) => {
  const frame = useCurrentFrame();
  const p = useEnter(at, 15);
  const draw = interpolate(frame, [at, at + 25], [0, 1], clamp);
  return (
    <div
      style={{
        width: 440,
        height: 330,
        borderRadius: 32,
        border: `3px solid rgba(255,255,255,0.55)`,
        background: "rgba(255,255,255,0.06)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        opacity: p,
        transform: `scale(${0.85 + p * 0.15})`,
      }}
    >
      <Icon name={icon} size={72} progress={draw} />
      <Counter to={to} at={at} suffix={suffix} size={92} />
      <div
        style={{
          fontFamily: FONT,
          fontSize: 38,
          color: WHITE,
          opacity: 0.85,
          direction: "rtl",
          textAlign: "center",
          padding: "0 20px",
        }}
      >
        {label}
      </div>
    </div>
  );
};

const Header: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      <SmallLogo />
      <div style={{ position: "absolute", top: 390, width: "100%" }}>
        <RiseText delay={0} size={112} weight={900}>
          مستهدفاتنا
        </RiseText>
        <RiseText delay={10} size={44} weight={400} opacity={0.75}>
          أرقام نعمل للوصول إليها
        </RiseText>
      </div>
      <TriangleBand y={640} progress={interpolate(frame, [5, 60], [0, 1], clamp)} opacity={0.3} />
    </>
  );
};

// Order follows the voiceover: volunteers → hours → beneficiaries.
const FIRST: React.ComponentProps<typeof StatCard>[] = [
  { icon: "people", to: 1500, label: "متطوع مسجل", at: 18 },
  { icon: "person", to: 600, label: "متطوع نشط", at: 50 },
  { icon: "hours", to: 25000, label: "ساعة تطوع", at: 116 },
  { icon: "book", to: 80, label: "دورة وبرنامج تدريبي", at: 150 },
  { icon: "heart", to: 10000, label: "مستفيد", at: 218 },
  { icon: "shield", to: 2000, label: "مشارك في التدريب", at: 250 },
];

export const StatsOne: React.FC = () => (
  <AbsoluteFill>
    <Header />
    <div
      style={{
        position: "absolute",
        top: 730,
        width: "100%",
        display: "flex",
        flexWrap: "wrap",
        flexDirection: "row-reverse",
        justifyContent: "center",
        gap: 34,
        padding: "0 60px",
        boxSizing: "border-box",
      }}
    >
      {FIRST.map((s) => (
        <StatCard key={s.label} {...s} />
      ))}
    </div>
  </AbsoluteFill>
);

const Ring: React.FC<{ at: number }> = ({ at }) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [at, at + 60], [0, 0.95], clamp);
  const eased = 0.95 * (1 - Math.pow(1 - t / 0.95, 3));
  const r = 200;
  const c = 2 * Math.PI * r;
  return (
    <div style={{ position: "relative", width: 480, height: 480 }}>
      <svg width={480} height={480} style={{ position: "absolute" }}>
        <circle cx={240} cy={240} r={r} stroke={WHITE} strokeOpacity={0.15} strokeWidth={26} fill="none" />
        <circle
          cx={240}
          cy={240}
          r={r}
          stroke={WHITE}
          strokeWidth={26}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - eased)}
          transform="rotate(-90 240 240)"
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
          fontSize: 150,
          fontWeight: 900,
          color: WHITE,
          direction: "ltr",
        }}
      >
        {Math.round(eased * 100)}%
      </div>
    </div>
  );
};

const Mini: React.FC<{ to: number; suffix?: string; label: string; at: number; icon: IconName }> = ({
  to,
  suffix = "+",
  label,
  at,
  icon,
}) => {
  const p = useEnter(at, 15);
  return (
    <div
      style={{
        width: 300,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        opacity: p,
        transform: `translateY(${(1 - p) * 40}px)`,
      }}
    >
      <Icon name={icon} size={64} />
      <Counter to={to} at={at} suffix={suffix} size={76} />
      <div style={{ fontFamily: FONT, fontSize: 36, color: WHITE, opacity: 0.85, direction: "rtl", textAlign: "center" }}>
        {label}
      </div>
    </div>
  );
};

export const StatsTwo: React.FC = () => {
  const ring = useEnter(4, 18);
  const clock = useEnter(128, 15);
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Header />
      <div
        style={{
          position: "absolute",
          top: 700,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          opacity: ring,
        }}
      >
        <Ring at={8} />
        <RiseText delay={20} size={52} weight={700}>
          نسبة الاستجابة للبلاغات
        </RiseText>
      </div>
      <div
        style={{
          position: "absolute",
          top: 1330,
          width: "100%",
          display: "flex",
          flexDirection: "row-reverse",
          justifyContent: "center",
          alignItems: "center",
          gap: 30,
          opacity: clock,
          transform: `scale(${0.85 + clock * 0.15})`,
        }}
      >
        <div style={{ transform: `rotate(${interpolate(frame, [128, 230], [0, 360], clamp)}deg)` }}>
          <Icon name="clock" size={120} />
        </div>
        <div style={{ fontFamily: FONT, color: WHITE, direction: "rtl" }}>
          <div style={{ fontSize: 76, fontWeight: 900, lineHeight: 1.2 }}>أقل من 10 دقائق</div>
          <div style={{ fontSize: 38, opacity: 0.8 }}>متوسط زمن التعامل الأولي</div>
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          top: 1560,
          width: "100%",
          display: "flex",
          flexDirection: "row-reverse",
          justifyContent: "center",
          gap: 20,
        }}
      >
        <Mini icon="siren" to={750} label="بلاغ سنويًا" at={160} />
        <Mini icon="flag" to={12} suffix="" label="فريقًا ميدانيًا" at={172} />
        <Mini icon="link" to={30} label="شراكة" at={184} />
      </div>
    </AbsoluteFill>
  );
};
