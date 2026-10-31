import {Easing} from 'remotion';

// Serinin görsel kimliği: tüm grafikler bu değerleri kullanır.
export const GOLD = '#c9a45c';
export const IVORY = '#f3ead8';
export const SAND = '#d8ccb4';
export const ease = Easing.bezier(0.16, 1, 0.3, 1);
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
