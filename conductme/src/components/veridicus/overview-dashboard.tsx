"use client";

import { useTokenMetrics, useQuantumJobs } from '@/lib/veridicus-data';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Activity, Flame, Zap, TrendingUp } from 'lucide-react';
import { formatNumber } from '@/lib/utils';

export function OverviewDashboard() {
  const { data: metrics, loading: metricsLoading } = useTokenMetrics();
  const { data: jobs, loading: jobsLoading } = useQuantumJobs();

  const formatToken = (value: number) => {
    return formatNumber(value, { maximumFractionDigits: 0 });
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const recentJobs = jobs?.slice(0, 5) || [];
  const totalJobs = jobs?.length || 0;
  const jobs24h = jobs?.filter(job => {
    const jobTime = job.timestamp * 1000;
    const now = Date.now();
    return now - jobTime < 24 * 60 * 60 * 1000;
  }).length || 0;

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Supply</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metricsLoading ? '...' : formatToken(metrics?.total_supply || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">VERIDICUS</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Burned</CardTitle>
            <Flame className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-500">
              {metricsLoading ? '...' : formatToken(metrics?.total_burned || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {metricsLoading ? '...' : formatPercent(
                ((metrics?.total_burned || 0) / (metrics?.total_supply || 1)) * 100
              )} of supply
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {jobsLoading ? '...' : formatToken(totalJobs)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {jobs24h} in last 24h
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Deflation Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {metricsLoading ? '...' : formatPercent(metrics?.deflation_rate || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Annual rate</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Quantum Jobs</CardTitle>
          <CardDescription>Latest quantum computing job executions</CardDescription>
        </CardHeader>
        <CardContent>
          {jobsLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading jobs...</div>
          ) : recentJobs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No jobs yet</div>
          ) : (
            <div className="space-y-2">
              {recentJobs.map((job) => (
                <div
                  key={job.job_id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      job.status === 'completed' ? 'bg-green-500' :
                      job.status === 'running' ? 'bg-yellow-500' :
                      job.status === 'failed' ? 'bg-red-500' :
                      'bg-gray-500'
                    }`} />
                    <div>
                      <div className="font-medium">{job.job_type}</div>
                      <div className="text-sm text-muted-foreground">
                        {job.provider} • {new Date(job.timestamp * 1000).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-orange-500">
                      -{formatToken(job.veridicus_burned)} VDC
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {job.execution_time_ms.toFixed(0)}ms
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

