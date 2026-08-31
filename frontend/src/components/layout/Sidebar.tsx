import {
  Activity,
  ChevronLeft,
  ChevronRight,
  Cog,
  Database,
  History,
  LayoutDashboard,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";
import { type ComponentType } from "react";
import { NavLink } from "react-router-dom";

import { cn } from "@/utils/cn";

interface NavItem {
  label: string;
  to: string;
  icon?: ComponentType<{ className?: string }>;
  end?: boolean;
}

interface NavSection {
  label: string;
  icon: ComponentType<{ className?: string }>;
  to?: string;
  end?: boolean;
  children?: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/", end: true },
  {
    label: "Historical Analysis",
    icon: Database,
    children: [
      { label: "Upload Historical Data", to: "/historical/upload" },
      { label: "Historical Data SPC Analysis", to: "/analyses?type=HISTORICAL" },
    ],
  },
  {
    label: "Manual Monitoring",
    icon: UploadCloud,
    children: [
      { label: "Upload Current Data", to: "/monitoring/upload" },
      { label: "Current Data SPC Analysis", to: "/analyses?type=MONITORING" },
    ],
  },
  {
    label: "Baselines",
    icon: ShieldCheck,
    children: [
      { label: "Active Baselines", to: "/baselines?status=ACTIVE" },
      { label: "Baseline History", to: "/baselines" },
    ],
  },
  { label: "Analysis History", icon: History, to: "/analyses" },
  { label: "Settings", icon: Cog, to: "/settings" },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-surface-200 bg-surface-0 transition-[width] duration-150",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-14 shrink-0 items-center gap-2 border-b border-surface-200 px-4">
        <Activity className="h-5 w-5 shrink-0 text-brand-600" aria-hidden="true" />
        {!collapsed && <span className="truncate text-sm font-semibold text-ink-900">SPC Analytics</span>}
      </div>

      <nav className="scroll-thin flex-1 overflow-y-auto px-2 py-3" aria-label="Main navigation">
        <ul className="flex flex-col gap-1">
          {NAV_SECTIONS.map((section) => (
            <SidebarSection key={section.label} section={section} collapsed={collapsed} />
          ))}
        </ul>
      </nav>

      <button
        type="button"
        onClick={onToggle}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        className="flex h-10 shrink-0 items-center justify-center gap-2 border-t border-surface-200 text-ink-500 hover:bg-surface-50 hover:text-ink-900"
      >
        {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        {!collapsed && <span className="text-xs">Collapse</span>}
      </button>
    </aside>
  );
}

function SidebarSection({ section, collapsed }: { section: NavSection; collapsed: boolean }) {
  const Icon = section.icon;

  if (!section.children) {
    return (
      <li>
        <NavLink
          to={section.to!}
          end={section.end}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium",
              isActive ? "bg-brand-50 text-brand-700" : "text-ink-700 hover:bg-surface-50",
            )
          }
          title={collapsed ? section.label : undefined}
        >
          <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
          {!collapsed && <span className="truncate">{section.label}</span>}
        </NavLink>
      </li>
    );
  }

  return (
    <li>
      <div
        className="flex items-center gap-2.5 px-2.5 py-2 text-xs font-semibold uppercase tracking-wide text-ink-400"
        title={collapsed ? section.label : undefined}
      >
        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
        {!collapsed && <span className="truncate">{section.label}</span>}
      </div>
      {!collapsed && (
        <ul className="ml-6 flex flex-col gap-0.5 border-l border-surface-200 pl-2.5">
          {section.children.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "block rounded-md px-2.5 py-1.5 text-sm",
                    isActive ? "bg-brand-50 font-medium text-brand-700" : "text-ink-700 hover:bg-surface-50",
                  )
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}
