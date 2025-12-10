"use client";

import { useStakingMetrics } from '@/lib/veridicus-data';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatNumber } from '@/lib/utils';
import { TrendingUp, Award, Percent } from 'lucide-react';

export function StakingDashboard() {
  const { data: metrics, loading } = useStakingMetrics();

  const formatToken = (value: number) => {
    return formatNumber(value, { maximumFractionDigits: 2 });
  };

  const stakingTiers = [
    { name: 'Standard', threshold: 0, discount: 0, emoji: '⚪' },
    { name: 'Bronze', threshold: 1_000, discount: 20, emoji: '🥉' },
    { name: 'Silver', threshold: 5_000, discount: 40, emoji: '🥈' },
    { name: 'Gold', threshold: 20_000, discount: 60, emoji: '🥇' },
  ];

  return (
    <div className="space-y-6">
      {/* Total Staked */}
      <Card>
        <CardHeader>
          <CardTitle>Total Staked</CardTitle>
          <CardDescription>VERIDICUS tokens currently staked for fee discounts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-4xl font-bold">
            {loading ? '...' : formatToken(metrics?.total_staked || 0)}
          </div>
          <p className="text-muted-foreground mt-2">VERIDICUS staked</p>
        </CardContent>
      </Card>

      {/* Staking Tiers */}
      <Card>
        <CardHeader>
          <CardTitle>Staking Tiers</CardTitle>
          <CardDescription>Stake VERIDICUS to unlock fee discounts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stakingTiers.map((tier) => {
              const tierData = metrics?.staking_tiers?.find(t => t.tier.toLowerCase() === tier.name.toLowerCase());
              const count = tierData?.count || 0;
              const totalStaked = tierData?.total_staked || 0;

              return (
                <div
                  key={tier.name}
                  className="p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{tier.emoji}</span>
                      <span className="font-medium">{tier.name}</span>
                    </div>
                    {tier.discount > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {tier.discount}% off
                      </Badge>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground mb-2">
                    {tier.threshold > 0 ? `Stake ${formatToken(tier.threshold)}+ VDC` : 'No staking required'}
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Stakers:</span>
                      <span className="font-medium">{count}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total:</span>
                      <span className="font-medium">{formatToken(totalStaked)} VDC</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Fee Discount Calculator */}
      <Card>
        <CardHeader>
          <CardTitle>Fee Discount Calculator</CardTitle>
          <CardDescription>Calculate your potential savings based on staking amount</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 rounded-lg border bg-card">
              <div className="flex items-center space-x-2 mb-4">
                <Percent className="h-5 w-5 text-muted-foreground" />
                <span className="font-medium">Discount Tiers</span>
              </div>
              <div className="space-y-2">
                {stakingTiers.filter(t => t.discount > 0).map((tier) => (
                  <div key={tier.name} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span>{tier.emoji}</span>
                      <span className="text-sm">{tier.name} ({formatToken(tier.threshold)}+ VDC)</span>
                    </div>
                    <Badge variant="outline">{tier.discount}% discount</Badge>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-card">
              <div className="flex items-center space-x-2 mb-4">
                <TrendingUp className="h-5 w-5 text-muted-foreground" />
                <span className="font-medium">Example Savings</span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">10 VERIDICUS job (Bronze tier):</span>
                  <span className="font-medium">Save 2 VDC (20% off)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">50 VERIDICUS job (Gold tier):</span>
                  <span className="font-medium">Save 30 VDC (60% off)</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Staking Distribution */}
      {metrics?.staking_tiers && metrics.staking_tiers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Staking Distribution</CardTitle>
            <CardDescription>Breakdown of stakers by tier</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {metrics.staking_tiers.map((tier) => {
                const percentage = (tier.total_staked / (metrics.total_staked || 1)) * 100;
                return (
                  <div key={tier.tier} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Award className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{tier.tier}</span>
                        <Badge variant="outline" className="text-xs">
                          {tier.count} stakers
                        </Badge>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {formatToken(tier.total_staked)} VDC ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-violet-500 h-2 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

