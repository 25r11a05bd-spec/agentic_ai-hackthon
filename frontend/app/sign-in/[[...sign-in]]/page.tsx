import Link from "next/link";
import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
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
              "linear-gradient(160deg, rgba(42, 228, 255, 0.1), rgba(255, 159, 90, 0.08))",
            border: "1px solid rgba(132, 197, 255, 0.16)"
          }}
        >
          <div className="brand-kicker">Autonomous QA Ops</div>
          <h1 style={{ marginTop: 0, fontSize: "2.4rem", lineHeight: 1.05 }}>
            Sign in to the QA control room
          </h1>
          <p className="muted" style={{ fontSize: "1rem", lineHeight: 1.7 }}>
            Review playback timelines, grounded failure explanations, self-heal strategy changes,
            and approval-gated runs from a single operations console.
          </p>
          <div className="timeline-list" style={{ marginTop: 22 }}>
            <div className="timeline-item">
              <strong>Playback-first debugging</strong>
              <div>Timeline replay synced with graph state and agent transitions.</div>
            </div>
            <div className="timeline-item">
              <strong>Safe self-healing only</strong>
              <div>No direct source mutation, only bounded plan adjustments and approval gates.</div>
            </div>
            <div className="timeline-item">
              <strong>Role-aware operations</strong>
              <div>Admins approve, operators retry, viewers observe.</div>
            </div>
          </div>
          <p style={{ marginTop: 24 }}>
            <Link className="small-link" href="/dashboard">
              Back to dashboard
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
          <SignIn
            path="/sign-in"
            routing="path"
            signUpUrl="/sign-up"
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
