import Link from "next/link";
import { Activity, BadgeCheck, Clock3, LayoutDashboard, Settings2, Sparkles } from "lucide-react";
import type { ReactNode } from "react";

const navItems = [
  {
    href: "/dashboard",
    label: "Dashboard",
    copy: "KPI cards, trend charts, pie insight",
    icon: LayoutDashboard
  },
  {
    href: "/runs",
    label: "Runs",
    copy: "Execution list, filters, QA outcomes",
    icon: Activity
  },
  {
    href: "/approvals",
    label: "Approvals",
    copy: "Go or no-go queue for risky runs",
    icon: BadgeCheck
  },
  {
    href: "/history",
    label: "History",
    copy: "Prior failures and successful fixes",
    icon: Clock3
  },
  {
    href: "/settings",
    label: "Settings",
    copy: "Thresholds, providers, notifications",
    icon: Settings2
  }
];

interface AppShellProps {
  children: ReactNode;
  pathname?: string;
}

export function AppShell({ children, pathname = "/dashboard" }: AppShellProps) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-kicker">Autonomous QA Ops</div>
          <h1>Playback-First Validation Control Room</h1>
          <p>
            Monitor self-healing runs, inspect grounded failure explanations, and decide when
            autonomous fixes are safe enough to ship.
          </p>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link className="nav-link" href={item.href} key={item.href} data-active={active}>
                <span className="nav-label">
                  <Icon size={16} style={{ marginRight: 8, verticalAlign: "text-top" }} />
                  {item.label}
                </span>
                <span className="nav-copy">{item.copy}</span>
              </Link>
            );
          })}
        </nav>

        <div className="card" style={{ marginTop: 24 }}>
          <div className="eyebrow">Control Policy</div>
          <h3 style={{ marginTop: 8, marginBottom: 10 }}>Safe self-healing only</h3>
          <p className="muted" style={{ margin: 0 }}>
            Direct source-file mutation stays disabled. This console only recommends and replays
            bounded plan changes.
          </p>
          <div className="chip" style={{ marginTop: 14 }}>
            <Sparkles size={14} />
            <strong>Approval gate stays human-in-the-loop</strong>
          </div>
        </div>
      </aside>

      <main className="content">{children}</main>
    </div>
  );
}
