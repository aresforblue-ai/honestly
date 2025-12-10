"use client";

import { useNetworkStats } from '@/lib/veridicus-data';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Users, TrendingUp, DollarSign, Activity } from 'lucide-react';
import { formatNumber } from '@/lib/utils';

export function NetworkStats() {
  const { data: stats, loading } = useNetworkStats();

  const formatToken = (value: number) => {
    return formatNumber(value, { maximumFractionDigits: 2 });
  };

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : formatToken(stats?.active_users || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Last 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transactions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : formatToken(stats?.total_transactions || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Job Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : formatToken(stats?.average_job_cost || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">VERIDICUS</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Network Growth</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">
              {loading ? '...' : stats?.network_growth && stats.network_growth.length > 0
                ? `${((stats.network_growth[stats.network_growth.length - 1].users / (stats.network_growth[0]?.users || 1) - 1) * 100).toFixed(1)}%`
                : '0%'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">30 day growth</p>
          </CardContent>
        </Card>
      </div>

      {/* Provider Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Provider Performance</CardTitle>
          <CardDescription>Quantum computing provider utilization and metrics</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading provider data...</div>
          ) : stats?.provider_utilization && stats.provider_utilization.length > 0 ? (
            <div className="space-y-4">
              {stats.provider_utilization.map((provider) => (
                <div key={provider.provider} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium capitalize">{provider.provider}</span>
                      <span className="text-sm text-muted-foreground">
                        {provider.jobs_count} jobs
                      </span>
                    </div>
                    <span className="text-sm font-medium">
                      {provider.utilization_percent.toFixed(1)}% utilization
                    </span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${provider.utilization_percent}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">No provider data yet</div>
          )}
        </CardContent>
      </Card>

      {/* Network Growth Chart */}
      {stats?.network_growth && stats.network_growth.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Network Growth Trend</CardTitle>
            <CardDescription>User and job growth over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.network_growth.slice(-7).map((point, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg border bg-card">
                  <div>
                    <div className="font-medium">{new Date(point.date).toLocaleDateString()}</div>
                    <div className="text-sm text-muted-foreground">
                      {point.jobs} jobs executed
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{point.users} users</div>
                    <div className="text-sm text-muted-foreground">Active</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

