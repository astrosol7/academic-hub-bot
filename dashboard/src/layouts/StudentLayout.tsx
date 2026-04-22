import { useState } from "react";
import { Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  BookOpen,
  MessageCircle,
  Search,
  Settings,
} from "lucide-react";
import {
  Sidebar,
  MobileSidebar,
  Topbar,
  type NavGroup,
  type NavItem,
} from "../components/navigation/Sidebar";

const navGroups: NavGroup[] = [
  {
    title: "Hub",
    items: [
      { to: "/student", label: "Dashboard", icon: LayoutDashboard },
      { to: "/student/resources", label: "Resources", icon: BookOpen },
      { to: "/student/search", label: "Search", icon: Search },
      { to: "/student/chat", label: "Ask Orbit", icon: MessageCircle },
    ],
  },
];

const bottomItems: NavItem[] = [
  { to: "/student/settings", label: "Settings", icon: Settings },
];

export default function StudentLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg)] text-[var(--fg)]">
      <Sidebar
        groups={navGroups}
        bottomItems={bottomItems}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((v) => !v)}
      />
      <MobileSidebar
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        groups={navGroups}
        bottomItems={bottomItems}
      />
      <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
        <Topbar title="Orbit Student Hub" onMenuClick={() => setMobileOpen((v) => !v)} />
        <div className="flex-1 overflow-y-auto px-4 py-6 lg:px-8 lg:py-8">
          <div className="mx-auto max-w-5xl">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
