import { ReactNode, useRef } from "react";

import { Button } from "./Button";
import { useFocusTrap } from "./useFocusTrap";

export function Drawer({
  isOpen,
  onClose,
  title,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const panelRef = useRef<HTMLElement>(null);
  useFocusTrap(panelRef, isOpen, onClose);

  if (!isOpen) return null;
  return (
    <div className="overlay" role="presentation" onMouseDown={onClose}>
      <aside
        className="drawer"
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        tabIndex={-1}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="overlay__header">
          <h2 id="drawer-title">{title}</h2>
          <Button variant="ghost" type="button" onClick={onClose} aria-label="关闭菜单">
            关闭
          </Button>
        </header>
        {children}
      </aside>
    </div>
  );
}
