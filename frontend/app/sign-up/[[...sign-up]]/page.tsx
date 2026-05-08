import Link from "next/link";
import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "24px"
      }}
    >
      <div
        className="panel"
        style={{
          width: "100%",
          maxWidth: 1080,
          display: "grid",
          gridTemplateColumns: "1.05fr 0.95fr",
          gap: 24
        }}
      >
        <section
          style={{
            padding: 28,
            borderRadius: 22,
            background:
              "linear-gradient(160deg, rgba(149, 255, 153, 0.1), rgba(42, 228, 255, 0.08))",
            border: "1px solid rgba(132, 197, 255, 0.16)"
          }}
        >
          <div className="brand-kicker">Autonomous QA Ops</div>
          <h1 style={{ marginTop: 0, fontSize: "2.4rem", lineHeight: 1.05 }}>
            Create access for the QA platform
          </h1>
          <p className="muted" style={{ fontSize: "1rem", lineHeight: 1.7 }}>
            New users should still receive the correct Clerk role metadata so route protection and
            approval actions line up with your org policy.
          </p>
          <div className="timeline-list" style={{ marginTop: 22 }}>
            <div className="timeline-item">
              <strong>Viewer</strong>
              <div>Read playback, findings, and metrics.</div>
            </div>
            <div className="timeline-item">
              <strong>Operator</strong>
              <div>Retry runs and monitor queue behavior.</div>
            </div>
            <div className="timeline-item">
              <strong>Admin</strong>
              <div>Approve or reject risky self-healed runs.</div>
            </div>
          </div>
          <p style={{ marginTop: 24 }}>
            <Link className="small-link" href="/sign-in">
              Already have access? Sign in
            </Link>
          </p>
        </section>

        <section
          style={{
            display: "grid",
            placeItems: "center",
            padding: 16
          }}
        >
          <SignUp
            path="/sign-up"
            routing="path"
            signInUrl="/sign-in"
            forceRedirectUrl="/dashboard"
            appearance={{
              variables: {
                colorPrimary: "#2ae4ff",
                colorBackground: "#0b1d2d",
                colorText: "#edf5ff",
                colorInputText: "#edf5ff",
                colorNeutral: "#99afc5"
              }
            }}
          />
        </section>
      </div>
    </main>
  );
}
