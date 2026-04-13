import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { pagesAPI } from '../lib/api';
import TopBar from '../components/editor/TopBar';
import LeftSidebar from '../components/editor/LeftSidebar';
import Canvas from '../components/editor/Canvas';
import PropertyPanel from '../components/editor/PropertyPanel';
import PagesList from '../components/editor/PagesList';
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
  const [activeSidebar, setActiveSidebar] = useState('pages');
  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);

  // Load pages list
  const loadPages = useCallback(async () => {
    try {
      const res = await pagesAPI.list();
      setPages(res.data);
      // Auto-open first page if none selected
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

  // Open a specific page
  const openPage = async (pageId) => {
    try {
      const res = await pagesAPI.get(pageId);
      setCurrentPage(res.data);
      setSelectedElement(null);
      setShowPagesList(false);
      setIsDirty(false);
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

    // Optimistic update - update local state immediately
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

    // Update selected element reference
    if (selectedElement && selectedElement.id === elementId) {
      setSelectedElement((prev) => ({
        ...prev,
        content: { ...prev.content, ...newContent },
      }));
    }

    setIsDirty(true);
  };

  // Save changes to backend
  const handleSave = async () => {
    if (!currentPage || !isDirty) return;
    setSaving(true);
    try {
      // Collect all content from current page elements and send bulk update
      const updates = collectAllContent(currentPage.elements);
      await pagesAPI.updateContentBulk(currentPage._id, updates);
      setIsDirty(false);
      // Reload page to sync status
      const res = await pagesAPI.get(currentPage._id);
      setCurrentPage(res.data);
      // Refresh pages list
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
      // Save first if dirty
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

  // Handle sidebar navigation
  const handleSidebarClick = (item) => {
    setActiveSidebar(item);
    if (item === 'pages') {
      setShowPagesList(true);
    } else {
      setShowPagesList(false);
    }
  };

  // Deselect on canvas background click
  const handleCanvasBackgroundClick = () => {
    setSelectedElement(null);
  };

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
      />

      <div className="editor-main">
        <LeftSidebar
          activeSidebar={activeSidebar}
          onSidebarClick={handleSidebarClick}
        />

        <div className="canvas-area custom-scrollbar" onClick={handleCanvasBackgroundClick}>
          {showPagesList ? (
            <PagesList
              pages={pages}
              currentPageId={currentPage?._id}
              onOpenPage={openPage}
              onClose={() => setShowPagesList(false)}
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

        {currentPage && !showPagesList && (
          <PropertyPanel
            selectedElement={selectedElement}
            onContentUpdate={handleContentUpdate}
            onDeselect={() => setSelectedElement(null)}
          />
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
