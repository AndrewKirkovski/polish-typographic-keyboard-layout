export interface KeyDef {
  id: string
  base: string
  shift?: string
  width?: number  // multiplier, default 1
  isModifier?: boolean
  altLabel?: string  // Mac equivalent symbol
}

/**
 * Maps KeyboardEvent.code values to KeyDef.id values used in KEYBOARD_ROWS.
 * This lets useModifierState translate physical key events into the key IDs
 * that KeyCap uses for pressed-state highlighting.
 */
export const CODE_TO_KEY_ID: Record<string, string> = {
  // Number row
  Backquote: '`',
  Digit1: '1',
  Digit2: '2',
  Digit3: '3',
  Digit4: '4',
  Digit5: '5',
  Digit6: '6',
  Digit7: '7',
  Digit8: '8',
  Digit9: '9',
  Digit0: '0',
  Minus: '-',
  Equal: '=',
  Backspace: '_bs',

  // QWERTY row
  Tab: '_tab',
  KeyQ: 'Q',
  KeyW: 'W',
  KeyE: 'E',
  KeyR: 'R',
  KeyT: 'T',
  KeyY: 'Y',
  KeyU: 'U',
  KeyI: 'I',
  KeyO: 'O',
  KeyP: 'P',
  BracketLeft: '[',
  BracketRight: ']',
  Backslash: '\\',

  // Home row
  CapsLock: '_caps',
  KeyA: 'A',
  KeyS: 'S',
  KeyD: 'D',
  KeyF: 'F',
  KeyG: 'G',
  KeyH: 'H',
  KeyJ: 'J',
  KeyK: 'K',
  KeyL: 'L',
  Semicolon: ';',
  Quote: "'",
  Enter: '_enter',

  // Bottom row
  ShiftLeft: '_lsh',
  KeyZ: 'Z',
  KeyX: 'X',
  KeyC: 'C',
  KeyV: 'V',
  KeyB: 'B',
  KeyN: 'N',
  KeyM: 'M',
  Comma: ',',
  Period: '.',
  Slash: '/',
  ShiftRight: '_rsh',

  // Space row
  ControlLeft: '_lc',
  MetaLeft: '_lw',
  AltLeft: '_la',
  Space: '_sp',
  AltRight: '_ra',
  MetaRight: '_rw',
  ContextMenu: '_mn',
  ControlRight: '_rc',
}

export const KEYBOARD_ROWS: KeyDef[][] = [
  // Number row
  [
    { id: '`', base: '`', shift: '~' },
    { id: '1', base: '1', shift: '!' },
    { id: '2', base: '2', shift: '@' },
    { id: '3', base: '3', shift: '#' },
    { id: '4', base: '4', shift: '$' },
    { id: '5', base: '5', shift: '%' },
    { id: '6', base: '6', shift: '^' },
    { id: '7', base: '7', shift: '&' },
    { id: '8', base: '8', shift: '*' },
    { id: '9', base: '9', shift: '(' },
    { id: '0', base: '0', shift: ')' },
    { id: '-', base: '-', shift: '_' },
    { id: '=', base: '=', shift: '+' },
    { id: '_bs', base: 'Backspace', width: 2, isModifier: true, altLabel: '\u232B' },
  ],
  // QWERTY row
  [
    { id: '_tab', base: 'Tab', width: 1.5, isModifier: true, altLabel: '\u21E5' },
    { id: 'Q', base: 'q', shift: 'Q' },
    { id: 'W', base: 'w', shift: 'W' },
    { id: 'E', base: 'e', shift: 'E' },
    { id: 'R', base: 'r', shift: 'R' },
    { id: 'T', base: 't', shift: 'T' },
    { id: 'Y', base: 'y', shift: 'Y' },
    { id: 'U', base: 'u', shift: 'U' },
    { id: 'I', base: 'i', shift: 'I' },
    { id: 'O', base: 'o', shift: 'O' },
    { id: 'P', base: 'p', shift: 'P' },
    { id: '[', base: '[', shift: '{' },
    { id: ']', base: ']', shift: '}' },
    { id: '\\', base: '\\', shift: '|', width: 1.5 },
  ],
  // Home row
  [
    { id: '_caps', base: 'Caps', width: 1.75, isModifier: true, altLabel: '\u21EA' },
    { id: 'A', base: 'a', shift: 'A' },
    { id: 'S', base: 's', shift: 'S' },
    { id: 'D', base: 'd', shift: 'D' },
    { id: 'F', base: 'f', shift: 'F' },
    { id: 'G', base: 'g', shift: 'G' },
    { id: 'H', base: 'h', shift: 'H' },
    { id: 'J', base: 'j', shift: 'J' },
    { id: 'K', base: 'k', shift: 'K' },
    { id: 'L', base: 'l', shift: 'L' },
    { id: ';', base: ';', shift: ':' },
    { id: "'", base: "'", shift: '"' },
    { id: '_enter', base: 'Enter', width: 2.25, isModifier: true, altLabel: '\u23CE' },
  ],
  // Bottom row
  [
    { id: '_lsh', base: 'Shift', width: 2.25, isModifier: true, altLabel: '\u21E7' },
    { id: 'Z', base: 'z', shift: 'Z' },
    { id: 'X', base: 'x', shift: 'X' },
    { id: 'C', base: 'c', shift: 'C' },
    { id: 'V', base: 'v', shift: 'V' },
    { id: 'B', base: 'b', shift: 'B' },
    { id: 'N', base: 'n', shift: 'N' },
    { id: 'M', base: 'm', shift: 'M' },
    { id: ',', base: ',', shift: '<' },
    { id: '.', base: '.', shift: '>' },
    { id: '/', base: '/', shift: '?' },
    { id: '_rsh', base: 'Shift', width: 2.75, isModifier: true, altLabel: '\u21E7' },
  ],
  // Space row
  [
    { id: '_lc', base: 'Ctrl', width: 1.25, isModifier: true, altLabel: '\u2303' },
    { id: '_lw', base: 'Win', width: 1.25, isModifier: true, altLabel: '\u2318' },
    { id: '_la', base: 'Alt', width: 1.25, isModifier: true, altLabel: '\u2325' },
    { id: '_sp', base: '', width: 6.25, isModifier: true },
    { id: '_ra', base: 'AltGr', width: 1.25, isModifier: true, altLabel: '\u2325' },
    { id: '_rw', base: 'Win', width: 1.25, isModifier: true, altLabel: '\u2318' },
    { id: '_mn', base: 'Menu', width: 1.25, isModifier: true, altLabel: '\u2630' },
    { id: '_rc', base: 'Ctrl', width: 1.25, isModifier: true, altLabel: '\u2303' },
  ],
]
