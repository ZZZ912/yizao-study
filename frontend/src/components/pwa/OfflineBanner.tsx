import { useEffect, useRef, useState } from "react";

export function OfflineBanner() {
  const [state, setState] = useState<"online" | "offline" | "restored">(() =>
    navigator.onLine ? "online" : "offline",
  );
  const restoreTimer = useRef<number | null>(null);
  useEffect(() => {
    const online = () => {
      setState("restored");
      if (restoreTimer.current) window.clearTimeout(restoreTimer.current);
      restoreTimer.current = window.setTimeout(() => setState("online"), 4_000);
    };
    const offline = () => setState("offline");
    window.addEventListener("online", online);
    window.addEventListener("offline", offline);
    return () => {
      window.removeEventListener("online", online);
      window.removeEventListener("offline", offline);
      if (restoreTimer.current) window.clearTimeout(restoreTimer.current);
    };
  }, []);
  if (state === "online") return null;
  return (
    <div className="status-banner" role="status">
      {state === "restored" ? "网络连接已恢复。" : "当前处于离线状态，联网后将自动恢复。"}
    </div>
  );
}
