"use client";

import { useEffect, useState } from "react";
import useTheme from "@/utils/themeUtils";
// theme picker

export default function ThemePicker() {
  const [userTheme, setUserTheme] = useState("default");

  const applyTheme = useTheme();

  useEffect(() => {
    const theme = localStorage.getItem("theme") || "default";
    setUserTheme(theme);

    applyTheme(userTheme)
  }, [userTheme, applyTheme]);

  const handleThemeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const theme = e.target.value;
    setUserTheme(theme);
    localStorage.setItem("theme", theme);
  };

  return (
    <div className="dropdown mb-72">
      <div tabIndex={0} role="button" className="btn m-1">
        Theme
      </div>
      <ul
        tabIndex={0}
        className="dropdown-content bg-base-300 rounded-box z-1 w-52 p-2 shadow-2xl"
      >
        <li>
          <input
            type="radio"
            name="theme-dropdown"
            className="theme-controller  btn btn-sm btn-block btn-ghost justify-start"
            aria-label="Default"
            value="default"
            onChange={handleThemeChange}
          />
        </li>
        <li>
          <input
            type="radio"
            name="theme-dropdown"
            className="theme-controller  btn btn-sm btn-block btn-ghost justify-start"
            aria-label="Retro"
            value="retro"
            onChange={handleThemeChange}
          />
        </li>
        <li>
          <input
            type="radio"
            name="theme-dropdown"
            className="theme-controller  btn btn-sm btn-block btn-ghost justify-start"
            aria-label="Cyberpunk"
            value="cyberpunk"
            onChange={handleThemeChange}
          />
        </li>
        <li>
          <input
            type="radio"
            name="theme-dropdown"
            className="theme-controller  btn btn-sm btn-block btn-ghost justify-start"
            aria-label="Valentine"
            value="valentine"
            onChange={handleThemeChange}
          />
        </li>
        <li>
          <input
            type="radio"
            name="theme-dropdown"
            className="theme-controller  btn btn-sm btn-block btn-ghost justify-start"
            aria-label="Aqua"
            value="aqua"
            onChange={handleThemeChange}
          />
        </li>
        <li>
          <input
            type="radio"
            name="theme-dropdown"
            className="theme-controller btn btn-sm btn-block btn-ghost justify-start"
            aria-label="Halloween"
            value="halloween"
            onChange={handleThemeChange}
          />
        </li>
      </ul>
    </div>
  );
}
