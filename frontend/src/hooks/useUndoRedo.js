import { useState, useCallback, useRef } from 'react';

/**
 * useUndoRedo - Session-level undo/redo for page element content.
 * Tracks a stack of element tree snapshots.
 */
export default function useUndoRedo(maxHistory = 50) {
  const [past, setPast] = useState([]);
  const [future, setFuture] = useState([]);
  const lastSnapshotRef = useRef(null);

  // Push the current state to history before making a change
  const pushState = useCallback(
    (elementsSnapshot) => {
      // Deep clone to prevent reference sharing
      const snapshot = JSON.parse(JSON.stringify(elementsSnapshot));
      // Don't push duplicates
      if (lastSnapshotRef.current && JSON.stringify(lastSnapshotRef.current) === JSON.stringify(snapshot)) {
        return;
      }
      setPast((prev) => {
        const newPast = [...prev, snapshot];
        if (newPast.length > maxHistory) newPast.shift();
        return newPast;
      });
      setFuture([]); // Clear redo stack on new action
      lastSnapshotRef.current = snapshot;
    },
    [maxHistory]
  );

  // Undo: pop from past, push current to future
  const undo = useCallback(
    (currentElements) => {
      if (past.length === 0) return null;
      const prev = past[past.length - 1];
      setPast((p) => p.slice(0, -1));
      setFuture((f) => [...f, JSON.parse(JSON.stringify(currentElements))]);
      lastSnapshotRef.current = prev;
      return prev;
    },
    [past]
  );

  // Redo: pop from future, push current to past
  const redo = useCallback(
    (currentElements) => {
      if (future.length === 0) return null;
      const next = future[future.length - 1];
      setFuture((f) => f.slice(0, -1));
      setPast((p) => [...p, JSON.parse(JSON.stringify(currentElements))]);
      lastSnapshotRef.current = next;
      return next;
    },
    [future]
  );

  const canUndo = past.length > 0;
  const canRedo = future.length > 0;

  const clear = useCallback(() => {
    setPast([]);
    setFuture([]);
    lastSnapshotRef.current = null;
  }, []);

  return { pushState, undo, redo, canUndo, canRedo, clear, undoCount: past.length, redoCount: future.length };
}
