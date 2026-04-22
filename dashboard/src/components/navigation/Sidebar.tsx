
import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {

  LogOut,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Sparkles,
  Sun,
  UserRound,
  Menu,
  type LucideIcon,
} from "lucide-react";
import { cn } from "../ui";
import { useTheme } from "../../lib/theme";
import { useAuth } from "../../lib/auth";

// ─── Types ───
export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  badge?: number;
  badgeTone?: "default" | "warning";
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

interface SidebarProps {
  groups: NavGroup[];
  bottomItems?: NavItem[];
  collapsed: boolean;
  onToggleCollapse: () => void;
}

// ─── NavButton ───
function SidebarLink({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const Icon = item.icon;
  return (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        cn(
          "group flex w-full items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium transition-all duration-150",
          collapsed ? "justify-center" : "",
          isActive
            ? "bg-[var(--surface)] text-[var(--fg)]"
            : "text-[var(--fg-muted)] hover:bg-[var(--surface)] hover:text-[var(--fg)]",
        )
      }
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
      {!collapsed && item.badge != null && item.badge > 0 && (
        <span
          className={cn(
            "ml-auto inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[10px] font-bold",
            item.badgeTone === "warning"
              ? "bg-amber-500/15 text-amber-500"
              : "bg-[var(--surface-hover)] text-[var(--fg-subtle)]",
          )}
        >
          {item.badge}
        </span>
      )}
    </NavLink>
  );
}

// ─── Desktop Sidebar ───
export function Sidebar({ groups, bottomItems, collapsed, onToggleCollapse }: SidebarProps) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <aside
      className={cn(
        "relative z-20 hidden shrink-0 flex-col border-r border-[var(--border)] bg-[var(--bg-elevated)] transition-all duration-300 lg:flex",
        collapsed ? "w-[var(--sidebar-collapsed-width)]" : "w-[var(--sidebar-width)]",
      )}
    >
      {/* Profile Header */}
      <div className="p-3">
        <div
          className={cn(
            "flex w-full items-center gap-3 rounded-[var(--radius-sm)] p-2 transition-colors",
            collapsed ? "justify-center" : "",
          )}
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--accent)]/10 text-[var(--fg)]">
            <UserRound className="h-4 w-4" />
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1 text-left">
              <div className="truncate text-sm font-semibold text-[var(--fg)]">{user?.username || "User"}</div>
              <div className="text-[0.65rem] font-bold uppercase tracking-widest text-[var(--fg-subtle)]">
                {user?.role || "guest"}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Search */}
      {!collapsed && (
        <div className="px-4 py-2">
          <div className="flex items-center gap-2 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--bg)] px-3 py-2">
            <Search className="h-3.5 w-3.5 text-[var(--fg-subtle)]" />
            <input
              className="w-full bg-transparent text-xs text-[var(--fg)] outline-none placeholder:text-[var(--fg-subtle)]"
              placeholder="Quick search..."
            />
            <span className="text-[10px] font-bold text-[var(--fg-subtle)]">/</span>
          </div>
        </div>
      )}

      {/* Nav Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <div className="space-y-6">
          {groups.map((group) => (
            <div key={group.title}>
              {!collapsed && (
                <div className="mb-2 px-3 text-[0.65rem] font-black uppercase tracking-[0.2em] text-[var(--fg-subtle)]">
                  {group.title}
                </div>
              )}
              <nav className="space-y-1">
                {group.items.map((item) => (
                  <SidebarLink key={item.to} item={item} collapsed={collapsed} />
                ))}
              </nav>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom */}
      <div className="mt-auto border-t border-[var(--border)] p-3 space-y-1">
        {bottomItems?.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className={cn(
            "group flex w-full items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium text-[var(--fg-muted)] hover:bg-[var(--surface)] hover:text-[var(--fg)] transition-colors",
            collapsed ? "justify-center" : "",
          )}
        >
          {theme === "night" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {!collapsed && <span>{theme === "night" ? "Light Mode" : "Dark Mode"}</span>}
        </button>
        {/* Collapse Toggle */}
        <button
          onClick={onToggleCollapse}
          className={cn(
            "group flex w-full items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium text-[var(--fg-muted)] hover:bg-[var(--surface)] hover:text-[var(--fg)] transition-colors",
            collapsed ? "justify-center" : "",
          )}
        >
          {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          {!collapsed && <span>Collapse</span>}
        </button>
        {/* Logout */}
        <button
          onClick={logout}
          className={cn(
            "group flex w-full items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium text-[var(--fg-muted)] hover:bg-red-500/10 hover:text-red-500 transition-colors",
            collapsed ? "justify-center" : "",
          )}
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>End Session</span>}
        </button>
      </div>
    </aside>
  );
}

// ─── Mobile Sidebar ───
export function MobileSidebar({
  open,
  onClose,
  groups,
  bottomItems,
}: {
  open: boolean;
  onClose: () => void;
  groups: NavGroup[];
  bottomItems?: NavItem[];
}) {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex lg:hidden">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.aside
        initial={{ x: "-100%" }}
        animate={{ x: 0 }}
        exit={{ x: "-100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="relative flex w-72 flex-col bg-[var(--bg-elevated)] border-r border-[var(--border)] p-4 shadow-2xl"
      >
        <div className="mb-6 flex items-center justify-between px-2">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent)]/10 text-[var(--fg)]">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="text-lg font-black tracking-tight text-[var(--fg)]">Orbit</span>
          </div>
          <button onClick={onClose} className="text-[var(--fg-subtle)] hover:text-[var(--fg)]">
            <PanelLeftClose className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto px-2">
          {groups.map((group) => (
            <div key={group.title}>
              <div className="mb-2 px-3 text-[0.65rem] font-black uppercase tracking-[0.2em] text-[var(--fg-subtle)]">
                {group.title}
              </div>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <SidebarLink key={item.to} item={item} collapsed={false} />
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-auto border-t border-[var(--border)] pt-4 space-y-1">
          {bottomItems?.map((item) => (
            <SidebarLink key={item.to} item={item} collapsed={false} />
          ))}
          <button
            onClick={toggleTheme}
            className="group flex w-full items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium text-[var(--fg-muted)] hover:bg-[var(--surface)] hover:text-[var(--fg)] transition-colors"
          >
            {theme === "night" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            <span>{theme === "night" ? "Light Mode" : "Dark Mode"}</span>
          </button>
          <button
            onClick={logout}
            className="group flex w-full items-center gap-3 rounded-[var(--radius-sm)] px-3 py-2 text-sm font-medium text-[var(--fg-muted)] hover:bg-red-500/10 hover:text-red-500 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>End Session</span>
          </button>
        </div>
      </motion.aside>
    </div>
  );
}

// ─── Mobile Topbar ───
export function Topbar({ title, onMenuClick }: { title: string; onMenuClick: () => void }) {
  return (
    <header className="flex h-[var(--topbar-height)] items-center border-b border-[var(--border)] bg-[var(--bg-elevated)] px-4 lg:px-6">
      <button
        onClick={onMenuClick}
        className="mr-3 inline-flex items-center justify-center rounded-[var(--radius-sm)] border border-[var(--border)] p-2 text-[var(--fg-muted)] lg:hidden"
      >
        <Menu className="h-4 w-4" />
      </button>
      <h1 className="text-base font-semibold text-[var(--fg)] truncate">{title}</h1>
    </header>
  );
}
