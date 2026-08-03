import { useRegisterSW } from "virtual:pwa-register/react";

import { Button } from "../ui/Button";

export function UpdatePrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  if (!needRefresh) return null;

  function applyUpdate() {
    const hasUnsavedWork = document.querySelector('[data-unsaved="true"]');
    if (hasUnsavedWork && !window.confirm("页面中有尚未保存的内容。仍要更新并重新载入吗？")) return;
    void updateServiceWorker(true);
  }

  return (
    <div className="update-prompt" role="status" aria-live="polite">
      <div>
        <strong>新版本已准备好</strong>
        <span>当前版本 {__APP_VERSION__}</span>
      </div>
      <Button type="button" onClick={applyUpdate}>更新并重新加载</Button>
      <Button type="button" variant="ghost" onClick={() => setNeedRefresh(false)}>稍后</Button>
    </div>
  );
}
