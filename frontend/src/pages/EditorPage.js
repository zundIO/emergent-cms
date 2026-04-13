import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { pagesAPI } from '../lib/api';
import useUndoRedo from '../hooks/useUndoRedo';
import TopBar from '../components/editor/TopBar';
import LeftSidebar from '../components/editor/LeftSidebar';
import Canvas from '../components/editor/Canvas';
import PropertyPanel from '../components/editor/PropertyPanel';
import PagesList from '../components/editor/PagesList';
import HistoryPanel from '../components/editor/HistoryPanel';
import UserManagement from '../components/editor/UserManagement';
import IntegrationDocs from '../components/editor/IntegrationDocs';
import '../App.css';

export default function EditorPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [pages, setPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(null);
  const [selectedElement, setSelectedElement] = useState(null);
  const [deviceMode, setDeviceMode] = useState('desktop');
  const [activeTab, setActiveTab] = useState('structure');
  const [showPagesList, setShowPagesList] = useState(false);
  const [showUserManagement, setShowUserManagement] = useState(false);
  const [showIntegrationDocs, setShowIntegrationDocs] = useState(false);
  const [activeSidebar, setActiveSidebar] = useState('pages');
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);

  // Undo/Redo system
  const { pushState, undo, redo, canUndo, canRedo, clear: clearHistory } = useUndoRedo(50);

  // Load pages list
  const loadPages = useCallback(async () => {
    try {
      const res = await pagesAPI.list();
      setPages(res.data);
      if (res.data.length > 0 && !currentPage) {
        const firstPage = await pagesAPI.get(res.data[0]._id);
        setCurrentPage(firstPage.data);
      }
    } catch (err) {
      console.error('Failed to load pages:', err);
    }
  }, [currentPage]);

  useEffect(() => {
    loadPages();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Keyboard shortcuts for undo/redo
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Skip if user is typing in an input or textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
        return;
      }
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      if (modKey && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      }
      if (modKey && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        handleRedo();
      }
      // Save with Ctrl+S
      if (modKey && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }); // Re-register on every render to capture latest state

  // Open a specific page
  const openPage = async (pageId) => {
    try {
      const res = await pagesAPI.get(pageId);
      setCurrentPage(res.data);
      setSelectedElement(null);
      setShowPagesList(false);
      setShowUserManagement(false);
      setShowIntegrationDocs(false);
      setIsDirty(false);
      clearHistory();
    } catch (err) {
      console.error('Failed to open page:', err);
    }
  };

  // Handle element selection
  const handleSelectElement = (element) => {
    setSelectedElement(element);
  };

  // Handle content update from property panel
  const handleContentUpdate = async (elementId, newContent) => {
    if (!currentPage) return;

    // Push BEFORE state to undo stack
    pushState(currentPage.elements);

    // Optimistic update
    const updatedElements = updateElementInTree(
      [...currentPage.elements],
      elementId,
      newContent
    );

    setCurrentPage((prev) => ({
      ...prev,
      elements: updatedElements,
      status: 'draft',
    }));

    if (selectedElement && selectedElement.id === elementId) {
      setSelectedElement((prev) => ({
        ...prev,
        content: { ...prev.content, ...newContent },
      }));
    }

    setIsDirty(true);
  };

  // Undo
  const handleUndo = () => {
    if (!currentPage || !canUndo) return;
    const prevElements = undo(currentPage.elements);
    if (prevElements) {
      setCurrentPage((prev) => ({
        ...prev,
        elements: prevElements,
        status: 'draft',
      }));
      // Update selected element if still exists
      if (selectedElement) {
        const found = findElementById(prevElements, selectedElement.id);
        setSelectedElement(found || null);
      }
      setIsDirty(true);
    }
  };

  // Redo
  const handleRedo = () => {
    if (!currentPage || !canRedo) return;
    const nextElements = redo(currentPage.elements);
    if (nextElements) {
      setCurrentPage((prev) => ({
        ...prev,
        elements: nextElements,
        status: 'draft',
      }));
      if (selectedElement) {
        const found = findElementById(nextElements, selectedElement.id);
        setSelectedElement(found || null);
      }
      setIsDirty(true);
    }
  };

  // Save changes to backend
  const handleSave = async () => {
    if (!currentPage || !isDirty) return;
    setSaving(true);
    try {
      const updates = collectAllContent(currentPage.elements);
      await pagesAPI.updateContentBulk(currentPage._id, updates);
      setIsDirty(false);
      const res = await pagesAPI.get(currentPage._id);
      setCurrentPage(res.data);
      loadPages();
    } catch (err) {
      console.error('Save failed:', err);
    } finally {
      setSaving(false);
    }
  };

  // Publish page
  const handlePublish = async () => {
    if (!currentPage) return;
    setPublishing(true);
    try {
      if (isDirty) {
        const updates = collectAllContent(currentPage.elements);
        await pagesAPI.updateContentBulk(currentPage._id, updates);
      }
      await pagesAPI.updateStatus(currentPage._id, 'published');
      const res = await pagesAPI.get(currentPage._id);
      setCurrentPage(res.data);
      setIsDirty(false);
      loadPages();
    } catch (err) {
      console.error('Publish failed:', err);
    } finally {
      setPublishing(false);
    }
  };

  // Handle history version restore
  const handleHistoryRestore = (restoredPage) => {
    setCurrentPage(restoredPage);
    setSelectedElement(null);
    setIsDirty(false);
    clearHistory();
    loadPages();
  };

  // Handle sidebar navigation
  const handleSidebarClick = (item) => {
    setActiveSidebar(item);
    if (item === 'pages') {
      setShowPagesList(true);
      setShowUserManagement(false);
      setShowIntegrationDocs(false);
    } else if (item === 'settings') {
      setShowUserManagement(true);
      setShowPagesList(false);
      setShowIntegrationDocs(false);
    } else if (item === 'integration') {
      setShowIntegrationDocs(true);
      setShowPagesList(false);
      setShowUserManagement(false);
    } else {
      setShowPagesList(false);
      setShowUserManagement(false);
      setShowIntegrationDocs(false);
    }
  };

  // Determine what to show in the main area
  const showHistory = activeTab === 'history' && currentPage && !showPagesList && !showUserManagement && !showIntegrationDocs;

  return (
    <div className="editor-workspace">
      <TopBar
        currentPage={currentPage}
        deviceMode={deviceMode}
        setDeviceMode={setDeviceMode}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onPublish={handlePublish}
        onSave={handleSave}
        publishing={publishing}
        saving={saving}
        isDirty={isDirty}
        user={user}
        onLogout={logout}
        canUndo={canUndo}
        canRedo={canRedo}
        onUndo={handleUndo}
        onRedo={handleRedo}
      />

      <div className="editor-main">
        <LeftSidebar
          activeSidebar={activeSidebar}
          onSidebarClick={handleSidebarClick}
          isAdmin={user?.role === 'admin'}
        />

        <div className="canvas-area custom-scrollbar" onClick={() => setSelectedElement(null)}>
          {showPagesList ? (
            <PagesList
              pages={pages}
              currentPageId={currentPage?._id}
              onOpenPage={openPage}
              onClose={() => setShowPagesList(false)}
            />
          ) : showUserManagement ? (
            <UserManagement
              onClose={() => {
                setShowUserManagement(false);
                setActiveSidebar('pages');
              }}
            />
          ) : showIntegrationDocs ? (
            <IntegrationDocs
              cmsUrl={process.env.REACT_APP_BACKEND_URL || window.location.origin}
              onClose={() => {
                setShowIntegrationDocs(false);
                setActiveSidebar('pages');
              }}
            />
          ) : currentPage ? (
            <Canvas
              page={currentPage}
              selectedElement={selectedElement}
              onSelectElement={handleSelectElement}
              deviceMode={deviceMode}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="font-headline text-lg" style={{ color: 'var(--muted)' }}>
                  No page selected
                </p>
                <p className="text-sm mt-2" style={{ color: 'var(--muted-2)' }}>
                  Select a page from the sidebar to start editing
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right panel: Property Panel or History Panel */}
        {currentPage && !showPagesList && !showUserManagement && !showIntegrationDocs && (
          showHistory ? (
            <div className="right-panel custom-scrollbar">
              <HistoryPanel
                pageId={currentPage._id}
                onRestore={handleHistoryRestore}
              />
            </div>
          ) : (
            <PropertyPanel
              selectedElement={selectedElement}
              onContentUpdate={handleContentUpdate}
              onDeselect={() => setSelectedElement(null)}
            />
          )
        )}
      </div>
    </div>
  );
}

// Utility: recursively update element content in tree
function updateElementInTree(elements, elementId, newContent) {
  return elements.map((el) => {
    if (el.id === elementId) {
      return {
        ...el,
        content: { ...el.content, ...newContent },
      };
    }
    if (el.children && el.children.length > 0) {
      return {
        ...el,
        children: updateElementInTree(el.children, elementId, newContent),
      };
    }
    return el;
  });
}

// Utility: find element by ID in tree
function findElementById(elements, elementId) {
  for (const el of elements) {
    if (el.id === elementId) return el;
    if (el.children) {
      const found = findElementById(el.children, elementId);
      if (found) return found;
    }
  }
  return null;
}

// Utility: collect all element contents for bulk update
function collectAllContent(elements) {
  const updates = [];
  function traverse(els) {
    for (const el of els) {
      if (el.content && Object.keys(el.content).length > 0) {
        updates.push({ element_id: el.id, content: el.content });
      }
      if (el.children) traverse(el.children);
    }
  }
  traverse(elements);
  return updates;
}
