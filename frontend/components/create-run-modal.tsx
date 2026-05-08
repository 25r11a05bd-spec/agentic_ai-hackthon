"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { Upload, X } from "lucide-react";

export function CreateRunModal({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const [task, setTask] = useState("Analyze automation workflow quality");
  const [projectFile, setProjectFile] = useState<File | null>(null);
  const [workflowFile, setWorkflowFile] = useState<File | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectFile || !workflowFile) {
      setError("Please select both app.py and automation.json files.");
      return;
    }

    startTransition(async () => {
      setError(null);
      const formData = new FormData();
      formData.append("task", task);
      formData.append("project_file", projectFile);
      formData.append("workflow_file", workflowFile);
      formData.append("validation_mode", "strict");
      formData.append("retry_enabled", "true");
      formData.append("notifications_enabled", "true");
      formData.append("max_retries", "3");

      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
        const response = await fetch(`${API_BASE}/api/v1/qa-runs`, {
          method: "POST",
          body: formData,
        });

        const result = await response.json();
        if (!response.ok) {
          setError(result.detail ?? "Failed to create run.");
          return;
        }

        onClose();
        // Teleport to the live run details page using the correct data structure
        if (result.data && result.data.id) {
          router.push(`/runs/${result.data.id}`);
        } else {
          router.push('/dashboard'); // Fallback if ID is missing
        }
      } catch (err) {
        setError("Network error. Please ensure the backend is running.");
      }
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content panel shadow-premium">
        <div className="section-heading">
          <div>
            <div className="eyebrow">New Execution</div>
            <h3>Dispatch Autonomous Run</h3>
          </div>
          <button className="icon-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="form-stack">
          <div className="field">
            <label className="eyebrow">Validation Task</label>
            <input
              className="toolbar-input"
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="e.g. Analyze automation workflow quality"
              required
            />
          </div>

          <div className="file-grid">
            <div className="field">
              <label className="eyebrow">Project Source (app.py)</label>
              <div className="file-input-wrapper">
                <input
                  type="file"
                  id="project_file"
                  onChange={(e) => setProjectFile(e.target.files?.[0] || null)}
                  accept=".py"
                  className="hidden-input"
                />
                <label htmlFor="project_file" className="file-label">
                  <Upload size={16} />
                  <span>{projectFile ? projectFile.name : "Select app.py"}</span>
                </label>
              </div>
            </div>

            <div className="field">
              <label className="eyebrow">Workflow Config (automation.json)</label>
              <div className="file-input-wrapper">
                <input
                  type="file"
                  id="workflow_file"
                  onChange={(e) => setWorkflowFile(e.target.files?.[0] || null)}
                  accept=".json"
                  className="hidden-input"
                />
                <label htmlFor="workflow_file" className="file-label">
                  <Upload size={16} />
                  <span>{workflowFile ? workflowFile.name : "Select automation.json"}</span>
                </label>
              </div>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="modal-actions">
            <button
              type="button"
              className="toolbar-select secondary"
              onClick={onClose}
              disabled={isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="toolbar-select primary"
              disabled={isPending}
            >
              {isPending ? "Dispatching..." : "Start Autonomous Run"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
