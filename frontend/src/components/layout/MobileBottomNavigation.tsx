import { NavLink } from "react-router";

const items = [["首页", "/"], ["学习", "/study"], ["刷题", "/practice"], ["复习", "/review"], ["我的", "/profile"]];

export function MobileBottomNavigation() {
  return (
    <nav className="mobile-bottom-nav" aria-label="主导航">
      {items.map(([item, path], index) => (
        <NavLink key={item} className={({ isActive }) => isActive ? "is-active" : ""} end={path === "/"} to={path}>
          <span className="nav-mark" aria-hidden="true">{index + 1}</span><span>{item}</span>
        </NavLink>
      ))}
    </nav>
  );
}
