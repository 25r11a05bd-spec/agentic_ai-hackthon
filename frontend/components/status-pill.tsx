import clsx from "clsx";

import type { QARunStatus } from "@/lib/types";

export function StatusPill({ status }: { status: QARunStatus | string }) {
  return <span className={clsx("status-pill", `status-${status}`)}>{status.replaceAll("_", " ")}</span>;
}
