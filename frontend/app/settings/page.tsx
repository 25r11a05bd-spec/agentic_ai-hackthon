import { AppShell } from "@/components/app-shell";
import { requireSession } from "@/lib/session";

const settingsCards = [
  {
    title: "Notification Channels",
    copy: "Twilio WhatsApp and SMS targets for operator alerts and approval prompts."
  },
  {
    title: "Approval Policy",
    copy: "Validation score, hallucination thresholds, retry exhaustion, and fallback-use controls."
  },
  {
    title: "Provider Strategy",
    copy: "Primary Groq orchestration with Ollama fallback for bounded retries and replans."
  },
  {
    title: "Role Controls",
    copy: "Admin, operator, and viewer access aligned with Clerk-authenticated sessions."
  }
];

export default async function SettingsPage() {
  await requireSession(["admin"]);
  return (
    <AppShell pathname="/settings">
      <div className="topbar">
        <div className="page-title">
          <h2>System Settings</h2>
          <p>
            Configuration surfaces for policy and delivery. This is the place where role-gated
            controls will persist backend thresholds and notification behavior.
          </p>
        </div>
      </div>

      <div className="settings-grid">
        {settingsCards.map((item) => (
          <section className="panel setting-item" key={item.title}>
            <div className="eyebrow">Config Surface</div>
            <h3>{item.title}</h3>
            <p className="muted">{item.copy}</p>
          </section>
        ))}
      </div>
    </AppShell>
  );
}
