import React from 'react';
import { Monitor, Tablet, Smartphone, TabletSmartphone, Undo2, Redo2 } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '../../components/ui/tooltip';

const TopBar = ({
  currentPage,
  deviceMode,
  setDeviceMode,
  activeTab,
  setActiveTab,
  onPublish,
  onSave,
  publishing,
  saving,
  isDirty,
  user,
  onLogout,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
}) => {
  const devices = [
    { id: 'desktop', icon: Monitor, label: 'Desktop' },
    { id: 'tablet', icon: Tablet, label: 'Tablet' },
    { id: 'tablet-sm', icon: TabletSmartphone, label: 'Tablet Small' },
    { id: 'mobile', icon: Smartphone, label: 'Mobile' },
  ];

  const tabs = [
    { id: 'structure', label: 'STRUCTURE' },
    { id: 'seo', label: 'SEO' },
    { id: 'history', label: 'HISTORY' },
  ];

  return (
    <TooltipProvider delayDuration={200}>
      <div className="top-bar" data-testid="editor-topbar">
        {/* Logo */}
        <div className="flex items-center mr-6">
          <div>
            <span className="font-headline font-bold text-sm" style={{ color: 'var(--on-surface)' }}>
              The Monolith
            </span>
            <br />
            <span className="text-[10px] font-semibold tracking-[0.12em] uppercase" style={{ color: 'var(--primary-2)' }}>
              CMS
            </span>
          </div>
        </div>

        {/* Page name + status */}
        {currentPage && (
          <div className="flex items-center gap-3 mr-6">
            <span
              className="font-headline text-xs font-semibold tracking-wider uppercase"
              style={{ color: 'var(--on-surface)' }}
              data-testid="editor-topbar-page-name"
            >
              {currentPage.name}
            </span>
            <span
              data-testid="editor-topbar-page-status"
              className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[3px]"
              style={{
                backgroundColor:
                  currentPage.status === 'published'
                    ? 'rgba(16, 185, 129, 0.14)'
                    : 'rgba(245, 158, 11, 0.14)',
                color:
                  currentPage.status === 'published' ? '#4edea3' : '#fbbf24',
              }}
            >
              {currentPage.status}
            </span>
            {isDirty && (
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: 'var(--warning)' }}
                title="Unsaved changes"
              />
            )}
          </div>
        )}

        {/* Undo/Redo buttons */}
        {currentPage && (
          <div className="flex items-center gap-0.5 mr-4" data-testid="undo-redo-controls">
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  data-testid="undo-button"
                  onClick={onUndo}
                  disabled={!canUndo}
                  className="w-8 h-8 rounded-[4px] grid place-items-center transition-colors duration-150"
                  style={{
                    color: canUndo ? 'var(--on-surface)' : 'var(--muted-2)',
                    opacity: canUndo ? 1 : 0.4,
                    cursor: canUndo ? 'pointer' : 'not-allowed',
                  }}
                >
                  <Undo2 size={15} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>Undo (Ctrl+Z)</p>
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  data-testid="redo-button"
                  onClick={onRedo}
                  disabled={!canRedo}
                  className="w-8 h-8 rounded-[4px] grid place-items-center transition-colors duration-150"
                  style={{
                    color: canRedo ? 'var(--on-surface)' : 'var(--muted-2)',
                    opacity: canRedo ? 1 : 0.4,
                    cursor: canRedo ? 'pointer' : 'not-allowed',
                  }}
                >
                  <Redo2 size={15} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>Redo (Ctrl+Y)</p>
              </TooltipContent>
            </Tooltip>
          </div>
        )}

        {/* Device icons */}
        <div className="flex items-center gap-1 mr-6" data-testid="editor-topbar-device-selector">
          {devices.map((d) => (
            <Tooltip key={d.id}>
              <TooltipTrigger asChild>
                <button
                  data-testid={`device-${d.id}`}
                  onClick={() => setDeviceMode(d.id === 'tablet-sm' ? 'mobile' : d.id)}
                  className="w-8 h-8 rounded-[4px] grid place-items-center transition-colors duration-150"
                  style={{
                    backgroundColor:
                      (d.id === deviceMode || (d.id === 'tablet-sm' && deviceMode === 'mobile'))
                        ? 'rgba(16, 185, 129, 0.14)'
                        : 'transparent',
                    color:
                      (d.id === deviceMode || (d.id === 'tablet-sm' && deviceMode === 'mobile'))
                        ? 'var(--primary-2)'
                        : 'var(--muted-2)',
                  }}
                >
                  <d.icon size={16} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>{d.label}</p>
              </TooltipContent>
            </Tooltip>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 flex-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              data-testid={`editor-topbar-tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className="px-4 py-2 text-xs font-semibold tracking-wider uppercase rounded-[4px] transition-colors duration-150 relative"
              style={{
                backgroundColor:
                  activeTab === tab.id ? 'rgba(255, 255, 255, 0.06)' : 'transparent',
                color:
                  activeTab === tab.id ? 'var(--on-surface)' : 'var(--muted-2)',
              }}
            >
              {tab.label}
              {activeTab === tab.id && (
                <span
                  className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 rounded-full"
                  style={{ backgroundColor: 'var(--primary)' }}
                />
              )}
            </button>
          ))}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          {/* Save indicator */}
          {isDirty && (
            <button
              data-testid="editor-topbar-save-button"
              onClick={onSave}
              disabled={saving}
              className="text-xs font-medium px-3 py-1.5 rounded-[4px] transition-colors duration-150"
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
                color: 'var(--on-surface)',
              }}
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          )}

          {/* Preview */}
          <button
            data-testid="editor-topbar-preview-button"
            className="text-xs font-medium transition-colors duration-150"
            style={{ color: 'var(--muted)' }}
          >
            Preview
          </button>

          {/* Publish */}
          <button
            data-testid="editor-topbar-publish-button"
            onClick={onPublish}
            disabled={publishing}
            className="gradient-btn px-5 py-2 rounded-[4px] font-headline font-bold text-xs tracking-wider uppercase transition-transform duration-150 active:scale-[0.98]"
          >
            {publishing ? 'Publishing...' : 'Publish'}
          </button>

          {/* User avatar */}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                data-testid="editor-topbar-user-avatar"
                onClick={onLogout}
                className="w-8 h-8 rounded-full grid place-items-center text-xs font-bold"
                style={{
                  backgroundColor: 'rgba(16, 185, 129, 0.2)',
                  color: 'var(--primary-2)',
                }}
              >
                {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p>Sign out ({user?.email})</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </TooltipProvider>
  );
};

export default TopBar;
