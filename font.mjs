import { GLYPHS } from './glyphs.mjs';

export const FONT_FAMILY = 'OpenCode Complete';
export const FONT_FILENAME = 'OpenCode-Complete.otf';
const LETTERS = Object.keys(GLYPHS);
const INVISIBLE = [0, 9, 10, 13, 0x200b, 0x200c, 0x200d, 0x2060, 0xfe0e, 0xfe0f, 0xfeff];

export function createCompleteLogoFont(opentype) {
  const path = data => opentype.Path.fromSVG(data, {
    flipY: true, flipYBase: 36, scale: 20, x: 60, y: 0,
  });
  const glyphs = [
    new opentype.Glyph({ name: '.notdef', advanceWidth: 600, path: path(GLYPHS.o.ink) }),
    new opentype.Glyph({ name: '.null', unicodes: [...INVISIBLE], advanceWidth: 0, path: new opentype.Path() }),
    new opentype.Glyph({ name: 'space', unicodes: [0x20, 0xa0], advanceWidth: 480, path: new opentype.Path() }),
  ];

  for (const letter of LETTERS) {
    const lowerCode = letter.codePointAt(0);
    const upperCode = letter.toUpperCase().codePointAt(0);
    const spec = GLYPHS[letter];
    glyphs.push(new opentype.Glyph({
      name: letter,
      unicode: lowerCode,
      unicodes: [lowerCode, upperCode],
      advanceWidth: spec.advanceWidth || 600,
      path: path(spec.ink),
    }));
  }

  return new opentype.Font({
    familyName: FONT_FAMILY,
    styleName: 'Regular',
    postScriptName: 'OpenCodeComplete-Regular',
    unitsPerEm: 1000,
    ascender: 800,
    descender: -200,
    weightClass: 400,
    version: 'Version 2.100',
    description: 'Complete 26-letter unicase OpenCode modular typeface (with 5x7 wide m/w and 3x7 symmetric i/l).',
    manufacturer: 'OpenType',
    designer: 'OpenCode wordmark + Complete Extension',
    designerURL: 'https://opencode.ai/font',
    glyphs,
  });
}
