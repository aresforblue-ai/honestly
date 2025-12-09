"use client";

import { useQuantumJobs, useQuantumProviders } from '@/lib/veridicus-data';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Clock, Zap } from 'lucide-react';
import { formatNumber } from '@/lib/utils';
import { useVERIDICUSWebSocket } from '@/lib/veridicus-websocket';
import { useEffect, useState } from 'react';

export function JobsMonitor() {
  const { data: jobs, loading: jobsLoading } = useQuantumJobs();
  const { data: providers } = useQuantumProviders();
  const [liveJobs, setLiveJobs] = useState(jobs || []);

  // Subscribe to real-time job events
  useVERIDICUSWebSocket('job_executed', (event) => {
    if (event.data) {
      setLiveJobs((prev) => [event.data, ...prev].slice(0, 50));
    }
  });

  useEffect(() => {
    if (jobs) {
      setLiveJobs(jobs);
    }
  }, [jobs]);

  const formatToken = (value: number) => {
    return formatNumber(value, { maximumFractionDigits: 2 });
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  // Job type breakdown
  const jobTypeCounts = liveJobs.reduce((acc, job) => {
    acc[job.job_type] = (acc[job.job_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Provider utilization
  const providerCounts = liveJobs.reduce((acc, job) => {
    acc[job.provider] = (acc[job.provider] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const totalBurned = liveJobs.reduce((sum, job) => sum + (job.veridicus_burned || 0), 0);
  const avgExecutionTime = liveJobs.length > 0
    ? liveJobs.reduce((sum, job) => sum + (job.execution_time_ms || 0), 0) / liveJobs.length
    : 0;

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{liveJobs.length}</div>
            <p className="text-xs text-muted-foreground mt-1">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Burned</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-500">
              {formatToken(totalBurned)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">VERIDICUS</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Execution</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatTime(avgExecutionTime)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Per job</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Providers</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(providerCounts).length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Available</p>
          </CardContent>
        </Card>
      </div>

      {/* Job Type Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Job Type Distribution</CardTitle>
          <CardDescription>Breakdown of quantum job types executed</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(jobTypeCounts).map(([type, count]) => (
              <div key={type} className="p-4 rounded-lg border bg-card">
                <div className="text-sm text-muted-foreground capitalize">
                  {type.replace('_', ' ')}
                </div>
                <div className="text-2xl font-bold mt-1">{count}</div>
                <div className="text-xs text-muted-foreground mt-1">jobs</div>
              </div>
            ))}
            {Object.keys(jobTypeCounts).length === 0 && (
              <div className="col-span-4 text-center py-8 text-muted-foreground">
                No jobs yet
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Provider Utilization */}
      <Card>
        <CardHeader>
          <CardTitle>Provider Utilization</CardTitle>
          <CardDescription>Quantum computing provider usage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(providerCounts).map(([provider, count]) => {
              const percentage = (count / liveJobs.length) * 100;
              return (
                <div key={provider} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize">{provider}</span>
                    <span className="text-sm text-muted-foreground">
                      {count} jobs ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
            {Object.keys(providerCounts).length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No provider data yet
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Live Job Queue */}
      <Card>
        <CardHeader>
          <CardTitle>Live Job Queue</CardTitle>
          <CardDescription>Real-time quantum job execution feed</CardDescription>
        </CardHeader>
        <CardContent>
          {jobsLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading jobs...</div>
          ) : liveJobs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No jobs yet</div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {liveJobs.map((job) => (
                <div
                  key={job.job_id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-center space-x-3 flex-1">
                    <div className={`w-2 h-2 rounded-full ${
                      job.status === 'completed' ? 'bg-green-500' :
                      job.status === 'running' ? 'bg-yellow-500 animate-pulse' :
                      job.status === 'failed' ? 'bg-red-500' :
                      'bg-gray-500'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium capitalize truncate">
                          {job.job_type.replace('_', ' ')}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {job.provider}
                        </Badge>
                        <Badge
                          variant={
                            job.status === 'completed' ? 'default' :
                            job.status === 'running' ? 'secondary' :
                            'destructive'
                          }
                          className="text-xs"
                        >
                          {job.status}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {new Date(job.timestamp * 1000).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <div className="font-medium text-orange-500">
                      -{formatToken(job.veridicus_burned)} VDC
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {formatTime(job.execution_time_ms)}
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

