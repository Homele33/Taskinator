// components/Layout.tsx
import { ReactNode } from 'react';
import { useRouter } from 'next/router';
import BurgerMenu from './burgerMenu';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const router = useRouter();
  const isAuthPage = router.pathname === '/login' || router.pathname === '/register';

  return (
    <>
      {!isAuthPage && <BurgerMenu />}
      <main>{children}</main>
    </>
  );
}
