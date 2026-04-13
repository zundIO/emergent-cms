import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../App.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container noise">
      <div className="login-card">
        {/* Logo */}
        <div className="mb-10">
          <h1 className="font-headline text-2xl font-bold tracking-tight" style={{ color: 'var(--on-surface)' }}>
            The Monolith
          </h1>
          <span className="text-xs font-semibold tracking-[0.15em] uppercase" style={{ color: 'var(--primary-2)' }}>
            CMS
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label
              className="block text-xs font-medium mb-1.5"
              style={{ color: 'var(--muted)' }}
              htmlFor="email"
            >
              EMAIL
            </label>
            <input
              id="email"
              data-testid="login-email-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@monolith.cms"
              className="w-full h-8 rounded-[4px] px-3 text-sm"
              style={{
                backgroundColor: 'var(--sunken)',
                color: 'var(--on-surface)',
                border: 'none',
                outline: 'none',
              }}
              required
            />
          </div>

          <div className="mb-8">
            <label
              className="block text-xs font-medium mb-1.5"
              style={{ color: 'var(--muted)' }}
              htmlFor="password"
            >
              PASSWORD
            </label>
            <input
              id="password"
              data-testid="login-password-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="w-full h-8 rounded-[4px] px-3 text-sm"
              style={{
                backgroundColor: 'var(--sunken)',
                color: 'var(--on-surface)',
                border: 'none',
                outline: 'none',
              }}
              required
            />
          </div>

          {error && (
            <div
              data-testid="login-error-message"
              className="mb-4 text-sm px-3 py-2 rounded-[4px]"
              style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            data-testid="login-form-submit-button"
            disabled={loading}
            className="gradient-btn w-full h-10 rounded-[4px] font-headline font-bold text-xs tracking-widest uppercase transition-transform duration-150"
            style={{ opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-xs text-center" style={{ color: 'var(--muted-2)' }}>
          Contact your administrator for access
        </p>
      </div>
    </div>
  );
}
