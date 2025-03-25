import React from "react";
import ThemePicker from "@/components/themePicker";

export default function Settings() {

  return (
    <div className="flex flex-col lg:flex-row items-center gap-5 justify-center">
      <div>
        <h1 className="text-3xl py-3">Settings</h1>
        <ThemePicker />
      </div>
    </div>
  )
}
