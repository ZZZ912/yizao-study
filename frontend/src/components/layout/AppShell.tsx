import { ReactNode, useCallback, useState } from "react";
import { NavLink } from "react-router";

import { Button } from "../ui/Button";
import { Drawer } from "../ui/Drawer";
import { DesktopSidebar } from "./DesktopSidebar";
import { MobileBottomNavigation } from "./MobileBottomNavigation";

export function AppShell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = useCallback(() => setMenuOpen(false), []);

  return (
    <div className="app-shell">
      <DesktopSidebar />
      <div className="app-shell__body">
        <header className="mobile-topbar">
          <a className="wordmark" href="/">
            <span aria-hidden="true">一造</span>
            <strong>一造学伴</strong>
          </a>
          <Button variant="ghost" type="button" onClick={() => setMenuOpen(true)} aria-expanded={menuOpen}>
            菜单
          </Button>
        </header>
        {children}
      </div>
      <MobileBottomNavigation />
      <Drawer isOpen={menuOpen} onClose={closeMenu} title="导航菜单">
        <nav className="drawer-nav" aria-label="抽屉导航">
          {[
            ["首页", "/"], ["学习", "/study"], ["刷题", "/practice"], ["复习", "/review"], ["我的", "/profile"],
          ].map(([item, path]) => <NavLink onClick={closeMenu} to={path} key={item}>{item}</NavLink>)}
        </nav>
      </Drawer>
    </div>
  );
}
