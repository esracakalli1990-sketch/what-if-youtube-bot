import {staticFile} from 'remotion';
import {loadFont} from '@remotion/fonts';

// Aile adları rakamla bitmesin: CSS "Source Sans 3" adını tırnaksız okuyamıyor.
export const SERIF = 'Cinzel';
export const SANS = 'SourceSans';

loadFont({family: SERIF, url: staticFile('Cinzel.ttf'), weight: '400 900'});
loadFont({family: SANS, url: staticFile('SourceSans3.ttf'), weight: '200 900'});
