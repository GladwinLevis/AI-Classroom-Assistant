import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  CalendarCheck,
  FileText,
  MessageSquareText,
  ClipboardCheck,
  Brain,
  Bell,
  UserCircle,
  Settings,
  Sparkles,
  X,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/attendance", label: "Attendance", icon: CalendarCheck },
  { to: "/notes-summary", label: "Notes Summary", icon: FileText },
  { to: "/chatbot", label: "AI Chatbot", icon: MessageSquareText },
  { to: "/assignment-checker", label: "Assignment Checker", icon: ClipboardCheck },
  { to: "/quiz-generator", label: "Quiz Generator", icon: Brain },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/profile", label: "Profile", icon: UserCircle },
  { to: "/settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-border bg-card/80 backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0 lg:bg-card/50",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex items-center justify-between px-6 py-6">
          <a href="/" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient shadow-soft">
              <Sparkles className="h-5 w-5 text-white" />
            </span>
            <span className="font-bold text-[15px] leading-tight">
              AI Classroom<br />Assistant
            </span>
          </a>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={onClose} aria-label="Close menu">
            <X className="h-5 w-5" />
          </Button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-4 pb-4" aria-label="Main navigation">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all",
                  isActive
                    ? "bg-brand-gradient text-white shadow-soft"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )
              }
            >
              <Icon className="h-[18px] w-[18px] shrink-0" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mx-4 mb-4 rounded-2xl bg-brand-gradient-soft p-4">
          <p className="text-xs font-semibold text-primary-700 dark:text-primary-300">AI Credits</p>
          <p className="mt-1 text-xs text-muted-foreground">AI-powered features available</p>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/50 dark:bg-white/10">
            <div className="h-full w-full rounded-full bg-brand-gradient" />
          </div>
        </div>
      </aside>
    </>
  );
}
