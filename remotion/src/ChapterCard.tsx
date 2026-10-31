import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {SERIF, SANS} from './fonts';
import {GOLD, IVORY, SAND, ease, clamp, trUpper} from './theme';

export type ChapterCardProps = {kicker: string; title: string; date: string; image: string};

// Bölüm başlık kartı: kararmış arka plan görseli + açılan başlık.
export const ChapterCard: React.FC<ChapterCardProps> = ({kicker, title, date, image}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const out = interpolate(frame, [durationInFrames - 0.8 * fps, durationInFrames], [1, 0], clamp);
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {image ? (
        <AbsoluteFill style={{opacity: 0.45 * out, scale: interpolate(frame, [0, durationInFrames], [1.08, 1])}}>
          <Img src={staticFile(image)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'sepia(0.35) saturate(0.8) blur(2px)'}} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.85) 80%)'}} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: out}}>
        <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 44, color: GOLD,
          letterSpacing: interpolate(frame, [0, 1.5 * fps], [4, 22], {...clamp, easing: ease}),
          opacity: interpolate(frame, [0, 0.8 * fps], [0, 1], clamp)}}>{kicker}</div>
        <div style={{height: 3, background: GOLD, margin: '36px 0',
          width: interpolate(frame, [0.4 * fps, 1.6 * fps], [0, 520], {...clamp, easing: ease})}} />
        <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 150, color: IVORY, textAlign: 'center',
          textShadow: '0 6px 40px rgba(0,0,0,0.8)', padding: '0 160px',
          opacity: interpolate(frame, [0.6 * fps, 1.6 * fps], [0, 1], clamp),
          translate: interpolate(frame, [0.6 * fps, 1.8 * fps], ['0px 40px', '0px 0px'], {...clamp, easing: ease})}}>{trUpper(title)}</div>
        <div style={{fontFamily: SANS, fontWeight: 300, fontSize: 48, color: SAND, marginTop: 40,
          opacity: interpolate(frame, [1.4 * fps, 2.2 * fps], [0, 0.9], clamp)}}>{date}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
