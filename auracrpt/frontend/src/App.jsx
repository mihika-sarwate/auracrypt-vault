import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { UploadCloud, Download, LogIn, UserPlus, Shield, Lock, FileAudio, LogOut, CheckCircle2 } from 'lucide-react';
import { supabase } from './supabase';
import './index.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Sender');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      if (isLogin) {
        // --- LOGIN ---
        const { data, error: authError } = await supabase.auth.signInWithPassword({
          email, password
        });
        if (authError) throw authError;

        // Fetch profile to get role
        const { data: profile, error: profileError } = await supabase
          .from('profiles')
          .select('role')
          .eq('id', data.user.id)
          .single();
        
        if (profileError) throw new Error("Profile not found. Please contact admin.");

        onLogin(data.session.access_token, profile.role, data.user.id);
      } else {
        // --- REGISTER ---
        const { data, error: authError } = await supabase.auth.signUp({
          email, password
        });
        if (authError) throw authError;
        if (!data.user) throw new Error("Signup failed");

        // Initialize Identity Vault on Backend (Generate keys, etc.)
        const setupRes = await fetch(`${API_URL}/auth/setup`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${data.session.access_token}`
          },
          body: JSON.stringify({ username, role })
        });
        
        const setupData = await setupRes.json();
        if (!setupRes.ok) throw new Error(setupData.error);

        alert('Identity Vault Initialized! Please check your email for verification (if enabled) and then log in.');
        setIsLogin(true);
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="glass-card" style={{ maxWidth: 400, margin: '2rem auto' }}>
      <h2 style={{ marginBottom: '1.5rem', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {isLogin ? <><LogIn style={{ marginRight: '8px' }}/> Vault Login</> : <><UserPlus style={{ marginRight: '8px' }}/> Create Identity</>}
      </h2>
      {error && <div style={{ color: 'var(--danger)', marginBottom: '1rem', textAlign: 'center' }}>{error}</div>}
      <form onSubmit={handleSubmit}>
        <input className="input-field" type="email" placeholder="Email Address" required value={email} onChange={e => setEmail(e.target.value)} />
        {!isLogin && (
          <input className="input-field" placeholder="Public Identity (Username)" required value={username} onChange={e => setUsername(e.target.value)} />
        )}
        <input className="input-field" type="password" placeholder="Passphrase" required value={password} onChange={e => setPassword(e.target.value)} />
        {!isLogin && (
          <select className="input-field" value={role} onChange={e => setRole(e.target.value)}>
            <option value="Sender">Sender (Encrypt & Embed)</option>
            <option value="Receiver">Receiver (Extract & Decrypt)</option>
          </select>
        )}
        <button className="btn-primary" type="submit" style={{ marginTop: '1rem' }} disabled={loading}>
           {loading ? 'Processing...' : (isLogin ? 'Authenticate' : 'Secure Register')}
        </button>
      </form>
      <div style={{ marginTop: '1rem', textAlign: 'center' }}>
        <span className="nav-span" onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? 'Need an account? Register' : 'Already have access? Login'}
        </span>
      </div>
    </div>
  );
}

function SenderDashboard({ token }) {
  const [receivers, setReceivers] = useState([]);
  const [recipient, setRecipient] = useState('');
  const [message, setMessage] = useState('');
  const [file, setFile] = useState(null);
  const [autoGen, setAutoGen] = useState(false);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef();

  useEffect(() => {
    fetch(`${API_URL}/users/receivers`, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => res.json())
      .then(data => {
         if (Array.isArray(data)) {
            setReceivers(data);
            if(data.length > 0) setRecipient(data[0].id);
         }
      }).catch(console.error);
  }, [token]);

  const handleEmbed = async (e) => {
    e.preventDefault();
    if ((!autoGen && !file) || !message || !recipient) return alert('Fill all required fields');
    
    const formData = new FormData();
    if (file && !autoGen) formData.append('audio', file);
    formData.append('message', message);
    formData.append('recipientId', recipient);
    if (autoGen) formData.append('autoGenerate', 'true');

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/vault/embed`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to embed');
      
      alert(data.message || 'Payload dispatched successfully!');
      setFile(null); setMessage('');
    } catch(err) {
      alert(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="glass-card">
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center' }}>
        <Lock style={{ marginRight: '10px' }}/> Encode Audio Vault
      </h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        Encrypt a text payload using RSA and dispatch it securely to the receiver's inbox inside an audio file.
      </p>

      <form onSubmit={handleEmbed}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Target Receiver</label>
          <select className="input-field" value={recipient} onChange={e => setRecipient(e.target.value)}>
            {receivers.map(r => <option key={r.id} value={r.id}>{r.username}</option>)}
            {receivers.length === 0 && <option value="">No receivers available</option>}
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Top Secret Payload</label>
          <textarea className="input-field" rows="4" placeholder="Enter strictly confidential text..." 
             value={message} onChange={e => setMessage(e.target.value)} required />
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
           <button type="button" className={`btn-primary ${autoGen ? '' : 'inactive'}`} 
              onClick={() => setAutoGen(true)} style={{ flex: 1, opacity: autoGen ? 1 : 0.6, background: autoGen ? 'var(--accent-primary)' : 'var(--glass-border)', color: autoGen ? '#111111' : 'var(--text-primary)' }}>
              Auto-Generate Carrier Audio
           </button>
           <button type="button" className={`btn-primary ${!autoGen ? '' : 'inactive'}`}
              onClick={() => setAutoGen(false)} style={{ flex: 1, opacity: !autoGen ? 1 : 0.6, background: !autoGen ? 'var(--accent-primary)' : 'var(--glass-border)', color: !autoGen ? '#111111' : 'var(--text-primary)' }}>
              Upload Custom WAV
           </button>
        </div>

        {!autoGen && (
          <div className="file-drop" onClick={() => fileInputRef.current.click()}>
            <input type="file" accept=".wav" ref={fileInputRef} style={{ display: 'none' }} 
               onChange={e => setFile(e.target.files[0])} />
            <UploadCloud size={48} style={{ margin: '0 auto', color: 'var(--accent-primary)', marginBottom: '1rem' }}/>
            <h3>{file ? file.name : 'Select standard WAV Carrier File'}</h3>
            <p style={{ color: 'var(--text-secondary)' }}>Must be uncompressed PCM Audio</p>
          </div>
        )}

        <button className="btn-primary" type="submit" disabled={loading || receivers.length === 0}>
          {loading ? 'Encrypting & Dispatching...' : 'Dispatch Payload to Inbox'}
        </button>
      </form>
    </div>
  );
}

function ReceiverDashboard({ token }) {
  const [inbox, setInbox] = useState([]);
  const [secret, setSecret] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchInbox();
  }, []);

  const fetchInbox = () => {
    fetch(`${API_URL}/vault/inbox`, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setInbox(data);
      })
      .catch(console.error);
  };

  const handleExtractAndBurn = async (messageId) => {
    setLoading(true); setSecret('');

    try {
      const res = await fetch(`${API_URL}/vault/extract`, {
        method: 'POST',
        headers: { 
           'Authorization': `Bearer ${token}`,
           'Content-Type': 'application/json'
        },
        body: JSON.stringify({ messageId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      
      setSecret(data.secret);
      // Remove from inbox visually
      setInbox(inbox.filter(m => m.id !== messageId));
    } catch(err) {
      alert(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="glass-card" style={{ maxWidth: 600 }}>
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center' }}>
        <Shield style={{ marginRight: '10px' }}/> Secure Inbox
      </h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        Incoming classified transmissions. Extracting the payload will trigger immediate cryptographic destruction of the host file.
      </p>

      {inbox.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
             <CheckCircle2 size={48} style={{ margin: '0 auto', marginBottom: '1rem', opacity: 0.5 }}/>
             <p>No pending transmissions. Inbox is secure.</p>
          </div>
      ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
             {inbox.map(msg => (
                <div key={msg.id} style={{ display: 'flex', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '8px', alignItems: 'center', justifyContent: 'space-between', border: '1px solid var(--glass-border)' }}>
                   <div>
                       <h4 style={{ margin: 0, color: 'var(--text-primary)' }}>From: {msg.senderName}</h4>
                       <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{new Date(msg.uploaded_at).toLocaleString()}</span>
                   </div>
                   <button className="btn-primary" 
                      onClick={() => handleExtractAndBurn(msg.id)} 
                      disabled={loading}
                      style={{ padding: '0.5rem 1rem', background: 'var(--danger)', color: 'white' }}>
                      {loading ? 'Decrypting...' : 'Extract & Burn'}
                   </button>
                </div>
             ))}
          </div>
      )}

      {secret && (
        <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(34, 197, 94, 0.1)', border: '1px solid var(--success)', borderRadius: '12px', animation: 'fadeIn 0.5s ease-out' }}>
          <h3 style={{ color: 'var(--success)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center' }}>
            <Lock size={18} style={{ marginRight: '8px' }}/> Unlocked Transmission
          </h3>
          <p style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {secret}
          </p>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [role, setRole] = useState(localStorage.getItem('role') || '');
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '');

  const login = (jwt, userRole, uId) => {
    localStorage.setItem('token', jwt);
    localStorage.setItem('role', userRole);
    localStorage.setItem('userId', uId);
    setToken(jwt); setRole(userRole); setUserId(uId);
  };
  
  const logout = async () => {
    await supabase.auth.signOut();
    localStorage.clear();
    setToken(''); setRole(''); setUserId('');
  };

  return (
    <Router>
      <div className="app-wrapper">
        <header className="header">
          <div className="logo"><Shield className="inline" style={{ verticalAlign: 'middle', marginRight: '8px' }} size={28}/> AuraCrypt</div>
          {token && (
            <span className="nav-span" style={{ display: 'flex', alignItems: 'center' }} onClick={logout}>
              <LogOut style={{ marginRight: '8px' }} size={18}/> Disconnect [{role}]
            </span>
          )}
        </header>

        <main className="container">
          <Routes>
            <Route path="/" element={token ? <Navigate to="/dashboard" /> : <Auth onLogin={login} />} />
            <Route path="/dashboard" element={
              !token ? <Navigate to="/" /> : 
              (role === 'Sender' ? <SenderDashboard token={token} /> : <ReceiverDashboard token={token} />)
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
