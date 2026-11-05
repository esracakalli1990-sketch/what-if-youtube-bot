import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {SERIF, SANS} from './fonts';
import {GOLD, IVORY, ease, clamp, trUpper} from './theme';

// Karakter kartı: solda portre (yavaş yaklaşma + altın çerçeve), sağda ad, rol
// ve kısa bilgiler sırayla belirir. Discovery tarzı "kim kimdir" ekranı.
export type PortraitCardProps = {
  image: string;
  name: string;
  role: string;
  facts: string[];        // en fazla 3 kısa satır
  side?: 'left' | 'right';
  focusY?: number;        // portrenin dikey odak noktası (0–1)
  durationSec: number;
};

const W = 2560;
const H = 1440;

export const PortraitCard: React.FC<PortraitCardProps> = (p) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;
  const appear = (s: number, l = 0.6) => interpolate(t, [s, s + l], [0, 1], {...clamp, easing: ease});
  const fade = interpolate(frame, [0, 0.5 * fps], [0, 1], clamp) *
    interpolate(frame, [durationInFrames - 0.6 * fps, durationInFrames], [1, 0], clamp);
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.1]);
  const left = (p.side ?? 'left') === 'left';
  const imgW = 1100, imgH = 1240, imgX = left ? 170 : W - 170 - imgW, imgY = 100;
  const textX = left ? imgX + imgW + 140 : 170;

  return (
    <AbsoluteFill style={{backgroundColor: '#0b0907', opacity: fade}}>
      {p.image ? (
        <Img src={staticFile(p.image)} style={{position: 'absolute', width: W, height: H, objectFit: 'cover',
          filter: 'blur(40px) brightness(0.25) sepia(0.5)', transform: 'scale(1.2)'}} />
      ) : null}
      <AbsoluteFill style={{boxShadow: 'inset 0 0 320px rgba(0,0,0,0.95)'}} />
      <div style={{position: 'absolute', left: imgX, top: imgY, width: imgW, height: imgH, overflow: 'hidden',
        border: `6px solid ${GOLD}`, boxShadow: '0 30px 90px rgba(0,0,0,0.85)',
        opacity: appear(0.1, 0.8), transform: `translateX(${(1 - appear(0.1, 0.9)) * (left ? -60 : 60)}px)`}}>
        {p.image ? (
          <Img src={staticFile(p.image)} style={{width: '100%', height: '100%', objectFit: 'cover',
            objectPosition: `50% ${(p.focusY ?? 0.3) * 100}%`, transform: `scale(${zoom})`,
            filter: 'sepia(0.2) contrast(1.05)'}} />
        ) : null}
      </div>
      <div style={{position: 'absolute', left: textX, top: 380, width: W - imgW - 480}}>
        <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 44, color: GOLD, letterSpacing: 8,
          opacity: appear(0.6)}}>{trUpper(p.role)}</div>
        <div style={{fontFamily: SERIF, fontWeight: 800, fontSize: 124, color: IVORY, lineHeight: 1.08,
          marginTop: 24, opacity: appear(0.9), textShadow: '0 6px 30px rgba(0,0,0,0.9)'}}>{trUpper(p.name)}</div>
        <div style={{width: 200 * appear(1.2, 0.8), height: 7, background: GOLD, margin: '44px 0 40px'}} />
        {p.facts.slice(0, 3).map((f, i) => (
          <div key={i} style={{fontFamily: SANS, fontWeight: 600, fontSize: 52, color: IVORY, marginBottom: 26,
            opacity: appear(1.6 + i * 0.5), transform: `translateY(${(1 - appear(1.6 + i * 0.5)) * 20}px)`}}>
            <span style={{color: GOLD, marginRight: 22}}>◆</span>{f}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
