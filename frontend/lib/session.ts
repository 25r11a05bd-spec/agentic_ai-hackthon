import "server-only";

import { redirect } from "next/navigation";
import { auth, currentUser } from "@clerk/nextjs/server";

export type AppRole = "admin" | "operator" | "viewer";

export interface SessionContext {
  clerkEnabled: boolean;
  signedIn: boolean;
  userId: string;
  role: AppRole;
  email: string | null;
  token: string | null;
}

function clerkEnabled() {
  return Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY
  );
}

export async function getSessionContext(): Promise<SessionContext> {
  if (!clerkEnabled()) {
    return {
      clerkEnabled: false,
      signedIn: true,
      userId: "dev-operator",
      role: "admin",
      email: "dev@local",
      token: null
    };
  }

  const authState = await auth();
  const user = await currentUser();
  const metadata = (user?.publicMetadata ?? {}) as Record<string, unknown>;
  const role = (metadata.role as AppRole | undefined) ?? "viewer";
  const token = authState.userId ? await authState.getToken() : null;

  return {
    clerkEnabled: true,
    signedIn: Boolean(authState.userId),
    userId: authState.userId ?? "",
    role,
    email: user?.primaryEmailAddress?.emailAddress ?? null,
    token
  };
}

export async function requireSession(allowedRoles?: AppRole[]): Promise<SessionContext> {
  const session = await getSessionContext();
  if (session.clerkEnabled && !session.signedIn) {
    redirect(process.env.NEXT_PUBLIC_CLERK_SIGN_IN_URL ?? "/sign-in");
  }
  if (allowedRoles && !allowedRoles.includes(session.role)) {
    redirect("/dashboard");
  }
  return session;
}

export async function buildBackendHeaders(requiredRoles?: AppRole[]): Promise<HeadersInit> {
  const session = await requireSession(requiredRoles);
  const headers: HeadersInit = {};

  if (session.token) {
    headers.Authorization = `Bearer ${session.token}`;
  }

  if (!session.clerkEnabled) {
    headers["x-demo-role"] = session.role;
    headers["x-demo-user"] = session.userId;
  }

  return headers;
}
