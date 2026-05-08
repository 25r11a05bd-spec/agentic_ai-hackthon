"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { CreateRunModal } from "@/components/create-run-modal";

export function RunsHeader({ hideTitle = false }: { hideTitle?: boolean }) {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      {!hideTitle && (
        <div className="topbar">
          <div className="page-title">
            <h2>Run Inventory</h2>
            <p>
              Search execution records by status, task, and file identity, then drill into playback
              for the exact retry and approval story.
            </p>
          </div>
          <button
            className="toolbar-select primary"
            style={{ width: "auto", display: "flex", alignItems: "center", gap: 8 }}
            onClick={() => setShowModal(true)}
          >
            <Plus size={18} />
            New Autonomous Run
          </button>
        </div>
      )}

      {hideTitle && (
        <button
          className="toolbar-select primary"
          style={{ width: "auto", display: "flex", alignItems: "center", gap: 8 }}
          onClick={() => setShowModal(true)}
        >
          <Plus size={18} />
          New Autonomous Run
        </button>
      )}

      {showModal && <CreateRunModal onClose={() => setShowModal(false)} />}
    </>
  );
}
