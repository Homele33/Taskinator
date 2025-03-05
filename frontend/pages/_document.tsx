import { Menu, House, Calendar, Settings } from "lucide-react";
import { Html, Head, Main, NextScript } from "next/document";

export default function Document() {
  return (
    <Html lang="en" data-theme="dracula">
      <Head />
      <body className="antialiased">
        <label
          htmlFor="drawer-toggle"
          className="btn btn-ghost drawer-button absolute top-5 left-2"
        >
          <Menu />
        </label>
        <Main />
        <div className="drawer">
          <input id="drawer-toggle" type="checkbox" className="drawer-toggle" />

          <div className="drawer-content ">
            <NextScript />
          </div>
          <div className="drawer-side items-center">
            <label htmlFor="drawer-toggle" className="drawer-overlay " />
            <div className="drawer-side-content ">
              <ul className="menu flex flex-col gap-4 w-full">
                <div className="tooltip" data-tip="Home">
                  <li>
                    <a href="/" className="btn flex">
                      <House />
                    </a>
                  </li>
                </div>
                <div className="tooltip" data-tip="Calendar">
                  <li>
                    <a href="/calendar" className="btn flex">
                      <Calendar />
                    </a>
                  </li>
                </div>
                <div className="tooltip" data-tip="Settings">
                  <a href="/settings" className="btn flex">
                    <Settings />
                  </a>
                  <div className="drawer-content-footer justify-end"></div>
                </div>
              </ul>
            </div>
          </div>
        </div>
      </body>
    </Html>
  );
}
