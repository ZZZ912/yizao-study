import { NavLink } from "react-router";

const items = [["首页", "/"], ["学习", "/study"], ["刷题", "/practice"], ["复习", "/review"], ["我的", "/profile"]];

export function DesktopSidebar() {
  return (
    <aside className="desktop-sidebar" aria-label="主导航">
      <NavLink className="wordmark" to="/" aria-label="一造学伴首页">
        <span aria-hidden="true">一造</span><strong>一造学伴</strong>
      </NavLink>
      <nav>{items.map(([item, path], index) => (
        <NavLink key={item} className={({ isActive }) => isActive ? "is-active" : ""} end={path === "/"} to={path}>
          <span className="nav-mark" aria-hidden="true">{index + 1}</span>{item}
        </NavLink>
      ))}</nav>
      <p className="sidebar-note">距 10 月 17 日<br />每一天都算数</p>
    </aside>
  );
}
