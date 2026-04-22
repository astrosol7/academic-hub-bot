import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react";

// ─── Utility ───
export function cn(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

// ─── Button ───
type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
}

const buttonVariants: Record<ButtonVariant, string> = {
  primary: "bg-[var(--accent)] text-[var(--accent-fg)] hover:bg-[var(--accent-hover)] active:scale-[0.98]",
  secondary: "bg-[var(--surface)] text-[var(--fg)] border border-[var(--border)] hover:bg-[var(--surface-hover)]",
  ghost: "text-[var(--fg-muted)] hover:bg-[var(--surface)] hover:text-[var(--fg)]",
  danger: "bg-[var(--danger)] text-[var(--danger-fg)] hover:opacity-90",
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs gap-1.5",
  md: "h-9 px-4 text-sm gap-2",
  lg: "h-11 px-6 text-sm gap-2",
};

export function Button({ variant = "primary", size = "md", loading, icon, children, className, disabled, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium rounded-[var(--radius-sm)] transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed",
        buttonVariants[variant],
        buttonSizes[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" /> : icon}
      {children}
    </button>
  );
}

// ─── Input ───
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ label, error, icon, className, ...props }, ref) => {
  return (
    <div className="space-y-1.5">
      {label && <label className="block text-xs font-medium text-[var(--fg-muted)]">{label}</label>}
      <div className="relative">
        {icon && <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--fg-subtle)]">{icon}</div>}
        <input
          ref={ref}
          className={cn(
            "w-full h-10 rounded-[var(--radius-sm)] border bg-[var(--bg)] px-3 text-sm text-[var(--fg)] placeholder:text-[var(--fg-subtle)] transition-colors duration-150",
            "border-[var(--border)] focus:border-[var(--accent)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]",
            icon ? "pl-10" : "",
            error ? "border-[var(--danger)]" : "",
            className,
          )}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-[var(--danger)]">{error}</p>}
    </div>
  );
});
Input.displayName = "Input";

// ─── Card ───
interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

export function Card({ children, className, padding = true }: CardProps) {
  return (
    <div className={cn(
      "rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg-elevated)] transition-theme",
      padding ? "p-5" : "",
      className,
    )}>
      {children}
    </div>
  );
}

// ─── Modal ───
interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  maxWidth?: string;
}

export function Modal({ open, onClose, title, children, maxWidth = "max-w-lg" }: ModalProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={{ duration: 0.15 }}
        className={cn(
          "relative z-10 w-full rounded-[var(--radius)] border border-[var(--border)] bg-[var(--bg-elevated)] shadow-2xl",
          maxWidth,
        )}
      >
        {title && (
          <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
            <h3 className="text-sm font-semibold text-[var(--fg)]">{title}</h3>
            <button onClick={onClose} className="text-[var(--fg-subtle)] hover:text-[var(--fg)] transition-colors">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
        <div className="p-5">{children}</div>
      </motion.div>
    </div>
  );
}

// ─── Toast ───
type ToastTone = "success" | "warning" | "danger" | "info";

interface Toast {
  id: string;
  message: string;
  tone: ToastTone;
}

const toastIcons: Record<ToastTone, React.ReactNode> = {
  success: <CheckCircle2 className="h-4 w-4 text-[var(--success)]" />,
  warning: <AlertTriangle className="h-4 w-4 text-[var(--warning)]" />,
  danger: <XCircle className="h-4 w-4 text-[var(--danger)]" />,
  info: <Info className="h-4 w-4 text-[var(--fg-muted)]" />,
};

export function ToastStack({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: string) => void }) {
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="pointer-events-auto flex items-center gap-3 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--bg-elevated)] px-4 py-3 shadow-lg"
          >
            {toastIcons[toast.tone]}
            <span className="text-sm text-[var(--fg)]">{toast.message}</span>
            <button onClick={() => onDismiss(toast.id)} className="ml-2 text-[var(--fg-subtle)] hover:text-[var(--fg)]">
              <X className="h-3.5 w-3.5" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

// ─── useToasts Hook ───
export function useToasts() {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const push = (message: string, tone: ToastTone = "info") => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [...prev, { id, message, tone }]);
    window.setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3200);
  };

  const dismiss = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

  return { toasts, push, dismiss };
}

// ─── StatusChip ───
export function StatusChip({ label, tone }: { label: string; tone: "success" | "warning" | "danger" | "default" }) {
  const colors: Record<string, string> = {
    success: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    danger: "bg-red-500/10 text-red-500 border-red-500/20",
    default: "bg-[var(--surface)] text-[var(--fg-muted)] border-[var(--border)]",
  };

  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold", colors[tone])}>
      <span className={cn("h-1.5 w-1.5 rounded-full", tone === "success" ? "bg-emerald-500" : tone === "warning" ? "bg-amber-500" : tone === "danger" ? "bg-red-500" : "bg-[var(--fg-subtle)]")} />
      {label}
    </span>
  );
}
