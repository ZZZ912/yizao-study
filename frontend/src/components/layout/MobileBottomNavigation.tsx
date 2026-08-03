const items = ["首页", "学习", "刷题", "复习", "我的"];

export function MobileBottomNavigation() {
  return (
    <nav className="mobile-bottom-nav" aria-label="主导航">
      {items.map((item, index) => (
        <a key={item} className={index === 0 ? "is-active" : ""} href={index === 0 ? "/" : `/#${item}`}>
          <span className="nav-mark" aria-hidden="true">{index + 1}</span>
          <span>{item}</span>
        </a>
      ))}
    </nav>
  );
}
