import { useEffect } from "react";

interface Shortcuts {
  onSpace?: () => void;
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
}

/**
 * キーボードショートカットフック.
 *
 * Space: 再生/停止
 * ←: コマ戻し
 * →: コマ送り
 */
export function useKeyboardShortcuts({ onSpace, onArrowLeft, onArrowRight }: Shortcuts) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // input/textarea にフォーカス中は無視
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;

      switch (e.code) {
        case "Space":
          e.preventDefault();
          onSpace?.();
          break;
        case "ArrowLeft":
          e.preventDefault();
          onArrowLeft?.();
          break;
        case "ArrowRight":
          e.preventDefault();
          onArrowRight?.();
          break;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onSpace, onArrowLeft, onArrowRight]);
}
