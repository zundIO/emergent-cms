import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, RotateCcw, Eye, ChevronRight, Save, Upload, Undo2, Loader2 } from 'lucide-react';
import { versionsAPI, pagesAPI } from '../../lib/api';

const actionIcons = {
  save: <Save size={14} />,
  publish: <Upload size={14} />,
  restore: <Undo2 size={14} />,
};

const actionColors = {
  save: 'var(--info)',
  publish: 'var(--primary-2)',
  restore: 'var(--warning)',
};

const HistoryPanel = ({ pageId, onRestore }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState(null);
  const [previewVersion, setPreviewVersion] = useState(null);

  const loadVersions = useCallback(async () => {
    if (!pageId) return;
    setLoading(true);
    try {
      const res = await versionsAPI.list(pageId);
      setVersions(res.data);
    } catch (err) {
      console.error('Failed to load versions:', err);
    } finally {
      setLoading(false);
    }
  }, [pageId]);

  useEffect(() => {
    loadVersions();
  }, [loadVersions]);

  const handleRestore = async (versionNumber) => {
    setRestoring(versionNumber);
    try {
      const res = await versionsAPI.restore(pageId, versionNumber);
      if (onRestore) onRestore(res.data);
      loadVersions(); // Refresh list
    } catch (err) {
      console.error('Failed to restore version:', err);
    } finally {
      setRestoring(null);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center" style={{ minHeight: '200px' }}>
        <Loader2 size={20} className="animate-spin" style={{ color: 'var(--muted)' }} />
      </div>
    );
  }

  if (versions.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={16} style={{ color: 'var(--primary-2)' }} />
          <span className="font-headline text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>
            Version History
          </span>
        </div>
        <div className="text-center py-12">
          <Clock size={32} className="mx-auto mb-3" style={{ color: 'var(--muted-2)' }} />
          <p className="text-sm" style={{ color: 'var(--muted)' }}>No versions yet</p>
          <p className="text-xs mt-1" style={{ color: 'var(--muted-2)' }}>Versions are created when you save or publish</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4" data-testid="history-panel">
      <div className="flex items-center gap-2 mb-4 px-2">
        <Clock size={16} style={{ color: 'var(--primary-2)' }} />
        <span className="font-headline text-sm font-semibold" style={{ color: 'var(--on-surface)' }}>
          Version History
        </span>
        <span
          className="text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] ml-auto"
          style={{ backgroundColor: 'rgba(255,255,255,0.06)', color: 'var(--muted)' }}
        >
          {versions.length}
        </span>
      </div>

      <div className="space-y-1">
        {versions.map((v, idx) => (
          <motion.div
            key={v._id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.15, delay: idx * 0.03 }}
            data-testid={`history-version-${v.version_number}`}
            className="group rounded-[4px] p-3 transition-colors duration-150 cursor-pointer"
            style={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.02)'; }}
          >
            <div className="flex items-center gap-3">
              {/* Version icon */}
              <div
                className="w-8 h-8 rounded-[4px] grid place-items-center flex-shrink-0"
                style={{
                  backgroundColor: `${actionColors[v.action] || 'var(--muted)'}15`,
                  color: actionColors[v.action] || 'var(--muted)',
                }}
              >
                {actionIcons[v.action] || <Clock size={14} />}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold" style={{ color: 'var(--on-surface)' }}>
                    v{v.version_number}
                  </span>
                  <span
                    className="text-[10px] font-medium uppercase tracking-wider px-1.5 py-0.5 rounded-[2px]"
                    style={{
                      backgroundColor: `${actionColors[v.action] || 'var(--muted)'}15`,
                      color: actionColors[v.action] || 'var(--muted)',
                    }}
                  >
                    {v.action}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px]" style={{ color: 'var(--muted-2)' }}>
                    {formatDate(v.created_at)}
                  </span>
                  <span className="text-[10px]" style={{ color: 'var(--muted-2)' }}>
                    by {v.created_by}
                  </span>
                </div>
              </div>

              {/* Restore button */}
              <button
                data-testid={`history-restore-${v.version_number}`}
                onClick={(e) => {
                  e.stopPropagation();
                  handleRestore(v.version_number);
                }}
                disabled={restoring === v.version_number}
                className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-[4px]"
                style={{
                  backgroundColor: 'rgba(16, 185, 129, 0.14)',
                  color: 'var(--primary-2)',
                }}
              >
                {restoring === v.version_number ? (
                  <Loader2 size={10} className="animate-spin" />
                ) : (
                  <RotateCcw size={10} />
                )}
                Restore
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default HistoryPanel;
