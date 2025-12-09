"use client";

import { useGovernanceProposals } from '@/lib/veridicus-data';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Vote, CheckCircle, XCircle, Clock } from 'lucide-react';
import { formatNumber } from '@/lib/utils';

export function GovernanceMonitor() {
  const { data: proposals, loading } = useGovernanceProposals();

  const formatToken = (value: number) => {
    return formatNumber(value, { maximumFractionDigits: 0 });
  };

  const activeProposals = proposals?.filter(p => p.status === 'active') || [];
  const passedProposals = proposals?.filter(p => p.status === 'passed') || [];
  const rejectedProposals = proposals?.filter(p => p.status === 'rejected') || [];

  const getProposalTypeLabel = (type: string) => {
    const types: Record<string, string> = {
      '0': 'Add Provider',
      '1': 'Update Burn Rates',
      '2': 'Treasury Allocation',
      '3': 'Phase 4 Node Rules',
    };
    return types[type] || `Type ${type}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'passed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="secondary">Active</Badge>;
      case 'passed':
        return <Badge variant="default" className="bg-green-500">Passed</Badge>;
      case 'rejected':
        return <Badge variant="destructive">Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Proposals</CardTitle>
            <Vote className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeProposals.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Open for voting</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Passed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{passedProposals.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Approved</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rejected</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{rejectedProposals.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Not approved</p>
          </CardContent>
        </Card>
      </div>

      {/* Active Proposals */}
      {activeProposals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Proposals</CardTitle>
            <CardDescription>Proposals currently open for voting</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {activeProposals.map((proposal) => {
                const totalVotes = proposal.votes_for + proposal.votes_against;
                const forPercentage = totalVotes > 0
                  ? (proposal.votes_for / totalVotes) * 100
                  : 0;

                return (
                  <div key={proposal.proposal_id} className="p-4 rounded-lg border bg-card">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          {getStatusIcon(proposal.status)}
                          <span className="font-medium">
                            {getProposalTypeLabel(proposal.proposal_type)}
                          </span>
                          {getStatusBadge(proposal.status)}
                        </div>
                        <p className="text-sm text-muted-foreground">{proposal.description}</p>
                        <p className="text-xs text-muted-foreground mt-2">
                          Created {new Date(proposal.created_at * 1000).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center space-x-4">
                          <span className="text-green-500">
                            For: {formatToken(proposal.votes_for)}
                          </span>
                          <span className="text-red-500">
                            Against: {formatToken(proposal.votes_against)}
                          </span>
                        </div>
                        <span className="text-muted-foreground">
                          {totalVotes} total votes
                        </span>
                      </div>
                      {totalVotes > 0 && (
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full transition-all"
                            style={{ width: `${forPercentage}%` }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Proposal History */}
      <Card>
        <CardHeader>
          <CardTitle>Proposal History</CardTitle>
          <CardDescription>All governance proposals</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading proposals...</div>
          ) : proposals && proposals.length > 0 ? (
            <div className="space-y-2">
              {proposals.map((proposal) => (
                <div
                  key={proposal.proposal_id}
                  className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-center space-x-3 flex-1">
                    {getStatusIcon(proposal.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">
                          {getProposalTypeLabel(proposal.proposal_type)}
                        </span>
                        {getStatusBadge(proposal.status)}
                      </div>
                      <p className="text-sm text-muted-foreground truncate mt-1">
                        {proposal.description}
                      </p>
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-sm">
                      <span className="text-green-500">{formatToken(proposal.votes_for)}</span>
                      {' / '}
                      <span className="text-red-500">{formatToken(proposal.votes_against)}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(proposal.created_at * 1000).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">No proposals yet</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

