import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {SERIF, SANS} from './fonts';
import {GOLD, IVORY, trUpper} from './theme';

export type ThumbnailProps = {image: string; line1: string; line2: string; badge: string; focusX: number};

// Kapak: tek güçlü görsel + 2–3 kelime. Mobilde küçük göründüğü için yazı iri,
// kontrast yüksek; sol taraf koyulaştırılır, görselin odağı sağda kalır.
export const Thumbnail: React.FC<ThumbnailProps> = ({image, line1, line2, badge, focusX}) => (
  <AbsoluteFill style={{backgroundColor: '#000'}}>
    {image ? (
      <Img src={staticFile(image)} style={{width: '100%', height: '100%', objectFit: 'cover',
        objectPosition: `${focusX * 100}% 50%`, filter: 'sepia(0.25) saturate(0.95) contrast(1.12) brightness(0.95)'}} />
    ) : null}
    <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(0,0,0,0.88) 0%, rgba(0,0,0,0.55) 45%, rgba(0,0,0,0) 75%)'}} />
    <AbsoluteFill style={{boxShadow: 'inset 0 0 160px rgba(0,0,0,0.85)'}} />
    <AbsoluteFill style={{justifyContent: 'center', paddingLeft: 70}}>
      {badge ? (
        <div style={{fontFamily: SANS, fontWeight: 700, fontSize: 30, letterSpacing: 8, color: GOLD, marginBottom: 18}}>{badge}</div>
      ) : null}
      <div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 104, lineHeight: 1.0, color: IVORY,
        textShadow: '0 4px 24px rgba(0,0,0,0.9)', maxWidth: 760}}>{trUpper(line1)}</div>
      <div style={{width: 150, height: 6, background: GOLD, margin: '26px 0 22px'}} />
      <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 64, lineHeight: 1.05, color: GOLD,
        textShadow: '0 4px 20px rgba(0,0,0,0.9)', maxWidth: 760}}>{trUpper(line2)}</div>
    </AbsoluteFill>
  </AbsoluteFill>
);
