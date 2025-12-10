"use client";

import { useTokenMetrics } from '@/lib/veridicus-data';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { formatNumber } from '@/lib/utils';

const COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b'];

export function TokenMetrics() {
  const { data: metrics, loading } = useTokenMetrics();

  const supplyData = metrics ? [
    { name: 'Community', value: 600_000, color: COLORS[0] },
    { name: 'Treasury', value: 300_000, color: COLORS[1] },
    { name: 'Team', value: 100_000, color: COLORS[2] },
  ] : [];

  const formatToken = (value: number) => {
    return formatNumber(value, { maximumFractionDigits: 0 });
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const circulatingSupply = metrics
    ? metrics.total_supply - metrics.total_burned
    : 0;

  const deflationRate = metrics
    ? ((metrics.total_burned / metrics.total_supply) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Supply Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Token Supply Distribution</CardTitle>
          <CardDescription>1,000,000 VERIDICUS total supply breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 rounded bg-blue-500" />
                      <span>Community Rewards</span>
                    </div>
                    <span className="font-medium">600,000 (60%)</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 rounded bg-violet-500" />
                      <span>Treasury</span>
                    </div>
                    <span className="font-medium">300,000 (30%)</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 rounded bg-amber-500" />
                      <span>Team</span>
                    </div>
                    <span className="font-medium">100,000 (10%)</span>
                  </div>
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={supplyData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {supplyData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Supply Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Total Supply</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : formatToken(metrics?.total_supply || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">VERIDICUS</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Circulating Supply</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : formatToken(circulatingSupply)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {loading ? '...' : formatPercent((circulatingSupply / (metrics?.total_supply || 1)) * 100)} of total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Total Burned</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-500">
              {loading ? '...' : formatToken(metrics?.total_burned || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {loading ? '...' : formatPercent(deflationRate)} deflation
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Burn Rates */}
      <Card>
        <CardHeader>
          <CardTitle>Burn Rates</CardTitle>
          <CardDescription>Token burn activity over different time periods</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border bg-card">
              <div className="text-sm text-muted-foreground">24 Hours</div>
              <div className="text-2xl font-bold mt-1">
                {loading ? '...' : formatToken(metrics?.burn_rate_24h || 0)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">VERIDICUS burned</div>
            </div>
            <div className="p-4 rounded-lg border bg-card">
              <div className="text-sm text-muted-foreground">7 Days</div>
              <div className="text-2xl font-bold mt-1">
                {loading ? '...' : formatToken(metrics?.burn_rate_7d || 0)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">VERIDICUS burned</div>
            </div>
            <div className="p-4 rounded-lg border bg-card">
              <div className="text-sm text-muted-foreground">30 Days</div>
              <div className="text-2xl font-bold mt-1">
                {loading ? '...' : formatToken(metrics?.burn_rate_30d || 0)}
              </div>
              <div className="text-xs text-muted-foreground mt-1">VERIDICUS burned</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

