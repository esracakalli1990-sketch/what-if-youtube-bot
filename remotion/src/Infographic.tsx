import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {SERIF, SANS} from './fonts';
import {GOLD, IVORY, ease, clamp, trUpper} from './theme';

// Belgesel bilgi grafikleri (Discovery tarzı). Tek bileşen, birkaç düzen:
//  rakam   : büyük sayılar sırayla sayarak belirir (ör. "53 GÜN", "60–80 BİN")
//  olcek   : dev bir nesne (top) ile insan siluetinin boy karşılaştırması
//  kesit   : katmanlı yapı kesiti (hendek → dış sur → iç sur)
//  tunel   : yer altı kesiti; tüneller iki yandan ilerler ve karşılaşır
//  zaman   : yatay zaman çizelgesi, olaylar sırayla yanar

export type Stat = {value: number; prefix?: string; suffix?: string; label: string; decimals?: number};
export type Layer = {label: string; height: number; width: number; color?: string; note?: string};
export type TimeEvent = {date: string; text: string};

export type InfographicProps = {
  type: 'rakam' | 'olcek' | 'kesit' | 'tunel' | 'zaman';
  title: string;
  subtitle?: string;
  background?: string;          // public/ altındaki görsel (karartılarak arka plan olur)
  stats?: Stat[];
  object?: {label: string; lengthM: number; caption?: string};   // olcek
  layers?: Layer[];                                               // kesit
  tunnels?: {left: string; right: string; meet?: string};         // tunel
  events?: TimeEvent[];                                           // zaman
  note?: string;
  durationSec: number;
};

const W = 2560;
const H = 1440;

const fmt = (v: number, d = 0) =>
  v.toLocaleString('tr-TR', {minimumFractionDigits: d, maximumFractionDigits: d});

export const Infographic: React.FC<InfographicProps> = (p) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;
  const appear = (start: number, len = 0.6) => interpolate(t, [start, start + len], [0, 1], {...clamp, easing: ease});
  const fadeIn = interpolate(frame, [0, 0.6 * fps], [0, 1], clamp);
  const fadeOut = interpolate(frame, [durationInFrames - 0.6 * fps, durationInFrames], [1, 0], clamp);
  const drift = interpolate(frame, [0, durationInFrames], [1.04, 1.12]);

  return (
    <AbsoluteFill style={{backgroundColor: '#0b0907', opacity: fadeIn * fadeOut, overflow: 'hidden'}}>
      {p.background ? (
        <Img src={staticFile(p.background)} style={{position: 'absolute', width: W, height: H, objectFit: 'cover',
          transform: `scale(${drift})`, filter: 'sepia(0.4) saturate(0.7) brightness(0.32) blur(2px)'}} />
      ) : null}
      {/* ince ızgara: teknik çizim hissi */}
      <svg width={W} height={H} style={{position: 'absolute', opacity: 0.08}}>
        {Array.from({length: 33}, (_, i) => <line key={`v${i}`} x1={i * 80} y1={0} x2={i * 80} y2={H} stroke={GOLD} strokeWidth={1} />)}
        {Array.from({length: 19}, (_, i) => <line key={`h${i}`} x1={0} y1={i * 80} x2={W} y2={i * 80} stroke={GOLD} strokeWidth={1} />)}
      </svg>
      <AbsoluteFill style={{boxShadow: 'inset 0 0 300px rgba(0,0,0,0.9)'}} />

      <div style={{position: 'absolute', left: 140, top: 110, opacity: appear(0.1)}}>
        <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 84, color: IVORY, letterSpacing: 4,
          textShadow: '0 4px 24px rgba(0,0,0,0.9)'}}>{trUpper(p.title)}</div>
        <div style={{width: 140 * appear(0.3, 0.8), height: 6, background: GOLD, margin: '20px 0 18px'}} />
        {p.subtitle ? <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 44, color: GOLD}}>{p.subtitle}</div> : null}
      </div>

      {p.type === 'rakam' ? <Stats {...p} t={t} appear={appear} /> : null}
      {p.type === 'olcek' ? <Scale {...p} t={t} appear={appear} /> : null}
      {p.type === 'kesit' ? <Section {...p} t={t} appear={appear} /> : null}
      {p.type === 'tunel' ? <Tunnel {...p} t={t} appear={appear} /> : null}
      {p.type === 'zaman' ? <Timeline {...p} t={t} appear={appear} /> : null}

      {p.note ? (
        <div style={{position: 'absolute', right: 140, bottom: 80, fontFamily: SANS, fontSize: 32,
          color: 'rgba(243,236,221,0.75)', fontStyle: 'italic', opacity: appear(1.0)}}>{p.note}</div>
      ) : null}
    </AbsoluteFill>
  );
};

type Inner = InfographicProps & {t: number; appear: (s: number, l?: number) => number};

const Stats: React.FC<Inner> = ({stats = [], t, appear}) => {
  const n = Math.max(1, stats.length);
  const colW = (W - 280) / n;
  return (
    <div style={{position: 'absolute', left: 140, top: 560, width: W - 280, display: 'flex'}}>
      {stats.map((s, i) => {
        const st = 0.8 + i * 1.2;
        const k = interpolate(t, [st, st + 1.6], [0, 1], {...clamp, easing: ease});
        return (
          <div key={i} style={{width: colW, textAlign: 'center', opacity: appear(st, 0.5),
            transform: `translateY(${(1 - appear(st, 0.7)) * 40}px)`}}>
            <div style={{fontFamily: SERIF, fontWeight: 800, color: IVORY, lineHeight: 1, whiteSpace: 'nowrap',
              fontSize: Math.min(180, (colW * 1.2) / Math.max(4, `${s.prefix ?? ''}${s.value}${s.suffix ?? ''}`.length)),
              textShadow: '0 6px 30px rgba(0,0,0,0.9)'}}>
              {trUpper(s.prefix ?? '')}{fmt(s.value * k, s.decimals ?? 0)}{trUpper(s.suffix ?? '')}
            </div>
            <div style={{width: 90, height: 5, background: GOLD, margin: '34px auto 26px'}} />
            <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 52, color: GOLD, padding: '0 30px'}}>{s.label}</div>
          </div>
        );
      })}
    </div>
  );
};

// İnsan silueti (1,75 m) ile büyük nesnenin aynı ölçekte çizimi
const Scale: React.FC<Inner> = ({object, t, appear}) => {
  if (!object) return null;
  const pxPerM = 230;
  const len = object.lengthM * pxPerM;
  const x0 = (W - len) / 2 - 120, ground = 1080;
  const k = interpolate(t, [1.6, 3.6], [0, 1], {...clamp, easing: ease});
  const human = 1.75 * pxPerM;
  const r = 150; // namlu yarıçapı (çizim)
  return (
    <svg width={W} height={H} style={{position: 'absolute'}}>
      <line x1={100} y1={ground} x2={W - 100} y2={ground} stroke={GOLD} strokeWidth={3} opacity={0.6} />
      {/* top gövdesi: arka hazne dar, namlu geniş */}
      <g opacity={appear(0.6, 0.8)}>
        <path d={`M ${x0} ${ground - r * 1.3} L ${x0 + len * 0.42} ${ground - r * 1.3} L ${x0 + len * 0.42} ${ground - r * 2.1}
          L ${x0 + len} ${ground - r * 2.1} L ${x0 + len} ${ground} L ${x0 + len * 0.42} ${ground}
          L ${x0 + len * 0.42} ${ground - 0} L ${x0} ${ground} Z`}
          fill="#7a5a2c" stroke={GOLD} strokeWidth={6} />
        {Array.from({length: 6}, (_, i) => (
          <line key={i} x1={x0 + len * (0.12 + i * 0.16)} y1={ground - (i < 3 ? r * 1.3 : r * 2.1)}
            x2={x0 + len * (0.12 + i * 0.16)} y2={ground} stroke="rgba(0,0,0,0.35)" strokeWidth={8} />
        ))}
        <ellipse cx={x0 + len} cy={ground - r * 1.05} rx={26} ry={r * 0.95} fill="#1a1208" stroke={GOLD} strokeWidth={5} />
      </g>
      {/* insan */}
      <g transform={`translate(${x0 + len + 260} ${ground})`} opacity={appear(1.0, 0.6)}>
        <circle cx={0} cy={-human + 34} r={34} fill={IVORY} />
        <rect x={-34} y={-human + 74} width={68} height={human * 0.48} rx={22} fill={IVORY} />
        <rect x={-30} y={-human * 0.42} width={24} height={human * 0.42} rx={10} fill={IVORY} />
        <rect x={6} y={-human * 0.42} width={24} height={human * 0.42} rx={10} fill={IVORY} />
        <text x={0} y={60} textAnchor="middle" fontFamily={SANS} fontWeight={700} fontSize={40} fill={IVORY}>1,75 m</text>
      </g>
      {/* ölçü çizgisi */}
      <g opacity={appear(1.6, 0.4)}>
        <line x1={x0} y1={ground + 90} x2={x0 + len * k} y2={ground + 90} stroke={GOLD} strokeWidth={6} />
        <line x1={x0} y1={ground + 60} x2={x0} y2={ground + 120} stroke={GOLD} strokeWidth={6} />
        {k > 0.98 ? <line x1={x0 + len} y1={ground + 60} x2={x0 + len} y2={ground + 120} stroke={GOLD} strokeWidth={6} /> : null}
        <text x={x0 + len / 2} y={ground + 190} textAnchor="middle" fontFamily={SANS} fontWeight={800} fontSize={100}
          fill={IVORY}>~{fmt(object.lengthM * k, 1)} m</text>
      </g>
      <text x={x0} y={ground - r * 2.1 - 50} fontFamily={SANS} fontWeight={700} fontSize={50} fill={GOLD}
        opacity={appear(0.9)}>{object.label}</text>
      {object.caption ? (
        <text x={W / 2} y={ground + 290} textAnchor="middle" fontFamily={SANS} fontSize={44} fill={IVORY}
          opacity={appear(3.6)}>{object.caption}</text>
      ) : null}
    </svg>
  );
};

// Katman kesiti: soldan sağa sırayla yükselen katmanlar (hendek → duvarlar)
const Section: React.FC<Inner> = ({layers = [], t, appear}) => {
  const ground = 980, scale = 40;
  const total = layers.reduce((s, l) => s + l.width * scale * 2.2 + 60, -60);
  let x = (W - total) / 2;
  return (
    <svg width={W} height={H} style={{position: 'absolute'}}>
      <rect x={0} y={ground} width={W} height={H - ground} fill="#3b2c1b" opacity={0.85} />
      <line x1={0} y1={ground} x2={W} y2={ground} stroke={GOLD} strokeWidth={3} />
      {layers.map((l, i) => {
        const st = 0.8 + i * 1.3;
        const k = interpolate(t, [st, st + 1.0], [0, 1], {...clamp, easing: ease});
        const w = l.width * scale * 2.2, h = Math.abs(l.height) * scale;
        const lx = x;
        x += w + 60;
        const down = l.height < 0; // hendek: zeminin altına
        const y = down ? ground : ground - h * k;
        const hh = h * k;
        return (
          <g key={i} opacity={appear(st, 0.3)}>
            <rect x={lx} y={y} width={w} height={hh} fill={l.color ?? (down ? '#2d5866' : '#b49a6a')}
              stroke={GOLD} strokeWidth={4} />
            {!down ? Array.from({length: Math.max(2, Math.floor(w / 46))}, (_, j) => (
              <rect key={j} x={lx + j * 46 + 6} y={y - 34} width={28} height={34} fill={l.color ?? '#b49a6a'}
                stroke={GOLD} strokeWidth={3} opacity={k} />
            )) : null}
            <text x={lx + w / 2} y={down ? ground + hh + 60 : y - 70} textAnchor="middle" fontFamily={SANS}
              fontWeight={700} fontSize={44} fill={IVORY} opacity={appear(st + 0.8)}>{l.label}</text>
            {l.note ? (
              <text x={lx + w / 2} y={down ? ground + hh + 110 : y - 124} textAnchor="middle" fontFamily={SANS}
                fontSize={36} fill={GOLD} opacity={appear(st + 1.0)}>{l.note}</text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
};

// Yer altı tünel savaşı: soldan saldıran, sağdan karşı tünel, ortada karşılaşma
const Tunnel: React.FC<Inner> = ({tunnels, t, appear}) => {
  const ground = 640, wallX = 1500;
  const kl = interpolate(t, [1.0, 5.0], [0, 1], {...clamp, easing: ease});
  const kr = interpolate(t, [2.5, 5.0], [0, 1], {...clamp, easing: ease});
  const meet = appear(5.0, 0.4);
  const lx = 260 + (wallX - 260 - 120) * kl;
  const rx = wallX + 520 - 420 * kr;
  return (
    <svg width={W} height={H} style={{position: 'absolute'}}>
      <rect x={0} y={ground} width={W} height={H - ground} fill="#4a3621" />
      <rect x={0} y={ground} width={W} height={H - ground} fill="url(#toprak)" opacity={0.4} />
      <defs><pattern id="toprak" width="40" height="40" patternUnits="userSpaceOnUse">
        <circle cx="10" cy="12" r="3" fill="#2a1d10" /><circle cx="30" cy="28" r="2" fill="#6b5236" /></pattern></defs>
      {/* sur */}
      <rect x={wallX} y={ground - 360} width={150} height={360} fill="#b49a6a" stroke={GOLD} strokeWidth={4} />
      {Array.from({length: 3}, (_, j) => <rect key={j} x={wallX + j * 52 + 4} y={ground - 394} width={34} height={34}
        fill="#b49a6a" stroke={GOLD} strokeWidth={3} />)}
      <text x={wallX + 75} y={ground - 420} textAnchor="middle" fontFamily={SANS} fontWeight={700} fontSize={44} fill={IVORY}>SUR</text>
      {/* sol tünel (saldıran) */}
      <path d={`M 260 ${ground} L 260 ${ground + 260} L ${lx} ${ground + 260}`} fill="none" stroke="#120c06"
        strokeWidth={70} strokeLinejoin="round" />
      <circle cx={lx} cy={ground + 260} r={14} fill="#ffb347" opacity={0.6 + 0.4 * Math.sin(t * 9)} />
      <text x={300} y={ground + 380} fontFamily={SANS} fontWeight={700} fontSize={44} fill={IVORY}
        opacity={appear(1.2)}>{tunnels?.left ?? 'Saldıran tünel'}</text>
      {/* sağ tünel (karşı) */}
      <path d={`M ${wallX + 520} ${ground} L ${wallX + 520} ${ground + 260} L ${rx} ${ground + 260}`} fill="none"
        stroke="#120c06" strokeWidth={70} strokeLinejoin="round" opacity={appear(2.5, 0.3)} />
      <circle cx={rx} cy={ground + 260} r={14} fill="#ffb347" opacity={appear(2.5, 0.3) * (0.6 + 0.4 * Math.sin(t * 9 + 1))} />
      <text x={wallX + 560} y={ground + 380} fontFamily={SANS} fontWeight={700} fontSize={44} fill={IVORY}
        opacity={appear(2.7)}>{tunnels?.right ?? 'Karşı tünel'}</text>
      {/* karşılaşma */}
      <g opacity={meet} transform={`translate(${(lx + rx) / 2} ${ground + 260})`}>
        <circle r={70 + 30 * Math.sin(t * 6)} fill="#ff6a2a" opacity={0.5} />
        <path d="M -40 -40 L 40 40 M 40 -40 L -40 40" stroke="#fff4d6" strokeWidth={12} strokeLinecap="round" />
        <text y={-110} textAnchor="middle" fontFamily={SANS} fontWeight={700} fontSize={46} fill={IVORY}>
          {tunnels?.meet ?? 'Yer altında çarpışma'}</text>
      </g>
    </svg>
  );
};

const Timeline: React.FC<Inner> = ({events = [], t, appear}) => {
  const y = 820, x0 = 220, x1 = W - 220;
  const n = Math.max(1, events.length);
  const step = (x1 - x0) / Math.max(1, n - 1);
  const k = interpolate(t, [0.6, 0.6 + n * 1.0], [0, 1], clamp);
  return (
    <svg width={W} height={H} style={{position: 'absolute'}}>
      <line x1={x0} y1={y} x2={x0 + (x1 - x0) * k} y2={y} stroke={GOLD} strokeWidth={8} />
      {events.map((e, i) => {
        const x = x0 + step * i;
        const on = appear(0.6 + i * 1.0, 0.5);
        const up = i % 2 === 0;
        return (
          <g key={i} opacity={on}>
            <circle cx={x} cy={y} r={22} fill={GOLD} stroke="#000" strokeWidth={5} />
            <line x1={x} y1={y} x2={x} y2={up ? y - 110 : y + 110} stroke={GOLD} strokeWidth={3} />
            <text x={x} y={up ? y - 200 : y + 180} textAnchor="middle" fontFamily={SERIF} fontWeight={800}
              fontSize={58} fill={IVORY}>{trUpper(e.date)}</text>
            <text x={x} y={up ? y - 140 : y + 240} textAnchor="middle" fontFamily={SANS} fontWeight={600}
              fontSize={38} fill={GOLD}>{e.text}</text>
          </g>
        );
      })}
    </svg>
  );
};
