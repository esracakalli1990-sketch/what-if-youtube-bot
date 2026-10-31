import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {SERIF, SANS} from './fonts';
import {GOLD, IVORY, ease, clamp, trUpper} from './theme';

// Harita üzerinde ordu/rota hareketleri. Koordinatlar 0–1 arası (görsel oranı).
export type Arrow = {points: [number, number][]; color: string; start: number; duration: number; label?: string};
export type Marker = {x: number; y: number; label: string; start: number};
export type MapMovesProps = {
  image: string;
  title: string;
  subtitle: string;
  arrows: Arrow[];
  markers: Marker[];
  zoom: [number, number];
  focus: [number, number];
  durationSec: number;
};

const W = 2560;
const H = 1440;

const pathD = (pts: [number, number][]) =>
  pts.map(([x, y], i) => `${i ? 'L' : 'M'} ${x * W} ${y * H}`).join(' ');

const pathLength = (pts: [number, number][]) =>
  pts.slice(1).reduce((s, [x, y], i) => s + Math.hypot((x - pts[i][0]) * W, (y - pts[i][1]) * H), 0);

const ArrowPath: React.FC<{arrow: Arrow}> = ({arrow}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const len = pathLength(arrow.points);
  const p = interpolate(frame, [arrow.start * fps, (arrow.start + arrow.duration) * fps], [0, 1], {...clamp, easing: ease});
  const [ex, ey] = arrow.points[arrow.points.length - 1];
  const [px, py] = arrow.points[arrow.points.length - 2] ?? arrow.points[0];
  const [sx, sy] = arrow.points[0];
  const angle = (Math.atan2((ey - py) * H, (ex - px) * W) * 180) / Math.PI;
  return (
    <g opacity={p > 0 ? 1 : 0}>
      <path d={pathD(arrow.points)} fill="none" stroke="rgba(0,0,0,0.55)" strokeWidth={22}
        strokeLinecap="round" strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
      <path d={pathD(arrow.points)} fill="none" stroke={arrow.color} strokeWidth={12}
        strokeLinecap="round" strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
      <polygon points="0,-26 46,0 0,26" fill={arrow.color} opacity={p >= 0.98 ? 1 : 0}
        transform={`translate(${ex * W} ${ey * H}) rotate(${angle})`} />
      {arrow.label ? (
        // Etiket okun başlangıcında: hedefte birleşen oklar etiketleri üst üste bindirmesin
        <text x={sx * W + (sx > 0.7 ? -30 : 30)} y={sy * H - 30} textAnchor={sx > 0.7 ? 'end' : 'start'} fill={IVORY} fontFamily={SANS} fontWeight={600} fontSize={46}
          opacity={interpolate(p, [0, 0.15], [0, 1], clamp)} style={{paintOrder: 'stroke'}}
          stroke="rgba(0,0,0,0.8)" strokeWidth={8}>{arrow.label}</text>
      ) : null}
    </g>
  );
};

const MapMarker: React.FC<{m: Marker}> = ({m}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = interpolate(frame, [m.start * fps, (m.start + 0.6) * fps], [0, 1], clamp);
  const pulse = 1 + 0.25 * Math.sin((frame / fps) * Math.PI * 1.5);
  return (
    <g opacity={a}>
      <circle cx={m.x * W} cy={m.y * H} r={34 * pulse} fill="none" stroke={GOLD} strokeWidth={5} opacity={0.6} />
      <circle cx={m.x * W} cy={m.y * H} r={14} fill={GOLD} stroke="#000" strokeWidth={4} />
      <text x={m.x * W + 34} y={m.y * H + 16} fill={IVORY} fontFamily={SERIF} fontWeight={700} fontSize={54}
        style={{paintOrder: 'stroke'}} stroke="rgba(0,0,0,0.85)" strokeWidth={10}>{trUpper(m.label)}</text>
    </g>
  );
};

// Ordu hareketlerini harita üzerinde çizen sahne (ör. Kadeş Savaşı).
export const MapMoves: React.FC<MapMovesProps> = ({image, title, subtitle, arrows, markers, zoom, focus}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const z = interpolate(frame, [0, durationInFrames], zoom);
  const fade = interpolate(frame, [0, 0.6 * fps, durationInFrames - 0.6 * fps, durationInFrames], [0, 1, 1, 0], clamp);
  return (
    <AbsoluteFill style={{backgroundColor: '#000', opacity: fade}}>
      <AbsoluteFill style={{scale: z, transformOrigin: `${focus[0] * 100}% ${focus[1] * 100}%`}}>
        {image ? (
          <Img src={staticFile(image)} style={{width: '100%', height: '100%', objectFit: 'cover',
            filter: 'sepia(0.45) saturate(0.75) contrast(1.05) brightness(0.8)'}} />
        ) : null}
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: 'absolute', inset: 0}}>
          {arrows.map((a, i) => <ArrowPath key={i} arrow={a} />)}
          {markers.map((m, i) => <MapMarker key={i} m={m} />)}
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{boxShadow: 'inset 0 0 260px rgba(0,0,0,0.9)'}} />
      <AbsoluteFill style={{padding: '90px 110px', justifyContent: 'flex-start'}}>
        <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 72, color: IVORY,
          textShadow: '0 4px 24px rgba(0,0,0,0.9)'}}>{trUpper(title)}</div>
        <div style={{width: 120, height: 4, background: GOLD, margin: '18px 0'}} />
        <div style={{fontFamily: SANS, fontWeight: 400, fontSize: 42, color: IVORY, opacity: 0.85}}>{subtitle}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
