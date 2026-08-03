const items = ["首页", "学习", "刷题", "复习", "我的"];

export function DesktopSidebar() {
  return (
    <aside className="desktop-sidebar" aria-label="主导航">
      <a className="wordmark" href="/" aria-label="一造学伴首页">
        <span aria-hidden="true">一造</span>
        <strong>一造学伴</strong>
      </a>
      <nav>
        {items.map((item, index) => (
          <a key={item} className={index === 0 ? "is-active" : ""} href={index === 0 ? "/" : `/#${item}`}>
            <span className="nav-mark" aria-hidden="true">{index + 1}</span>
            {item}
          </a>
        ))}
      </nav>
    </aside>
  );
}
