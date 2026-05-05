import React, { useState, useEffect } from 'react';
import { Download, RefreshCw, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../lib/api';

const API_BASE = process.env.REACT_APP_CMS_API_BASE || '/api/cms';

/**
 * Polls the CMS for available updates and exposes a small badge in the TopBar.
 * Click → modal that confirms upgrade. POST /system/upgrade triggers
 * install.sh --upgrade in the background. The backend restarts ~30s later.
 */
const UpdateChecker = () => {
  const [status, setStatus] = useState(null); // {update_available, current_short, latest_short, ref}
  const [showModal, setShowModal] = useState(false);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.get(`${API_BASE}/system/check-update`);
        setStatus(res.data);
      } catch (err) {
        // Silently fail — admin endpoint, may 401 for editors
      }
    };
    check();
    const id = setInterval(check, 30 * 60 * 1000); // every 30 min
    return () => clearInterval(id);
  }, []);

  const handleUpgrade = async () => {
    setUpgrading(true);
    try {
      const res = await api.post(`${API_BASE}/system/upgrade`);
      toast.success('Upgrade started', {
        description: 'The CMS will restart in ~30 seconds. The page will reload automatically.',
        duration: 30000,
      });
      // Auto-reload after backend restart window
      setTimeout(() => window.location.reload(), 35000);
    } catch (err) {
      setUpgrading(false);
      toast.error('Upgrade failed', {
        description: err.response?.data?.detail || err.message,
      });
    }
  };

  if (!status || !status.update_available) return null;

  return (
    <>
      {/* Compact badge in TopBar */}
      <button
        data-testid="cms-update-badge"
        onClick={() => setShowModal(true)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-[4px] text-xs font-medium transition-colors duration-150 hover:opacity-80"
        style={{
          backgroundColor: 'rgba(245, 158, 11, 0.15)',
          color: '#fbbf24',
          border: '1px solid rgba(245, 158, 11, 0.3)',
        }}
        title={`Update available: ${status.current_short} → ${status.latest_short}`}
      >
        <Download size={12} />
        Update
      </button>

      {/* Modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ backgroundColor: 'rgba(0,0,0,0.7)' }}
          onClick={() => !upgrading && setShowModal(false)}
        >
          <div
            data-testid="cms-update-modal"
            onClick={(e) => e.stopPropagation()}
            className="rounded-[6px] p-6 max-w-md w-full mx-4"
            style={{
              backgroundColor: '#1a1b1b',
              border: '1px solid rgba(255,255,255,0.06)',
              fontFamily: "'Space Grotesk', sans-serif",
              color: '#e3e2e2',
            }}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-2">
                <Download size={18} style={{ color: '#fbbf24' }} />
                <h3 className="font-bold text-base tracking-wide uppercase">
                  CMS Update Available
                </h3>
              </div>
              {!upgrading && (
                <button
                  onClick={() => setShowModal(false)}
                  className="opacity-60 hover:opacity-100"
                  data-testid="cms-update-modal-close"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            <div className="space-y-3 text-sm" style={{ color: 'rgba(227,226,226,0.85)' }}>
              <div className="grid grid-cols-2 gap-3 p-3 rounded-[4px]" style={{ backgroundColor: 'rgba(255,255,255,0.03)' }}>
                <div>
                  <div className="text-xs uppercase opacity-50 mb-1">Current</div>
                  <div className="font-mono text-xs">{status.current_short}</div>
                </div>
                <div>
                  <div className="text-xs uppercase opacity-50 mb-1">Latest</div>
                  <div className="font-mono text-xs" style={{ color: '#10b981' }}>
                    {status.latest_short}
                  </div>
                </div>
              </div>

              <p className="text-xs leading-relaxed">
                The upgrade pulls the latest CMS code from <span className="font-mono opacity-80">{status.ref}</span> on
                <span className="font-mono opacity-80"> {status.repo?.replace('https://github.com/', '').replace('.git', '')}</span>.
              </p>

              <div className="flex items-start gap-2 p-2 rounded-[4px]" style={{ backgroundColor: 'rgba(16,185,129,0.08)', color: 'rgba(227,226,226,0.7)' }}>
                <CheckCircle2 size={14} style={{ color: '#10b981', flexShrink: 0, marginTop: 2 }} />
                <span className="text-xs">Your content (pages, projects, users) and admin password are preserved.</span>
              </div>

              <div className="flex items-start gap-2 p-2 rounded-[4px]" style={{ backgroundColor: 'rgba(245,158,11,0.08)', color: 'rgba(227,226,226,0.7)' }}>
                <AlertCircle size={14} style={{ color: '#fbbf24', flexShrink: 0, marginTop: 2 }} />
                <span className="text-xs">The CMS will restart in ~30 seconds. The page will auto-reload.</span>
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <button
                onClick={() => setShowModal(false)}
                disabled={upgrading}
                data-testid="cms-update-modal-cancel"
                className="flex-1 px-4 py-2 rounded-[4px] text-xs font-medium uppercase tracking-wider transition-colors duration-150"
                style={{
                  backgroundColor: 'rgba(255,255,255,0.05)',
                  color: 'rgba(227,226,226,0.7)',
                  opacity: upgrading ? 0.4 : 1,
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleUpgrade}
                disabled={upgrading}
                data-testid="cms-update-modal-confirm"
                className="flex-1 gradient-btn px-4 py-2 rounded-[4px] font-headline font-bold text-xs tracking-wider uppercase flex items-center justify-center gap-2"
              >
                {upgrading ? (
                  <>
                    <RefreshCw size={12} className="animate-spin" />
                    Upgrading…
                  </>
                ) : (
                  <>
                    <Download size={12} />
                    Update now
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default UpdateChecker;
