import { StyleSheet } from 'react-native';

const originalCreate = StyleSheet.create;

function cleanStyle(style: any): any {
  if (!style || typeof style !== 'object' || Array.isArray(style)) return style;
  const next: any = { ...style };
  if (typeof next.color === 'string' && next.color.toLowerCase() === '#0d0d0d') {
    next.color = '#FFFFFF';
  }
  if (typeof next.borderWidth === 'number' && next.borderWidth > 0) {
    next.borderWidth = 0;
  }
  if (typeof next.borderColor === 'string' && next.borderColor.includes('0, 255, 136')) {
    next.borderColor = 'transparent';
  }
  if (next.fontFamily === 'PressStart2P_400Regular' && typeof next.fontSize === 'number' && next.fontSize < 9) {
    next.fontSize = 9;
  }
  return next;
}

if (!(StyleSheet as any).__coderoPatched) {
  (StyleSheet as any).create = (styles: any) => {
    const cleaned: any = {};
    Object.keys(styles || {}).forEach((key) => {
      cleaned[key] = cleanStyle(styles[key]);
    });
    return originalCreate(cleaned);
  };
  (StyleSheet as any).__coderoPatched = true;
}
