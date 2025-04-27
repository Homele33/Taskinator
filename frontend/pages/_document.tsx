import { Html, Head, Main, NextScript } from "next/document";
import BurgerMenu from "@/components/burgerMenu";

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body className="antialiased">
        <Main />
        <BurgerMenu />
        <NextScript />
      </body>
    </Html>
  );
}
