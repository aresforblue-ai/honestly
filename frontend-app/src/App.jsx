import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams, useNavigate } from 'react-router-dom';
import { ApolloClient, InMemoryCache, ApolloProvider, useQuery, gql } from '@apollo/client';
import { groth16 } from 'snarkjs';
import { 
  Shield, Search, CheckCircle, AlertTriangle, FileJson, Lock, Activity, 
  Eye, Server, Terminal, Zap, ArrowRight, ExternalLink, Copy, Check,
  Sparkles, Globe, TrendingUp, Users, ChevronRight, Menu, X, Github
} from 'lucide-react';

// ============================================
// CONFIGURATION
// ============================================
const getGraphQLUri = () => {
  if (import.meta.env.VITE_GRAPHQL_URI) return import.meta.env.VITE_GRAPHQL_URI;
  if (import.meta.env.MODE === 'development') return 'http://localhost:4000/graphql';
  return '/graphql';
};

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const vkCache = new Map();

const client = new ApolloClient({
  uri: getGraphQLUri(),
  cache: new InMemoryCache(),
});

// ============================================
// GRAPHQL QUERIES
// ============================================
const GET_APPS = gql`
  query GetApps {
    apps {
      id
      name
      whistlerScore
      metadata
    }
  }
`;

const GET_APP_DETAILS = gql`
  query GetAppDetails($id: ID!) {
    app(id: $id) {
      id
      name
      whistlerScore
      metadata
      claims {
        id
        statement
        claimHash
        verdicts {
          outcome
          confidence
        }
      }
      reviews {
        id
        rating
        sentiment
      }
    }
    scoreApp(appId: $id) {
      grade
      breakdown {
        privacy { value }
        financial { value }
      }
    }
  }
`;

// ============================================
// ANIMATED BACKGROUND COMPONENT
// ============================================
const AnimatedBackground = () => (
  <div className="fixed inset-0 -z-10 overflow-hidden">
    <div className="absolute inset-0 bg-mesh" />
    {/* Floating orbs */}
    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl animate-float" />
    <div className="absolute top-3/4 right-1/4 w-80 h-80 bg-purple-500/15 rounded-full blur-3xl animate-float" style={{ animationDelay: '-3s' }} />
    <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-violet-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '-1.5s' }} />
    {/* Grid overlay */}
    <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:64px_64px]" />
  </div>
);

// ============================================
// NAVIGATION
// ============================================
const Navigation = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      scrolled ? 'glass border-b border-slate-700/50' : ''
    }`}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30 group-hover:shadow-indigo-500/50 transition-all group-hover:scale-105">
              <Shield className="text-white" size={20} fill="currentColor" />
            </div>
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl blur opacity-30 group-hover:opacity-50 transition-opacity" />
          </div>
          <div>
            <span className="font-display font-bold text-xl text-white">
              App<span className="text-gradient">Whistler</span>
            </span>
            <div className="text-[10px] font-mono text-slate-500 tracking-wider">TRUTH ENGINE</div>
          </div>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-6">
          <Link to="/" className="text-sm text-slate-400 hover:text-white transition-colors">Dashboard</Link>
          <a href="#features" className="text-sm text-slate-400 hover:text-white transition-colors">Features</a>
          <a href="https://github.com" target="_blank" rel="noopener" className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-1">
            <Github size={14} /> GitHub
          </a>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-mono text-emerald-400">ONLINE</span>
          </div>
        </div>

        {/* Mobile Menu Button */}
        <button 
          className="md:hidden p-2 text-slate-400 hover:text-white"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden glass border-t border-slate-700/50 px-6 py-4 animate-fade-in">
          <div className="flex flex-col gap-4">
            <Link to="/" className="text-slate-300 hover:text-white">Dashboard</Link>
            <a href="#features" className="text-slate-300 hover:text-white">Features</a>
          </div>
        </div>
      )}
    </nav>
  );
};

// ============================================
// GRADE BADGE COMPONENT
// ============================================
const GradeBadge = ({ score, size = 'default' }) => {
  let grade = 'F';
  let gradientClass = 'from-red-500 to-red-600';
  let glowClass = 'shadow-red-500/50';
  
  if (score >= 90) { 
    grade = 'A'; 
    gradientClass = 'from-emerald-400 to-emerald-600'; 
    glowClass = 'shadow-emerald-500/50';
  } else if (score >= 80) { 
    grade = 'B'; 
    gradientClass = 'from-blue-400 to-blue-600'; 
    glowClass = 'shadow-blue-500/50';
  } else if (score >= 70) { 
    grade = 'C'; 
    gradientClass = 'from-yellow-400 to-yellow-600'; 
    glowClass = 'shadow-yellow-500/50';
  } else if (score >= 60) { 
    grade = 'D'; 
    gradientClass = 'from-orange-400 to-orange-600'; 
    glowClass = 'shadow-orange-500/50';
  }

  const sizeClasses = size === 'large' 
    ? 'w-20 h-20 text-5xl' 
    : 'w-14 h-14 text-3xl';

  return (
    <div className={`relative flex items-center justify-center ${sizeClasses} rounded-2xl bg-gradient-to-br ${gradientClass} shadow-lg ${glowClass}`}>
      <span className="font-display font-black text-white">{grade}</span>
      <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${gradientClass} blur-xl opacity-50`} />
    </div>
  );
};

// ============================================
// ZK STATUS COMPONENT
// ============================================
const ZKStatus = ({ isVerified }) => (
  <div className={`flex items-center gap-2 px-3 py-1.5 text-xs font-mono rounded-full transition-all ${
    isVerified 
      ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400' 
      : 'bg-slate-800/50 border border-slate-700/50 text-slate-500'
  }`}>
    <Lock size={12} className={isVerified ? 'text-emerald-400' : ''} />
    {isVerified ? "ZK-VERIFIED" : "UNVERIFIED"}
  </div>
);

// ============================================
// STATS COUNTER
// ============================================
const StatCounter = ({ value, label, icon: Icon }) => {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    const duration = 2000;
    const steps = 60;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [value]);

  return (
    <div className="text-center">
      <div className="flex items-center justify-center gap-2 mb-2">
        <Icon className="text-indigo-400" size={20} />
        <span className="text-3xl font-display font-bold text-white">{count}+</span>
      </div>
      <p className="text-sm text-slate-400">{label}</p>
    </div>
  );
};

// ============================================
// LANDING PAGE / HERO
// ============================================
const LandingHero = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-[90vh] flex flex-col items-center justify-center text-center px-6 py-20">
      {/* Badge */}
      <div className="animate-fade-up opacity-0 stagger-1" style={{ animationFillMode: 'forwards' }}>
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-indigo-500/30 mb-8">
          <Sparkles className="text-indigo-400" size={14} />
          <span className="text-sm text-slate-300">Zero-Knowledge Identity Verification</span>
        </div>
      </div>

      {/* Main Heading */}
      <h1 className="animate-fade-up opacity-0 stagger-2 font-display text-5xl md:text-7xl font-bold mb-6 leading-tight" style={{ animationFillMode: 'forwards' }}>
        <span className="text-white">Trust, but </span>
        <span className="text-gradient">Verify</span>
        <br />
        <span className="text-slate-400 text-3xl md:text-5xl">with Cryptographic Proof</span>
      </h1>

      {/* Subtitle */}
      <p className="animate-fade-up opacity-0 stagger-3 max-w-2xl text-lg text-slate-400 mb-10" style={{ animationFillMode: 'forwards' }}>
        AppWhistler is the truth engine for the AI age. Verify entity claims, audit app behaviors, 
        and share proof bundles—all powered by Groth16 zero-knowledge proofs.
      </p>

      {/* CTA Buttons */}
      <div className="animate-fade-up opacity-0 stagger-4 flex flex-col sm:flex-row gap-4 mb-16" style={{ animationFillMode: 'forwards' }}>
        <button 
          onClick={() => navigate('/')}
          className="btn-primary flex items-center gap-2 text-lg"
        >
          Launch Dashboard
          <ArrowRight size={18} />
        </button>
        <a 
          href="https://docs.honestly.dev"
          target="_blank"
          rel="noopener"
          className="btn-ghost flex items-center gap-2 text-lg"
        >
          Documentation
          <ExternalLink size={16} />
        </a>
      </div>

      {/* Stats */}
      <div className="animate-fade-up opacity-0 stagger-5 grid grid-cols-3 gap-8 md:gap-16" style={{ animationFillMode: 'forwards' }}>
        <StatCounter value={1200} label="Entities Verified" icon={Shield} />
        <StatCounter value={50000} label="Proofs Generated" icon={Zap} />
        <StatCounter value={99} label="Accuracy Rate %" icon={TrendingUp} />
      </div>
    </div>
  );
};

// ============================================
// DASHBOARD
// ============================================
const Dashboard = () => {
  const { loading, error, data } = useQuery(GET_APPS);
  const [searchTerm, setSearchTerm] = useState('');
  const inputRef = useRef(null);

  // Focus search on Cmd/Ctrl+K
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400 font-mono">Initializing Truth Engine<span className="loading-dots" /></p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="glass-card p-8 text-center max-w-md">
          <AlertTriangle className="text-red-400 mx-auto mb-4" size={48} />
          <h3 className="text-xl font-bold text-white mb-2">Connection Failed</h3>
          <p className="text-slate-400 mb-4">Unable to connect to the Truth Engine. Is the backend running?</p>
          <button 
            onClick={() => window.location.reload()} 
            className="btn-ghost text-sm"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const filteredApps = data.apps.filter(app => 
    app.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-display font-bold text-white">Entity Registry</h2>
          <p className="text-slate-400">{data.apps.length} verified entities in the trust lattice</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="badge badge-info">
            <Activity size={12} className="mr-1" /> Live
          </span>
        </div>
      </div>

      {/* Search */}
      <div className="relative group">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="text-slate-500 group-focus-within:text-indigo-400 transition-colors" size={20} />
        </div>
        <input 
          ref={inputRef}
          type="text" 
          placeholder="Search entities, bundle IDs..." 
          className="input-dark pl-12 pr-24"
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
          <kbd className="hidden sm:inline-flex px-2 py-1 text-[10px] font-mono text-slate-500 bg-slate-800 rounded border border-slate-700">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredApps.map((app, idx) => (
          <Link 
            key={app.id} 
            to={`/app/${app.id}`} 
            className="glass-card p-6 group animate-fade-up opacity-0"
            style={{ 
              animationDelay: `${idx * 0.05}s`,
              animationFillMode: 'forwards'
            }}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 rounded-xl bg-slate-800/80 group-hover:bg-indigo-500/20 transition-colors">
                <Activity className="text-indigo-400" size={20} />
              </div>
              <GradeBadge score={app.whistlerScore || 0} />
            </div>
            
            <h3 className="text-xl font-display font-bold text-white mb-1 group-hover:text-indigo-300 transition-colors">
              {app.name}
            </h3>
            <p className="text-sm text-slate-500 font-mono mb-4">
              {app.id.slice(0, 12)}...
            </p>
            
            <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
              <ZKStatus isVerified={app.metadata?.zkProofVerified} />
              <div className="flex items-center gap-1 text-xs text-slate-500">
                <span>{app.whistlerScore}</span>
                <ChevronRight size={14} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Link>
        ))}
      </div>

      {filteredApps.length === 0 && (
        <div className="text-center py-16">
          <Globe className="mx-auto text-slate-600 mb-4" size={48} />
          <p className="text-slate-400">No entities match your search</p>
        </div>
      )}
    </div>
  );
};

// ============================================
// APP DETAIL PAGE
// ============================================
const AppDetail = () => {
  const { id } = useParams();
  const { loading, error, data } = useQuery(GET_APP_DETAILS, { variables: { id } });
  const [copied, setCopied] = useState(false);

  const copyForAgent = () => {
    if (!data?.app) return;
    const payload = JSON.stringify({
      entity: data.app.name,
      verification_grade: data.scoreApp?.grade,
      provenance_claims: data.app.claims.length,
      zk_proof_available: true,
      timestamp: new Date().toISOString()
    }, null, 2);
    navigator.clipboard.writeText(payload);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400 font-mono">Loading entity data<span className="loading-dots" /></p>
        </div>
      </div>
    );
  }

  if (error || !data?.app) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <AlertTriangle className="text-red-400 mx-auto mb-4" size={48} />
          <h3 className="text-xl font-bold text-white mb-2">Entity Not Found</h3>
          <Link to="/" className="btn-ghost text-sm mt-4 inline-block">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const { app, scoreApp } = data;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header Card */}
      <div className="glass-card p-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="flex items-center gap-6">
            <GradeBadge score={app.whistlerScore} size="large" />
            <div>
              <h1 className="text-3xl font-display font-bold text-white mb-2">{app.name}</h1>
              <div className="flex flex-wrap gap-3">
                <ZKStatus isVerified={true} />
                <span className="badge badge-info">
                  <Server size={12} className="mr-1" />
                  {id.slice(0, 8)}
                </span>
              </div>
            </div>
          </div>
          <button 
            onClick={copyForAgent}
            className="btn-ghost flex items-center gap-2"
          >
            {copied ? <Check size={16} className="text-emerald-400" /> : <Copy size={16} />}
            {copied ? 'Copied!' : 'Export for Agent'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Signal Analysis */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-6 flex items-center gap-2">
            <Activity size={16} /> Signal Analysis
          </h3>
          <div className="space-y-6">
            {[
              { label: 'Privacy Hygiene', val: scoreApp?.breakdown?.privacy?.value || 75 },
              { label: 'Financial Transparency', val: scoreApp?.breakdown?.financial?.value || 70 },
              { label: 'User Sentiment', val: 78 },
              { label: 'Provenance Depth', val: 45 },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-300">{stat.label}</span>
                  <span className="font-mono text-indigo-400">{Math.round(stat.val)}/100</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000" 
                    style={{ width: `${stat.val}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Claims Ledger */}
        <div className="lg:col-span-2 glass-card overflow-hidden">
          <div className="p-6 border-b border-slate-700/50 flex justify-between items-center">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <FileJson size={16} /> Claim Verification Ledger
            </h3>
            <span className="badge badge-info">{app.claims.length} Records</span>
          </div>
          
          <div className="divide-y divide-slate-800/50 max-h-96 overflow-y-auto">
            {app.claims.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                No claims recorded in ledger
              </div>
            ) : (
              app.claims.map(claim => (
                <div key={claim.id} className="p-6 hover:bg-slate-800/30 transition-colors">
                  <div className="flex items-start gap-4">
                    <div className="mt-1">
                      {claim.verdicts[0]?.outcome === 'TRUE' ? (
                        <CheckCircle className="text-emerald-500" size={20} />
                      ) : (
                        <AlertTriangle className="text-yellow-500" size={20} />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="text-slate-200 font-medium mb-2">"{claim.statement}"</p>
                      <div className="flex flex-wrap gap-2 text-xs font-mono">
                        <span className="px-2 py-1 rounded bg-slate-800/60 text-slate-400">
                          HASH: {claim.claimHash?.slice(0, 8) || 'N/A'}
                        </span>
                        <span className="flex items-center gap-1 text-slate-400">
                          <Eye size={12} />
                          {Math.round((claim.verdicts[0]?.confidence || 0) * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================
// VERIFY SHARE PAGE
// ============================================
const VerifyShare = () => {
  const { token } = useParams();
  const [state, setState] = useState({ 
    status: 'Initializing', 
    error: null, 
    bundle: null, 
    verified: null, 
    circuit: null 
  });

  useEffect(() => {
    const run = async () => {
      try {
        setState(s => ({ ...s, status: 'Fetching bundle...' }));
        const res = await fetch(`${API_BASE}/vault/share/${token}/bundle`);
        if (!res.ok) throw new Error(`Bundle fetch failed (${res.status})`);
        const bundle = await res.json();

        const raw = bundle.proof_data || bundle.proof || bundle.bundle;
        if (!raw) {
          setState({ status: 'No proof found', error: 'Bundle missing proof_data', bundle, verified: null, circuit: bundle.proof_type });
          return;
        }

        const proofBundle = typeof raw === 'string' ? JSON.parse(raw) : raw;
        const circuit = bundle.proof_type || proofBundle.circuit || 'age';
        const vkeyUrl = bundle.verification?.vk_url || `${API_BASE}/zkp/artifacts/${circuit}/verification_key.json`;

        setState(s => ({ ...s, status: 'Fetching verification key...' }));
        let vkey = vkCache.get(vkeyUrl);
        if (!vkey) {
          const vkRes = await fetch(vkeyUrl, { cache: 'force-cache' });
          if (!vkRes.ok) throw new Error(`Verification key fetch failed (${vkRes.status})`);
          vkey = await vkRes.json();
          vkCache.set(vkeyUrl, vkey);
        }

        setState(s => ({ ...s, status: 'Verifying proof...' }));
        const publicSignals = proofBundle.publicSignals || proofBundle.namedSignals;
        if (!publicSignals || !proofBundle.proof) throw new Error('Proof bundle missing proof or publicSignals');

        const ok = await groth16.verify(vkey, publicSignals, proofBundle.proof);
        setState({ status: ok ? 'Proof verified!' : 'Verification failed', error: null, bundle, verified: ok, circuit });
      } catch (err) {
        setState(s => ({ ...s, status: 'Error', error: err.message, verified: false }));
      }
    };
    run();
  }, [token]);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="glass-card p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-display font-bold text-white">Proof Verification</h1>
            <p className="text-sm text-slate-500 font-mono">Token: {token}</p>
          </div>
          <div className={`badge ${state.verified ? 'badge-success' : state.verified === false ? 'badge-danger' : 'badge-info'}`}>
            {state.verified && <CheckCircle size={12} className="mr-1" />}
            {state.status}
          </div>
        </div>

        {state.error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-mono mb-6">
            {state.error}
          </div>
        )}

        {state.bundle && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
              <h3 className="text-xs uppercase tracking-wide text-slate-400 mb-2">Bundle Data</h3>
              <pre className="text-[11px] text-slate-300 font-mono whitespace-pre-wrap break-all max-h-64 overflow-y-auto">
                {JSON.stringify(state.bundle, null, 2)}
              </pre>
            </div>
            <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
              <h3 className="text-xs uppercase tracking-wide text-slate-400 mb-2">Verification Result</h3>
              <ul className="text-sm text-slate-300 space-y-2 font-mono">
                <li className="flex justify-between">
                  <span className="text-slate-500">Verified</span>
                  <span className={state.verified ? 'text-emerald-400' : 'text-red-400'}>
                    {state.verified === null ? 'pending' : state.verified.toString()}
                  </span>
                </li>
                <li className="flex justify-between">
                  <span className="text-slate-500">Circuit</span>
                  <span>{state.circuit || 'unknown'}</span>
                </li>
                <li className="flex justify-between">
                  <span className="text-slate-500">Access</span>
                  <span>{state.bundle.access_level || 'N/A'}</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================
// MAIN APP
// ============================================
const App = () => {
  return (
    <ApolloProvider client={client}>
      <Router>
        <div className="min-h-screen text-slate-200 selection:bg-indigo-500/30">
          <AnimatedBackground />
          <Navigation />
          
          <main className="max-w-7xl mx-auto px-6 pt-24 pb-16">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/welcome" element={<LandingHero />} />
              <Route path="/app/:id" element={<AppDetail />} />
              <Route path="/verify/:token" element={<VerifyShare />} />
            </Routes>
          </main>

          {/* Footer */}
          <footer className="border-t border-slate-800/50 py-8">
            <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-2 text-slate-500 text-sm">
                <Shield size={16} className="text-indigo-400" />
                <span>AppWhistler Truth Engine</span>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-600">
                <span>Powered by Groth16 ZK-SNARKs</span>
                <span>•</span>
                <span>Poseidon Hash</span>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </ApolloProvider>
  );
};

export default App;
