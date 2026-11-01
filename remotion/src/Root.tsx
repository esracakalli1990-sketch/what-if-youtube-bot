import React from 'react';
import {Composition} from 'remotion';
import {ChapterCard} from './ChapterCard';
import {Thumbnail} from './Thumbnail';
import {MapMoves, MapMovesProps} from './MapMoves';
import {ChannelBanner, ChannelAvatar} from './ChannelArt';

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
  <Composition
    id="MapMoves"
    component={MapMoves}
    durationInFrames={300}
    fps={30}
    width={2560}
    height={1440}
    calculateMetadata={({props}: {props: MapMovesProps}) => ({durationInFrames: Math.round(props.durationSec * 30)})}
    defaultProps={{image: '', title: 'Kadeş', subtitle: 'MÖ 13. yüzyıl · Asi Nehri', arrows: [], markers: [],
      zoom: [1, 1.08], focus: [0.5, 0.5], durationSec: 10} as MapMovesProps}
  />
  <Composition
    id="ChannelBanner"
    component={ChannelBanner}
    durationInFrames={1}
    fps={30}
    width={2560}
    height={1440}
    defaultProps={{image: '', title: 'Tarih Dosyaları', tagline: "Anadolu'dan dünyaya imparatorlukların tam hikâyesi"}}
  />
  <Composition
    id="ChannelAvatar"
    component={ChannelAvatar}
    durationInFrames={1}
    fps={30}
    width={800}
    height={800}
    defaultProps={{image: '', monogram: 'TD', focusX: 0.5, focusY: 0.4}}
  />
  </>
);
