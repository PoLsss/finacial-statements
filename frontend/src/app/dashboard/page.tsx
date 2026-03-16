'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getDashboard, getStatus } from '@/lib/api';
import type { DashboardData, StatusData } from '@/types/api';
import {
  Database,
  Layers,
  DollarSign,
  Hash,
  RefreshCw,
  CheckCircle,
  XCircle,
  Activity,
} from 'lucide-react';

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [status, setStatus] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashRes, statusRes] = await Promise.all([getDashboard(), getStatus()]);
      if (dashRes.success && dashRes.data) setDashboard(dashRes.data);
      if (statusRes.success && statusRes.data) setStatus(statusRes.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="container py-6">
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">System performance and monitoring overview</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchData}
          disabled={loading}
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={<Database className="h-5 w-5" />}
          title="Documents"
          value={dashboard?.total_documents ?? 0}
          description="Financial reports in database"
          gradient="from-blue-500 to-blue-600"
          loading={loading}
        />
        <MetricCard
          icon={<Layers className="h-5 w-5" />}
          title="Chunks"
          value={dashboard?.total_chunks ?? 0}
          description="Text chunks stored"
          gradient="from-teal-500 to-teal-600"
          loading={loading}
        />
        <MetricCard
          icon={<DollarSign className="h-5 w-5" />}
          title="Estimated Cost"
          value={`$${(dashboard?.total_cost ?? 0).toFixed(4)}`}
          description="Total API cost"
          gradient="from-amber-500 to-amber-600"
          loading={loading}
        />
        <MetricCard
          icon={<Hash className="h-5 w-5" />}
          title="Tokens"
          value={(dashboard?.total_tokens ?? 0).toLocaleString()}
          description="Total tokens consumed"
          gradient="from-purple-500 to-purple-600"
          loading={loading}
        />
      </div>

      {/* Services Status */}
      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Activity className="h-5 w-5 text-primary" />
            Service Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <ServiceStatus
              name="OpenAI"
              active={status?.services?.openai ?? false}
              loading={loading}
            />
            <ServiceStatus
              name="Landing AI"
              active={status?.services?.landing_ai ?? false}
              loading={loading}
            />
            <ServiceStatus
              name="MongoDB"
              active={status?.services?.mongodb ?? false}
              loading={loading}
            />
          </div>
          {status && (
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-border">
              <div className="text-sm">
                <span className="text-muted-foreground">Embedding Model:</span>{' '}
                <span className="font-medium">{status.embedding_model}</span>
              </div>
              <div className="text-sm">
                <span className="text-muted-foreground">LLM Model:</span>{' '}
                <span className="font-medium">{status.llm_model}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-lg">Embeddings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">
              {loading ? '...' : (dashboard?.total_embeddings ?? 0).toLocaleString()}
            </div>
            <p className="text-sm text-muted-foreground mt-1">Vector embeddings stored</p>
          </CardContent>
        </Card>
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle className="text-lg">Database Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {status?.database_initialized ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-lg font-medium text-green-600">Initialized</span>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-yellow-500" />
                  <span className="text-lg font-medium text-yellow-600">
                    {loading ? 'Loading...' : 'Not Initialized'}
                  </span>
                </>
              )}
            </div>
            <p className="text-sm text-muted-foreground mt-1">MongoDB Atlas connection</p>
          </CardContent>
        </Card>
      </div>
    </div>
    </div>
  );
}

function MetricCard({
  icon,
  title,
  value,
  description,
  gradient,
  loading,
}: {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  description: string;
  gradient: string;
  loading: boolean;
}) {
  return (
    <Card className="border-primary/10 hover:shadow-lg transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className={`bg-gradient-to-br ${gradient} p-3 rounded-xl text-white shadow-lg`}>
            {icon}
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">
              {loading ? '...' : value}
            </p>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-3">{description}</p>
      </CardContent>
    </Card>
  );
}

function ServiceStatus({
  name,
  active,
  loading,
}: {
  name: string;
  active: boolean;
  loading: boolean;
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      {loading ? (
        <div className="h-3 w-3 rounded-full bg-gray-300 animate-pulse" />
      ) : active ? (
        <div className="h-3 w-3 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
      ) : (
        <div className="h-3 w-3 rounded-full bg-red-400" />
      )}
      <span className="text-sm font-medium">{name}</span>
      <span className={`text-xs ml-auto ${active ? 'text-green-600' : 'text-muted-foreground'}`}>
        {loading ? '...' : active ? 'Active' : 'Inactive'}
      </span>
    </div>
  );
}
