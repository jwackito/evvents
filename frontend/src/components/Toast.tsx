import { useToastStore } from "@/stores/toast";
import type { ToastType } from "@/stores/toast";
import styles from "./Toast.module.css";

const icons: Record<ToastType, string> = {
  success: "\u2713",
  error: "\u2717",
  info: "\u2139",
  warning: "\u26A0",
};

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const removeToast = useToastStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div className={styles.container}>
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`${styles.toast} ${styles[t.type]}`}
          onClick={() => removeToast(t.id)}
        >
          <span className={styles.icon}>{icons[t.type]}</span>
          <span className={styles.message}>{t.message}</span>
        </div>
      ))}
    </div>
  );
}
