import { NextResponse } from "next/server";
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const protectedRoutes = createRouteMatcher([
  "/dashboard(.*)",
  "/runs(.*)",
  "/approvals(.*)",
  "/history(.*)",
  "/settings(.*)",
  "/api/qa-runs(.*)"
]);

const adminRoutes = createRouteMatcher([
  "/approvals(.*)",
  "/settings(.*)",
  "/api/qa-runs/(.*)/approve"
]);

const clerkConfigured = Boolean(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY
);

const middleware = clerkConfigured
  ? clerkMiddleware(async (authObject, request) => {
      if (protectedRoutes(request)) {
        await authObject.protect();
      }

      if (adminRoutes(request)) {
        const session = await authObject();
        const claims = (session.sessionClaims ?? {}) as Record<string, unknown>;
        const metadata = (claims.metadata ?? claims.publicMetadata ?? {}) as Record<string, unknown>;
        const role = (metadata.role as string | undefined) ?? "viewer";
        if (role !== "admin") {
          return NextResponse.redirect(new URL("/dashboard", request.url));
        }
      }

      return NextResponse.next();
    })
  : () => NextResponse.next();

export default middleware;

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/api/:path*"]
};
