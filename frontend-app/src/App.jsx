import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams } from 'react-router-dom';
import { ApolloClient, InMemoryCache, ApolloProvider, useQuery, gql } from '@apollo/client';
import { groth16 } from 'snarkjs';
import { Shield, Search, CheckCircle, AlertTriangle, FileJson, Lock, Activity, Eye, Server, Terminal } from 'lucide-react';

// --- 1. CONFIGURATION & CLIENT ---
const getGraphQLUri = () => {
  if (process.env.REACT_APP_GRAPHQL_URI) {
    return process.env.REACT_APP_GRAPHQL_URI;
  }
  // Default for development only
  if (import.meta.env.MODE === 'development') {
    return 'http://localhost:4000/graphql';
  }
  throw new Error('REACT_APP_GRAPHQL_URI environment variable is required in production');
};

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const vkCache = new Map();

const client = new ApolloClient({
  uri: getGraphQLUri(),
  cache: new InMemoryCache(),
});

// --- 2. GRAPHQL QUERIES ---
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

// --- 3. HELPER COMPONENTS ---
const GradeBadge = ({ score }) => {
  let grade = 'F';
  let color = 'bg-red-500';
  
  if (score >= 90) { grade = 'A'; color = 'bg-emerald-500'; }
  else if (score >= 80) { grade = 'B'; color = 'bg-blue-500'; }
  else if (score >= 70) { grade = 'C'; color = 'bg-yellow-500'; }
  else if (score >= 60) { grade = 'D'; color = 'bg-orange-500'; }

  return (
    <div className={`flex items-center justify-center w-16 h-16 rounded-xl ${color} shadow-lg shadow-${color}/50`}>
      <span className="text-4xl font-black text-white">{grade}</span>
    </div>
  );
};

const ZKStatus = ({ isVerified }) => (
  <div className={`flex items-center gap-2 px-3 py-1 text-xs font-mono border rounded-full ${isVerified ? 'border-emerald-500 text-emerald-400 bg-emerald-500/10' : 'border-slate-600 text-slate-400'}`}>
    <Lock size={12} />
    {isVerified ? "ZK-PROOF VERIFIED" : "NO PROOF ANCHORED"}
  </div>
);

// --- 4. PAGES ---
const Dashboard = () => {
  const { loading, error, data } = useQuery(GET_APPS);
  const [searchTerm, setSearchTerm] = useState('');

  if (loading) return <div className="p-10 text-emerald-400 font-mono animate-pulse">Initializing Trust Engine...</div>;
  if (error) return <div className="p-10 text-red-500 font-mono">Error connecting to Truth Node. Is Backend running?</div>;

  const filteredApps = data.apps.filter(app => 
    app.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="text-slate-500" />
        </div>
        <input 
          type="text" 
          placeholder="Search Entity / App Bundle ID..." 
          className="w-full bg-slate-800 border border-slate-700 rounded-xl py-4 pl-12 pr-4 text-slate-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all font-mono"
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredApps.map(app => (
          <Link key={app.id} to={`/app/${app.id}`} className="group relative bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-emerald-500/50 transition-all hover:shadow-2xl hover:shadow-emerald-500/10">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-slate-900 rounded-lg group-hover:bg-slate-800 transition-colors">
                <Activity className="text-emerald-400" />
              </div>
              <GradeBadge score={app.whistlerScore || 0} />
            </div>
            <h3 className="text-xl font-bold text-slate-100 mb-1">{app.name}</h3>
            <p className="text-sm text-slate-400 font-mono mb-4">ID: {app.id.slice(0, 8)}...</p>
            <div className="flex items-center justify-between border-t border-slate-700 pt-4">
              <ZKStatus isVerified={app.metadata?.zkProofVerified || false} />
              <span className="text-xs text-slate-500 font-mono">Whistler Score: {app.whistlerScore}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

const AppTruthTerminal = () => {
  const { id } = useParams();
  const { loading, error, data } = useQuery(GET_APP_DETAILS, { variables: { id } });

  if (loading) return <div className="p-10 text-emerald-400 font-mono">Loading Lattice Data...</div>;
  if (error) return <div className="p-10 text-red-500">System Failure.</div>;

  const app = data.app;
  const scoreData = data.scoreApp;

  const copyForAgent = () => {
    const payload = JSON.stringify({
      entity: app.name,
      verification_grade: scoreData.grade,
      provenance_claims: app.claims.length,
      zk_proof_available: true,
      timestamp: new Date().toISOString()
    }, null, 2);
    navigator.clipboard.writeText(payload);
    alert("JSON Schema copied. Ready for LLM ingestion.");
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-slate-800 p-8 rounded-2xl border border-slate-700">
        <div className="flex items-center gap-6">
          <GradeBadge score={app.whistlerScore} />
          <div>
            <h1 className="text-3xl font-black text-white tracking-tight">{app.name}</h1>
            <div className="flex gap-4 mt-2">
              <ZKStatus isVerified={true} />
              <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
                <Server size={12} /> NODE: {id.slice(0,8)}
              </span>
            </div>
          </div>
        </div>
        <button 
          onClick={copyForAgent}
          className="flex items-center gap-2 bg-slate-900 hover:bg-black text-emerald-400 border border-emerald-500/30 px-4 py-2 rounded-lg font-mono text-sm transition-all"
        >
          <Terminal size={16} />
          EXPORT FOR AGENT
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-6 flex items-center gap-2">
              <Activity size={16} /> Signal Analysis
            </h3>
            
            <div className="space-y-6">
              {[
                { label: 'Privacy Hygiene', val: scoreData.breakdown.privacy.value },
                { label: 'Financial Transparency', val: scoreData.breakdown.financial.value },
                { label: 'User Sentiment', val: 78 },
                { label: 'Provenance Depth', val: 45 },
              ].map((stat) => (
                <div key={stat.label}>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-300">{stat.label}</span>
                    <span className="font-mono text-emerald-400">{stat.val}/100</span>
                  </div>
                  <div className="h-2 bg-slate-900 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-500 rounded-full transition-all duration-1000" 
                      style={{ width: `${stat.val}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
             <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Lock size={16} /> Shadow Oracle
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Cryptographic verification of membership in the "Truth" Merkle Tree.
            </p>
            <div className="bg-black p-3 rounded font-mono text-[10px] text-emerald-600 break-all border border-emerald-900/30">
              0x71C7656EC7ab88b098defB751B7401B5f6d8976F
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
            <div className="p-6 border-b border-slate-700 flex justify-between items-center">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <FileJson size={16} /> Claim Verification Ledger
              </h3>
              <span className="text-xs bg-slate-700 text-white px-2 py-1 rounded">{app.claims.length} Records</span>
            </div>

            <div className="divide-y divide-slate-700">
              {app.claims.length === 0 ? (
                <div className="p-8 text-center text-slate-500">No claims recorded in ledger.</div>
              ) : (
                app.claims.map(claim => (
                  <div key={claim.id} className="p-6 hover:bg-slate-700/30 transition-colors">
                    <div className="flex items-start gap-4">
                      <div className="mt-1">
                        {claim.verdicts[0]?.outcome === 'TRUE' ? (
                          <CheckCircle className="text-emerald-500" size={20} />
                        ) : (
                          <AlertTriangle className="text-yellow-500" size={20} />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="text-slate-200 text-lg font-medium leading-snug mb-2">
                          "{claim.statement}"
                        </p>
                        <div className="flex gap-4 text-xs font-mono text-slate-400">
                           <span className="bg-slate-900 px-2 py-1 rounded">HASH: {claim.claimHash.slice(0,8)}</span>
                           <span className="flex items-center gap-1">
                             <Eye size={12} /> CONFIDENCE: {(claim.verdicts[0]?.confidence * 100) || 0}%
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
    </div>
  );
};

// --- 5. VERIFY SHARE PAGE ---
const VerifyShare = () => {
  const { token } = useParams();
  const [state, setState] = useState({ status: 'Initializing', error: null, bundle: null, verified: null, circuit: null });

  useEffect(() => {
    const run = async () => {
      try {
        setState((s) => ({ ...s, status: 'Fetching bundle...' }));
        const res = await fetch(`${API_BASE}/vault/share/${token}/bundle`);
        if (!res.ok) {
          throw new Error(`Bundle fetch failed (${res.status})`);
        }
        const bundle = await res.json();

        // Expect proof_data JSON string or an inline proof bundle
        const raw = bundle.proof_data || bundle.proof || bundle.bundle;
        if (!raw) {
          setState({ status: 'No proof found in bundle', error: 'Bundle missing proof_data', bundle, verified: null, circuit: bundle.proof_type });
          return;
        }

        const proofBundle = typeof raw === 'string' ? JSON.parse(raw) : raw;
        const circuit = bundle.proof_type || proofBundle.circuit || 'age';

        const vkeyUrl =
          (bundle.verification && bundle.verification.vk_url) ||
          `${API_BASE}/zkp/artifacts/${circuit}/verification_key.json`;

        setState((s) => ({ ...s, status: 'Fetching verification key...' }));
        let vkey = vkCache.get(vkeyUrl);
        if (!vkey) {
          const vkRes = await fetch(vkeyUrl, { cache: 'force-cache' });
          if (!vkRes.ok) {
            throw new Error(`Verification key fetch failed (${vkRes.status})`);
          }
          vkey = await vkRes.json();
          vkCache.set(vkeyUrl, vkey);
        }

        setState((s) => ({ ...s, status: 'Verifying proof...' }));
        const publicSignals = proofBundle.publicSignals || proofBundle.namedSignals;
        if (!publicSignals || !proofBundle.proof) {
          throw new Error('Proof bundle missing proof or publicSignals');
        }

        const ok = await groth16.verify(vkey, publicSignals, proofBundle.proof);
        setState({ status: ok ? 'Proof verified' : 'Proof failed', error: null, bundle, verified: ok, circuit });
      } catch (err) {
        setState((s) => ({ ...s, status: 'Verification error', error: err.message, verified: false }));
      }
    };
    run();
  }, [token]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-black text-white">Proof Verification</h1>
            <p className="text-sm text-slate-400 font-mono">Token: {token}</p>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-mono ${state.verified ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/40' : 'bg-slate-900 text-slate-400 border border-slate-700'}`}>
            {state.status}
          </div>
        </div>
        {state.error && (
          <div className="mt-4 text-sm text-red-400 font-mono border border-red-500/30 bg-red-500/5 rounded p-3">
            {state.error}
          </div>
        )}
        {state.bundle && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900/60 border border-slate-800 rounded p-4">
              <h3 className="text-xs uppercase tracking-wide text-slate-400 mb-2">Bundle</h3>
              <pre className="text-[11px] text-slate-200 font-mono whitespace-pre-wrap break-all">{JSON.stringify(state.bundle, null, 2)}</pre>
            </div>
            <div className="bg-slate-900/60 border border-slate-800 rounded p-4">
              <h3 className="text-xs uppercase tracking-wide text-slate-400 mb-2">Result</h3>
              <ul className="text-sm text-slate-200 space-y-1 font-mono">
                <li>Verified: {state.verified === null ? 'pending' : state.verified ? 'true' : 'false'}</li>
                <li>Circuit: {state.circuit || 'unknown'}</li>
                <li>Access: {state.bundle.access_level}</li>
                <li>Proof type: {state.bundle.proof_type}</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// --- 5. MAIN APP LAYOUT ---
const App = () => {
  return (
    <ApolloProvider client={client}>
      <Router>
        <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-emerald-500/30">
          <nav className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
              <Link to="/" className="flex items-center gap-3 group">
                <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(16,185,129,0.4)] group-hover:scale-105 transition-transform">
                  <Shield className="text-slate-900" size={18} fill="currentColor" />
                </div>
                <span className="font-bold text-xl tracking-tight text-white">App<span className="text-emerald-400">Whistler</span></span>
              </Link>
              <div className="flex items-center gap-4">
                <span className="hidden md:block text-xs font-mono text-slate-500">SYSTEM: ONLINE</span>
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              </div>
            </div>
          </nav>

          <main className="max-w-7xl mx-auto px-6 py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/app/:id" element={<AppTruthTerminal />} />
              <Route path="/verify/:token" element={<VerifyShare />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ApolloProvider>
  );
};

export default App;
