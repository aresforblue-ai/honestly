/**
 * Anomaly Detection Dashboard Page
 * =================================
 * 
 * Real-time monitoring of AI agent anomalies.
 * 
 * Route: /dashboard
 */

import { AnomalyDashboard } from "@/components/anomaly-dashboard";

export const metadata = {
  title: "Anomaly Dashboard | Honestly AAIP",
  description: "Real-time ML-powered anomaly detection for AI agents",
};

export default function DashboardPage() {
  return <AnomalyDashboard />;
}

