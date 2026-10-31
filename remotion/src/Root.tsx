import React from 'react';
import {Composition} from 'remotion';
import {ChapterCard} from './ChapterCard';
import {Thumbnail} from './Thumbnail';

// Belgesel grafik parçaları. Gövde (fotoğraf + Ken Burns) Python render
// motorunda üretilir; burada yalnızca animasyonlu grafik klipleri var.
export const Root: React.FC = () => (
  <>
  <Composition
    id="ChapterCard"
    component={ChapterCard}
    durationInFrames={150}
    fps={30}
    width={2560}
    height={1440}
    defaultProps={{kicker: 'BÖLÜM I', title: "Hattuşa'nın Doğuşu", date: 'MÖ 1650 · Çorum, Anadolu', image: ''}}
  />
  <Composition
    id="Thumbnail"
    component={Thumbnail}
    durationInFrames={1}
    fps={30}
    width={1280}
    height={720}
    defaultProps={{image: '', line1: 'UNUTULAN İMPARATORLUK', line2: 'Hititler', badge: 'TAM HİKÂYE', focusX: 0.6}}
  />
  </>
);
