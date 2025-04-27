"use client";

export default function useTheme() {
  const theme = localStorage.getItem("theme") || "default";
  document.documentElement.setAttribute("data-theme", theme);
}
