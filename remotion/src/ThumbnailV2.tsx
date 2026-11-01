import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {SANS} from './fonts';
import {trUpper} from './theme';

// Kapak v2 — rakip analizinden çıkan kurallar (Kasım 2026):
// tek büyük odak (gerçek müze eseri), arkasında renkli ışık halesi, sol tarafta
// 2 satır çok iri ve kalın yazı (kalın siyah kenar + gölge), doygun sıcak renkler,
// köşede küçük seri kimliği. Yazı telefonda (168×94) okunacak büyüklükte.
export type ThumbV2Props = {
  subject: string;            // odak görseli (siyah ya da düz zeminli müze fotoğrafı)
  subjectX: number;           // odak merkezinin yatay konumu (0–1)
  subjectY: number;
  subjectH: number;           // odak yüksekliği (kapak yüksekliğine oran, ör. 1.15)
  blend: 'lighten' | 'normal';// siyah zeminli fotoğrafta 'lighten' zemini eritir
  background: string;         // isteğe bağlı arka plan görseli
  bgPosition: string;         // arka planın kadrajı (CSS object-position, ör. '60% 20%')
  glow: string;               // hale rengi
  line1: string;
  line2: string;
  accent: string;             // 2. satır rengi
  tag: string;
};

const stroke = (w: number) => ({
  WebkitTextStroke: `${w}px #000`, paintOrder: 'stroke fill' as const,
  textShadow: '0 8px 0 rgba(0,0,0,0.55), 0 0 40px rgba(0,0,0,0.8)',
});

export const ThumbnailV2: React.FC<ThumbV2Props> = (p) => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse at 70% 50%, #4a3014 0%, #1a1009 75%)', overflow: 'hidden'}}>
    {p.background ? (
      <Img src={staticFile(p.background)} style={{position: 'absolute', width: '100%', height: '100%',
        objectFit: 'cover', objectPosition: p.bgPosition || '50% 50%',
        filter: 'sepia(0.25) saturate(1.4) contrast(1.15) brightness(0.8)'}} />
    ) : null}
    <div style={{position: 'absolute', left: `${p.subjectX * 100 - 30}%`, top: '-10%', width: '60%', height: '120%',
      background: `radial-gradient(circle, ${p.glow} 0%, transparent 65%)`, opacity: 0.95}} />
    {p.subject ? (
      <Img src={staticFile(p.subject)} style={{position: 'absolute', height: `${p.subjectH * 100}%`,
        left: `${p.subjectX * 100}%`, top: `${p.subjectY * 100}%`, transform: 'translate(-50%, -50%)',
        mixBlendMode: p.blend, filter: 'saturate(1.3) contrast(1.12) brightness(1.2)'}} />
    ) : null}
    <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.35) 38%, rgba(0,0,0,0) 58%)'}} />
    <AbsoluteFill style={{boxShadow: 'inset 0 0 100px rgba(0,0,0,0.75)'}} />
    <div style={{position: 'absolute', left: 52, top: 40, fontFamily: SANS, fontWeight: 800, fontSize: 30,
      letterSpacing: 6, color: '#F3ECDD', opacity: 0.9, ...stroke(4)}}>{trUpper(p.tag)}</div>
    <div style={{position: 'absolute', left: 48, bottom: 70, width: 700, fontFamily: SANS, fontWeight: 800}}>
      <div style={{fontSize: 108, lineHeight: 0.98, color: '#FFFFFF', ...stroke(10)}}>{trUpper(p.line1)}</div>
      <div style={{fontSize: 150, lineHeight: 1.0, color: p.accent, ...stroke(12)}}>{trUpper(p.line2)}</div>
    </div>
  </AbsoluteFill>
);
