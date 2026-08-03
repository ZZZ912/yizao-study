import { ReactNode, useRef } from "react";

import { Button } from "./Button";
import { useFocusTrap } from "./useFocusTrap";

export function Dialog({
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
  const panelRef = useRef<HTMLDivElement>(null);
  useFocusTrap(panelRef, isOpen, onClose);

  if (!isOpen) return null;
  return (
    <div className="overlay overlay--center" role="presentation" onMouseDown={onClose}>
      <div
        className="dialog"
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        tabIndex={-1}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="overlay__header">
          <h2 id="dialog-title">{title}</h2>
          <Button variant="ghost" type="button" onClick={onClose} aria-label="关闭对话框">
            关闭
          </Button>
        </header>
        {children}
      </div>
    </div>
  );
}
