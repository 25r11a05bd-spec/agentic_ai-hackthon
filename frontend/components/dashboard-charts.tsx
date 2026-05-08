"use client";

import { Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { MetricsOverview, NotificationLog } from "@/lib/types";

const colors = ["#2ae4ff", "#ff9f5a", "#95ff99", "#ff6a7d"];

interface DashboardChartsProps {
  metrics: MetricsOverview;
  notifications: NotificationLog[];
}

export function DashboardCharts({ metrics, notifications }: DashboardChartsProps) {
  return (
    <div className="panel-grid">
      <section className="panel">
        <div className="section-heading">
          <div>
            <div className="eyebrow">Trendline</div>
            <h3>Reliability vs Overall</h3>
          </div>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={metrics.reliability_trend}>
              <XAxis dataKey="runId" stroke="#99afc5" />
              <YAxis stroke="#99afc5" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="reliability" stroke="#2ae4ff" strokeWidth={3} dot={false} />
              <Line type="monotone" dataKey="overall" stroke="#ff9f5a" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <div className="eyebrow">Distribution</div>
            <h3>Risk Breakdown</h3>
          </div>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={metrics.risk_breakdown} dataKey="value" nameKey="name" innerRadius={65} outerRadius={100}>
                {metrics.risk_breakdown.map((entry, index) => (
                  <Cell key={entry.name} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <div className="eyebrow">Agent Share</div>
            <h3>Contribution by Lane</h3>
          </div>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={metrics.agent_contribution} dataKey="share" nameKey="agent" innerRadius={60} outerRadius={100}>
                {metrics.agent_contribution.map((entry, index) => (
                  <Cell key={entry.agent} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <div className="eyebrow">Alert Feed</div>
            <h3>Notifications</h3>
          </div>
        </div>
        <div className="timeline-list">
          {notifications.map((notification) => (
            <div key={notification.id} className="timeline-item">
              <strong>{notification.channel.toUpperCase()}</strong>
              <div>{notification.message}</div>
              <small className="muted">
                {notification.status} · {notification.recipient}
              </small>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
