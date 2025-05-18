"use client";
import { useCallback } from 'react';

export default function useTheme() {
  const applyTheme = useCallback((theme: string) => {
    document.documentElement.setAttribute('data-theme', theme);
    // Or any other logic to apply the theme
  }, [])

  return applyTheme;
};
