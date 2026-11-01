import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {SERIF, SANS} from './fonts';
import {GOLD, IVORY, trUpper} from './theme';

// Kanal kimliği: "Tarih Dosyaları". Belgesel kapakları ve bölüm kartlarıyla
// aynı dil (Cinzel, altın/fildişi, sıcak ton, koyu kenar).

export type BannerProps = {image: string; title: string; tagline: string};

// YouTube banner'ı 2560×1440; her cihazda görünen güvenli alan ortadaki
// 1546×423 piksel. Yazının tamamı bu alanın içinde kalır.
export const SAFE_W = 1546;
export const SAFE_H = 423;

export const ChannelBanner: React.FC<BannerProps> = ({image, title, tagline}) => (
  <AbsoluteFill style={{backgroundColor: '#0b0907'}}>
    {image ? (
      <Img src={staticFile(image)} style={{width: '100%', height: '100%', objectFit: 'cover',
        filter: 'sepia(0.35) saturate(0.9) contrast(1.08) brightness(0.55)'}} />
    ) : null}
    <AbsoluteFill style={{background: 'radial-gradient(ellipse 60% 45% at 50% 50%, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.75) 100%)'}} />
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <div style={{width: SAFE_W, height: SAFE_H, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center'}}>
        <div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 118, letterSpacing: 10, color: IVORY,
          lineHeight: 1, textShadow: '0 6px 30px rgba(0,0,0,0.9)', whiteSpace: 'nowrap'}}>{trUpper(title)}</div>
        <div style={{display: 'flex', alignItems: 'center', gap: 28, margin: '34px 0 26px'}}>
          <div style={{width: 180, height: 3, background: GOLD}} />
          <div style={{width: 14, height: 14, background: GOLD, transform: 'rotate(45deg)'}} />
          <div style={{width: 180, height: 3, background: GOLD}} />
        </div>
        <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 42, letterSpacing: 2, color: GOLD,
          textShadow: '0 3px 16px rgba(0,0,0,0.9)', whiteSpace: 'nowrap'}}>{tagline}</div>
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);

export type AvatarProps = {image: string; monogram: string; focusX: number; focusY: number};

// Profil resmi: YouTube daire olarak kırpar ve çok küçük gösterir; tek odak
// (Aslanlı Kapı'nın aslanı), altın halka ve kısa monogram.
export const ChannelAvatar: React.FC<AvatarProps> = ({image, monogram, focusX, focusY}) => (
  <AbsoluteFill style={{backgroundColor: '#0b0907'}}>
    {image ? (
      <Img src={staticFile(image)} style={{width: '100%', height: '100%', objectFit: 'cover',
        objectPosition: `${focusX * 100}% ${focusY * 100}%`,
        filter: 'sepia(0.65) saturate(0.85) contrast(1.15) brightness(0.72)'}} />
    ) : null}
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0) 45%, rgba(0,0,0,0.85) 100%)'}} />
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <div style={{width: 740, height: 740, borderRadius: '50%', border: `14px solid ${GOLD}`,
        boxShadow: 'inset 0 0 60px rgba(0,0,0,0.8)'}} />
    </AbsoluteFill>
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 120}}>
      <div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 150, color: IVORY, letterSpacing: 10,
        textShadow: '0 6px 24px rgba(0,0,0,0.95)'}}>{monogram}</div>
    </AbsoluteFill>
  </AbsoluteFill>
);
