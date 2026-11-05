import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {SERIF, SANS} from './fonts';
import {GOLD, IVORY, ease, clamp, trUpper} from './theme';

// Coğrafi harita sahnesi (Faz 2). Taban: NASA Blue Marble'dan kırpılmış
// eşdikdörtgen rölyef görüntü; her şey GERÇEK enlem/boylamla yerleştirilir.
// Katmanlar: bölge (sınır, zaman içinde değişir), rota (sefer), birlik (savaş
// blokları), çarpışma, kent, etiket, yıl sayacı; kamera anahtar kareleri.

export type LonLat = [number, number];
export type Bounds = {west: number; east: number; south: number; north: number};
export type Region = {name: string; color: string; poly: LonLat[]; start: number; end?: number; label?: LonLat};
export type Route = {points: LonLat[]; color: string; start: number; duration: number; label?: string; dashed?: boolean; army?: boolean};
export type Unit = {label: string; color: string; path: LonLat[]; start: number; duration: number; labelSide?: 'above' | 'below'};
export type Clash = {at: LonLat; start: number};
export type City = {at: LonLat; label: string; start: number; major?: boolean; side?: 'left' | 'right'};
export type Label = {at: LonLat; text: string; start: number; kind?: 'sea' | 'river' | 'land'};
export type River = {points: LonLat[]; name?: string; start: number; labelAt?: LonLat};
export type Year = {t: number; text: string};
export type CamKey = {t: number; center: LonLat; zoom: number};
// Şehir planı katmanları (İstanbul kuşatması gibi yakın plan sahneler)
export type Land = {poly: LonLat[]; start?: number};
export type Line = {points: LonLat[]; kind: 'wall' | 'chain' | 'bridge' | 'trench'; start: number; duration?: number;
  color?: string; label?: string; labelAt?: LonLat};
export type Convoy = {points: LonLat[]; count: number; start: number; duration: number; spacing?: number;
  color?: string; label?: string};

export type MapStoryProps = {
  image: string;
  bounds: Bounds;
  title: string;
  subtitle: string;
  regions: Region[];
  routes: Route[];
  units: Unit[];
  clashes: Clash[];
  cities: City[];
  labels: Label[];
  rivers: River[];
  years: Year[];
  camera: CamKey[];
  lands?: Land[];       // kara parçaları (parşömen tabanda kıyı çizgisi)
  lines?: Line[];       // sur, zincir, köprü, hendek
  convoys?: Convoy[];   // rota boyunca art arda ilerleyen gemiler
  note: string;          // ör. "Sınırlar yaklaşıktır"
  durationSec: number;
};

const W = 2560;
const H = 1440;

const project = (b: Bounds) => ([lon, lat]: LonLat): [number, number] => [
  ((lon - b.west) / (b.east - b.west)) * W,
  ((b.north - lat) / (b.north - b.south)) * H,
];

const pathLen = (pts: [number, number][]) =>
  pts.slice(1).reduce((s, [x, y], i) => s + Math.hypot(x - pts[i][0], y - pts[i][1]), 0);

const pointAt = (pts: [number, number][], p: number): [number, number] => {
  const total = pathLen(pts);
  let left = total * p;
  for (let i = 1; i < pts.length; i++) {
    const seg = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    if (left <= seg || i === pts.length - 1) {
      const k = seg ? Math.min(1, left / seg) : 1;
      return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k];
    }
    left -= seg;
  }
  return pts[pts.length - 1];
};

// Kamera: anahtar kareler arasında yumuşak geçiş (merkez + yakınlık)
const cameraAt = (keys: CamKey[], t: number, proj: (p: LonLat) => [number, number]) => {
  if (!keys.length) return {cx: W / 2, cy: H / 2, z: 1};
  let a = keys[0], b = keys[keys.length - 1];
  for (let i = 0; i < keys.length - 1; i++) {
    if (t >= keys[i].t && t <= keys[i + 1].t) { a = keys[i]; b = keys[i + 1]; break; }
  }
  const k = a === b ? 1 : interpolate(t, [a.t, b.t], [0, 1], {...clamp, easing: ease});
  const [ax, ay] = proj(a.center), [bx, by] = proj(b.center);
  // yakınlık logaritmik aralanır: uzaklaşma/yakınlaşma eşit hızda hissedilir
  const z = Math.exp(Math.log(a.zoom) + (Math.log(b.zoom) - Math.log(a.zoom)) * k);
  return {cx: ax + (bx - ax) * k, cy: ay + (by - ay) * k, z};
};

export const MapStory: React.FC<MapStoryProps> = (p) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / fps;
  const proj = project(p.bounds);
  const cam = cameraAt(p.camera, t, proj);
  // Görüntü kenarı ekrana girmesin: merkez sınırlandırılır
  const halfW = W / 2 / cam.z, halfH = H / 2 / cam.z;
  const cx = Math.min(W - halfW, Math.max(halfW, cam.cx));
  const cy = Math.min(H - halfH, Math.max(halfH, cam.cy));
  const s = 1 / cam.z; // ekranda sabit boyut için ters ölçek
  const fadeIn = interpolate(frame, [0, 0.8 * fps], [0, 1], clamp);
  const fadeOut = interpolate(frame, [durationInFrames - 0.6 * fps, durationInFrames], [1, 0], clamp);
  const appear = (start: number, len = 0.6) => interpolate(t, [start, start + len], [0, 1], clamp);
  const year = [...p.years].reverse().find((y) => t >= y.t);

  return (
    <AbsoluteFill style={{backgroundColor: '#0c0a08', opacity: fadeIn * fadeOut}}>
      <div style={{position: 'absolute', width: W, height: H, transformOrigin: '0 0',
        transform: `scale(${cam.z}) translate(${W / 2 / cam.z - cx}px, ${H / 2 / cam.z - cy}px)`}}>
        {p.image ? (
          <Img src={staticFile(p.image)} style={{width: W, height: H,
            filter: 'sepia(0.35) saturate(0.85) contrast(1.08) brightness(0.92)'}} />
        ) : (
          // Yakın plan savaş haritası: uydu görüntüsü bu ölçekte bulanık; parşömen zemin
          <svg width={W} height={H}>
            <defs>
              <radialGradient id="parsomen" cx="50%" cy="45%" r="75%">
                <stop offset="0%" stopColor="#cdb68a" /><stop offset="60%" stopColor="#a88b5c" />
                <stop offset="100%" stopColor="#6e5536" />
              </radialGradient>
              <filter id="doku"><feTurbulence type="fractalNoise" baseFrequency="0.0035" numOctaves="5" seed="7" />
                <feColorMatrix values="0 0 0 0 0.35  0 0 0 0 0.26  0 0 0 0 0.15  0 0 0 0.55 0" /></filter>
              <filter id="tane"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" />
                <feColorMatrix values="0 0 0 0 0.3  0 0 0 0 0.22  0 0 0 0 0.12  0 0 0 0.18 0" /></filter>
            </defs>
            <rect width={W} height={H} fill="url(#parsomen)" />
            <rect width={W} height={H} filter="url(#doku)" />
            <rect width={W} height={H} filter="url(#tane)" />
          </svg>
        )}
        <svg width={W} height={H} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
          {(p.lands ?? []).length && !p.image ? (
            <rect x={-W} y={-H} width={3 * W} height={3 * H} fill="#3f6470" opacity={0.5} />
          ) : null}
          {(p.lands ?? []).map((l, i) => {
            const d = l.poly.map((q, j) => `${j ? 'L' : 'M'} ${proj(q).join(' ')}`).join(' ') + ' Z';
            return (
              <g key={`la${i}`} opacity={appear(l.start ?? 0, 0.8)}>
                <path d={d} fill="#d6c08f" stroke="#4a3a26" strokeWidth={7 * s} strokeLinejoin="round" />
                <path d={d} fill="url(#parsomen)" opacity={0.55} />
              </g>
            );
          })}
          {(p.lines ?? []).map((ln, i) => {
            const pts = ln.points.map(proj);
            const len = pathLen(pts);
            const k = interpolate(t, [ln.start, ln.start + (ln.duration ?? 1.5)], [0, 1], {...clamp, easing: ease});
            if (k <= 0) return null;
            const d = pts.map(([x, y], j) => `${j ? 'L' : 'M'} ${x} ${y}`).join(' ');
            const style = {
              wall: {stroke: ln.color ?? '#3a2a1a', w: 22, dash: undefined as string | undefined, under: '#e9dcc0'},
              chain: {stroke: ln.color ?? '#d9d9d9', w: 10, dash: `${16 * s} ${10 * s}`, under: '#1a1a1a'},
              bridge: {stroke: ln.color ?? '#8a5a2b', w: 14, dash: `${6 * s} ${6 * s}`, under: '#2b1a0c'},
              trench: {stroke: ln.color ?? '#6b4b2a', w: 9, dash: `${4 * s} ${8 * s}`, under: 'rgba(0,0,0,0.3)'},
            }[ln.kind];
            const [lx, ly] = ln.labelAt ? proj(ln.labelAt) : pointAt(pts, 0.5);
            return (
              <g key={`ln${i}`}>
                <path d={d} fill="none" stroke={style.under} strokeWidth={(style.w + 10) * s} strokeLinecap="round"
                  strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - k)} opacity={0.8} />
                <path d={d} fill="none" stroke={style.stroke} strokeWidth={style.w * s} strokeLinecap="round"
                  strokeLinejoin="round" mask={`url(#lm${i})`} strokeDasharray={style.dash} />
                {ln.kind === 'wall' ? (
                  <path d={d} fill="none" stroke="#e9dcc0" strokeWidth={5 * s} strokeDasharray={`${10 * s} ${14 * s}`}
                    mask={`url(#lm${i})`} />
                ) : null}
                <mask id={`lm${i}`}><path d={d} fill="none" stroke="#fff" strokeWidth={(style.w + 20) * s}
                  strokeDasharray={len} strokeDashoffset={len * (1 - k)} /></mask>
                {ln.label ? (
                  <text x={lx} y={ly - 30 * s} textAnchor="middle" fontFamily={SANS} fontWeight={700}
                    fontSize={40 * s} fill={IVORY} opacity={Math.min(1, k * 2)} stroke="rgba(0,0,0,0.85)"
                    strokeWidth={8 * s} style={{paintOrder: 'stroke'}}>{ln.label}</text>
                ) : null}
              </g>
            );
          })}
          {p.regions.map((r, i) => {
            const on = appear(r.start, 1.0) * (r.end !== undefined ? 1 - appear(r.end, 1.0) : 1);
            if (on <= 0) return null;
            const d = r.poly.map((q, j) => `${j ? 'L' : 'M'} ${proj(q).join(' ')}`).join(' ') + ' Z';
            const [lx, ly] = proj(r.label ?? r.poly[0]);
            return (
              <g key={`r${i}`} opacity={on}>
                <path d={d} fill={r.color} fillOpacity={0.32} stroke={r.color} strokeWidth={6 * s}
                  strokeLinejoin="round" />
                <text x={lx} y={ly} textAnchor="middle" fontFamily={SERIF} fontWeight={700}
                  fontSize={54 * s} fill={IVORY} stroke="rgba(0,0,0,0.75)" strokeWidth={8 * s}
                  style={{paintOrder: 'stroke'}} letterSpacing={6 * s}>{trUpper(r.name)}</text>
              </g>
            );
          })}
          {p.rivers.map((r, i) => {
            const pts = r.points.map(proj);
            const d = pts.map(([x, y], j) => `${j ? 'L' : 'M'} ${x} ${y}`).join(' ');
            const [lx, ly] = proj(r.labelAt ?? r.points[Math.floor(r.points.length / 2)]);
            return (
              <g key={`rv${i}`} opacity={appear(r.start)}>
                <path d={d} fill="none" stroke="#2f6f8f" strokeWidth={(p.image ? 7 : 16) * s}
                  strokeLinecap="round" strokeLinejoin="round" opacity={0.9} />
                {r.name ? (
                  <text x={lx + 26 * s} y={ly} fontFamily={SERIF} fontStyle="italic" fontSize={40 * s}
                    fill={p.image ? '#bfe3ef' : '#1e4a60'} stroke={p.image ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.35)'}
                    strokeWidth={5 * s} style={{paintOrder: 'stroke'}}>{r.name}</text>
                ) : null}
              </g>
            );
          })}
          {p.labels.map((l, i) => {
            const [x, y] = proj(l.at);
            const water = l.kind === 'sea' || l.kind === 'river';
            return (
              <text key={`l${i}`} x={x} y={y} textAnchor="middle" opacity={appear(l.start) * 0.9}
                fontFamily={SERIF} fontStyle={water ? 'italic' : 'normal'} fontSize={(l.kind === 'sea' ? 46 : 38) * s}
                fill={water ? '#bfe3ef' : IVORY} letterSpacing={(l.kind === 'sea' ? 10 : 3) * s}
                stroke="rgba(0,0,0,0.6)" strokeWidth={6 * s} style={{paintOrder: 'stroke'}}>{l.text}</text>
            );
          })}
          {p.routes.map((r, i) => {
            const pts = r.points.map(proj);
            const len = pathLen(pts);
            const k = interpolate(t, [r.start, r.start + r.duration], [0, 1], {...clamp, easing: ease});
            if (k <= 0) return null;
            const d = pts.map(([x, y], j) => `${j ? 'L' : 'M'} ${x} ${y}`).join(' ');
            const [hx, hy] = pointAt(pts, k);
            const [sx, sy] = pts[0];
            return (
              <g key={`ro${i}`}>
                <path d={d} fill="none" stroke="rgba(0,0,0,0.55)" strokeWidth={20 * s}
                  strokeDasharray={len} strokeDashoffset={len * (1 - k)} strokeLinecap="round" />
                <path d={d} fill="none" stroke={r.color} strokeWidth={11 * s} strokeLinecap="round"
                  strokeDasharray={r.dashed ? `${34 * s} ${22 * s}` : undefined}
                  style={{strokeDashoffset: r.dashed ? -t * 60 * s : undefined}}
                  mask={`url(#m${i})`} />
                <mask id={`m${i}`}><path d={d} fill="none" stroke="#fff" strokeWidth={24 * s}
                  strokeDasharray={len} strokeDashoffset={len * (1 - k)} /></mask>
                {r.army !== false ? (
                  <g transform={`translate(${hx} ${hy}) scale(${s})`}>
                    <circle r={22} fill={r.color} stroke="#000" strokeWidth={5} />
                    <circle r={34} fill="none" stroke={r.color} strokeWidth={4}
                      opacity={0.5 + 0.5 * Math.sin(t * 6)} />
                  </g>
                ) : null}
                {r.label ? (
                  <text x={sx} y={sy - 40 * s} textAnchor="middle" fontFamily={SANS} fontWeight={700}
                    fontSize={46 * s} fill={IVORY} opacity={Math.min(1, k * 4)} stroke="rgba(0,0,0,0.85)"
                    strokeWidth={9 * s} style={{paintOrder: 'stroke'}}>{r.label}</text>
                ) : null}
              </g>
            );
          })}
          {p.units.map((u, i) => {
            const pts = u.path.map(proj);
            const k = interpolate(t, [u.start, u.start + u.duration], [0, 1], {...clamp, easing: ease});
            const show = appear(u.start - 0.4, 0.4);
            if (show <= 0) return null;
            const [x, y] = pointAt(pts, k);
            const [px, py] = pointAt(pts, Math.max(0, k - 0.02));
            const ang = (Math.atan2(y - py, x - px) * 180) / Math.PI;
            return (
              <g key={`u${i}`} opacity={show}>
                <g transform={`translate(${x} ${y}) scale(${s})`}>
                  <rect x={-70} y={-30} width={140} height={60} rx={6} fill={u.color} stroke="#000" strokeWidth={5} />
                  <line x1={-70} y1={-30} x2={70} y2={30} stroke="rgba(0,0,0,0.45)" strokeWidth={4} />
                  <line x1={-70} y1={30} x2={70} y2={-30} stroke="rgba(0,0,0,0.45)" strokeWidth={4} />
                  {k > 0.01 && k < 0.999 ? (
                    <g transform={`rotate(${ang})`}>
                      <polygon points="88,-22 124,0 88,22" fill={u.color} stroke="#000" strokeWidth={4} />
                    </g>
                  ) : null}
                </g>
                <text x={x} y={y + (u.labelSide === 'above' ? -56 : 84) * s} textAnchor="middle" fontFamily={SANS} fontWeight={700}
                  fontSize={40 * s} fill={IVORY} stroke="rgba(0,0,0,0.85)" strokeWidth={8 * s}
                  style={{paintOrder: 'stroke'}}>{u.label}</text>
              </g>
            );
          })}
          {(p.convoys ?? []).map((cv, i) => {
            const pts = cv.points.map(proj);
            const gap = cv.spacing ?? 0.35;
            const [sx, sy] = pts[0];
            return (
              <g key={`cv${i}`}>
                {Array.from({length: cv.count}, (_, j) => {
                  const st = cv.start + j * gap;
                  const k = interpolate(t, [st, st + cv.duration], [0, 1], {...clamp, easing: ease});
                  if (t < st) return null;
                  const [x, y] = pointAt(pts, k);
                  const [px, py] = pointAt(pts, Math.max(0, k - 0.01));
                  const ang = k > 0.005 ? (Math.atan2(y - py, x - px) * 180) / Math.PI : 0;
                  return (
                    <g key={j} transform={`translate(${x} ${y}) rotate(${ang}) scale(${s * 1.6})`}>
                      <path d="M -34 -9 L 24 -9 L 40 0 L 24 9 L -34 9 Z" fill={cv.color ?? '#b5482f'} stroke="#000" strokeWidth={4} />
                      <line x1={-6} y1={0} x2={-6} y2={-30} stroke="#000" strokeWidth={4} />
                      <path d="M -6 -30 L 12 -16 L -6 -10 Z" fill={IVORY} stroke="#000" strokeWidth={2} />
                    </g>
                  );
                })}
                {cv.label ? (
                  <text x={sx} y={sy - 50 * s} textAnchor="middle" fontFamily={SANS} fontWeight={700}
                    fontSize={44 * s} fill={IVORY} opacity={appear(cv.start, 0.5)} stroke="rgba(0,0,0,0.85)"
                    strokeWidth={9 * s} style={{paintOrder: 'stroke'}}>{cv.label}</text>
                ) : null}
              </g>
            );
          })}
          {p.clashes.map((c, i) => {
            const [x, y] = proj(c.at);
            const k = interpolate(t, [c.start, c.start + 1.2], [0, 1], clamp);
            if (k <= 0) return null;
            const pulse = 0.5 + 0.5 * Math.sin((t - c.start) * 8);
            return (
              <g key={`c${i}`} transform={`translate(${x} ${y}) scale(${s})`}>
                <circle r={40 + 120 * k} fill="none" stroke="#ffcf6a" strokeWidth={8} opacity={(1 - k) * 0.9} />
                <circle r={46} fill="#ff6a2a" opacity={0.55 + 0.35 * pulse} />
                <path d="M -34 -34 L 34 34 M 34 -34 L -34 34" stroke="#fff4d6" strokeWidth={10} strokeLinecap="round" />
              </g>
            );
          })}
          {p.cities.map((c, i) => {
            const [x, y] = proj(c.at);
            const a = appear(c.start, 0.5);
            if (a <= 0) return null;
            const pop = interpolate(t, [c.start, c.start + 0.35, c.start + 0.6], [0.3, 1.35, 1], clamp);
            const right = c.side !== 'left';
            return (
              <g key={`ci${i}`} opacity={a}>
                <g transform={`translate(${x} ${y}) scale(${s * pop})`}>
                  <circle r={c.major ? 20 : 13} fill={GOLD} stroke="#000" strokeWidth={5} />
                  {c.major ? <circle r={32} fill="none" stroke={GOLD} strokeWidth={4} /> : null}
                </g>
                <text x={x + (right ? 36 : -36) * s} y={y + 16 * s} textAnchor={right ? 'start' : 'end'}
                  fontFamily={SERIF} fontWeight={700} fontSize={(c.major ? 52 : 42) * s} fill={IVORY}
                  stroke="rgba(0,0,0,0.85)" strokeWidth={9 * s} style={{paintOrder: 'stroke'}}>{trUpper(c.label)}</text>
              </g>
            );
          })}
        </svg>
      </div>
      <AbsoluteFill style={{boxShadow: 'inset 0 0 260px rgba(0,0,0,0.85)', pointerEvents: 'none'}} />
      <div style={{position: 'absolute', left: 120, top: 92, opacity: appear(0.2, 0.8)}}>
        <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 78, color: IVORY, letterSpacing: 4,
          textShadow: '0 4px 24px rgba(0,0,0,0.9)'}}>{trUpper(p.title)}</div>
        <div style={{width: 120, height: 5, background: GOLD, margin: '18px 0 16px'}} />
        <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 40, color: GOLD,
          textShadow: '0 3px 16px rgba(0,0,0,0.9)'}}>{p.subtitle}</div>
      </div>
      {year ? (
        <div style={{position: 'absolute', right: 120, top: 92, fontFamily: SERIF, fontWeight: 700,
          fontSize: year.text.length > 10 ? 60 : 92,
          color: IVORY, textShadow: '0 4px 24px rgba(0,0,0,0.9)', opacity: appear(year.t, 0.4)}}>{year.text}</div>
      ) : null}
      {p.note ? (
        <div style={{position: 'absolute', right: 120, bottom: 70, fontFamily: SANS, fontSize: 30,
          color: 'rgba(243,236,221,0.75)', fontStyle: 'italic'}}>{p.note}</div>
      ) : null}
    </AbsoluteFill>
  );
};
