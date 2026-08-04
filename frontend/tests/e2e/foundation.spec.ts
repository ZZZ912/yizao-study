import { expect, Page, test } from "@playwright/test";

const email = process.env.E2E_EMAIL ?? "browser@example.com";
const password = process.env.E2E_PASSWORD ?? "Browser-test-password-2026";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("邮箱").fill(email);
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: /你好/ })).toBeVisible();
}

test("login and logout work without a page refresh", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "我的", exact: true }).click();
  await page.getByRole("button", { name: "退出登录" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "登录学习空间" })).toBeVisible();
});

test("production proxy disables HTTP caching for API and Admin", async ({ request }) => {
  test.skip(
    process.env.E2E_EXPECT_CACHE_HEADERS !== "true",
    "Requires the production Caddy proxy test harness.",
  );
  for (const path of ["/api/v1/auth/csrf/", "/api/v1/auth/me/", "/admin/login/"]) {
    const response = await request.get(path);
    const cacheControl = response.headers()["cache-control"] ?? "";
    expect(cacheControl).toContain("no-store");
    expect(cacheControl).toContain("max-age=0");
  }
});

test("fragmented study card leads into a completed lesson", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.getByRole("link", { name: "开始碎片学习" }).click();
  await expect(page).toHaveURL(/\/quick-study$/);
  await expect(page.getByRole("heading", { name: "碎片记忆卡" })).toBeVisible();
  await page.getByRole("link", { name: "学习完整小节" }).click();
  const completionButton = page.getByRole("button", { name: /完成本节学习|本节已完成/ });
  await expect(completionButton).toBeVisible();
  if ((await completionButton.textContent())?.includes("本节已完成") === false) {
    await completionButton.click();
  }
  await expect(page.getByRole("button", { name: "✓ 本节已完成" })).toBeVisible();
  await page.goto("/");
  await expect(page.locator(".daily-overview").getByText(/\d+\/\d+ 节已完成/)).toBeVisible();
});

for (const width of [360, 390, 768, 1366, 1440]) {
  test(`layout has no horizontal overflow at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width < 1024 ? 844 : 900 });
    await login(page);
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
    await page.screenshot({ path: `test-results/screenshots/foundation-${width}.png`, fullPage: true });
  });
}

test("drawer traps focus, closes with Escape, and restores focus", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  const trigger = page.getByRole("button", { name: "菜单" });
  await trigger.click();
  const drawer = page.getByRole("dialog", { name: "导航菜单" });
  await expect(drawer).toBeVisible();
  const closeButton = drawer.getByRole("button", { name: "关闭菜单" });
  await expect(closeButton).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(drawer.getByRole("link", { name: "我的" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(closeButton).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(trigger).toBeFocused();
});

test("a learner can submit a question and receive an explanation", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.getByRole("link", { name: "刷题", exact: true }).click();
  await expect(page.getByRole("heading", { name: "刷题中心" })).toBeVisible();
  await page.getByRole("link", { name: "开始今日20题", exact: true }).click();
  await page.locator(".option-button").first().click();
  await page.getByRole("button", { name: "提交答案" }).click();
  await expect(page.getByRole("heading", { name: "答案解析" })).toBeVisible();
  await expect(page.getByRole("button", { name: "下一题" })).toBeVisible();
});

test("practice center exposes chapters, records, and a real learning report", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.getByRole("link", { name: "刷题", exact: true }).click();
  await expect(page.getByRole("heading", { name: "刷题中心" })).toBeVisible();
  await expect(page.getByRole("link", { name: /限时训练/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /错题重做/ })).toBeVisible();
  await page.screenshot({ path: "test-results/screenshots/practice-center-390.png", fullPage: true });

  await page.getByRole("link", { name: "章节练习", exact: true }).click();
  await expect(page).toHaveURL(/\/practice\/chapters\//);
  await expect(page.getByRole("heading", { level: 1, name: /建设工程/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "开始做题" }).first()).toBeVisible();

  await page.goto("/report");
  await expect(page.getByRole("heading", { name: "学习报告" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "科目掌握情况" })).toBeVisible();
  await page.screenshot({ path: "test-results/screenshots/learning-report-390.png", fullPage: true });

  await page.goto("/practice/records");
  await expect(page.getByRole("heading", { name: "练习记录" })).toBeVisible();
});

test("layout remains usable at 200 percent zoom", async ({ page }) => {
  await page.setViewportSize({ width: 720, height: 900 });
  await login(page);
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
  expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
});

test("service worker never stores sensitive routes", async ({ page }) => {
  await login(page);
  const cachedUrls = await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
    const keys = await caches.keys();
    const requests = await Promise.all(keys.map(async (key) => (await caches.open(key)).keys()));
    return requests.flat().map((request) => new URL(request.url).pathname);
  });
  for (const path of cachedUrls) {
    expect(path).not.toMatch(/^\/(api|admin|login|user|submit)(\/|$)/);
  }
});
