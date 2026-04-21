/**
 * Monolith CMS - File-based Storage Layer
 * Speichert Content als JSON files in cms-data/
 */

import fs from 'fs';
import path from 'path';

const CMS_DATA_DIR = path.join(process.cwd(), 'cms-data');
const CONTENT_FILE = path.join(CMS_DATA_DIR, 'content.json');
const CONFIG_FILE = path.join(CMS_DATA_DIR, '.cms-config.json');

// Ensure cms-data directory exists
function ensureDataDir() {
  if (!fs.existsSync(CMS_DATA_DIR)) {
    fs.mkdirSync(CMS_DATA_DIR, { recursive: true });
  }
  if (!fs.existsSync(CONTENT_FILE)) {
    fs.writeFileSync(CONTENT_FILE, JSON.stringify({ elements: {}, version: 1 }, null, 2));
  }
  if (!fs.existsSync(CONFIG_FILE)) {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify({ 
      initialized: new Date().toISOString(),
      auto_discover: true 
    }, null, 2));
  }
}

/**
 * Get all content
 */
export function getContent() {
  ensureDataDir();
  const data = fs.readFileSync(CONTENT_FILE, 'utf-8');
  return JSON.parse(data);
}

/**
 * Save content
 */
export function saveContent(content) {
  ensureDataDir();
  const data = {
    elements: content.elements || {},
    version: (content.version || 0) + 1,
    updated_at: new Date().toISOString()
  };
  fs.writeFileSync(CONTENT_FILE, JSON.stringify(data, null, 2));
  return data;
}

/**
 * Get single element
 */
export function getElement(elementId) {
  const content = getContent();
  return content.elements[elementId] || null;
}

/**
 * Update single element
 */
export function updateElement(elementId, elementData) {
  const content = getContent();
  content.elements[elementId] = {
    ...content.elements[elementId],
    ...elementData,
    updated_at: new Date().toISOString()
  };
  return saveContent(content);
}

/**
 * Get published content only (for public API)
 */
export function getPublishedContent() {
  const content = getContent();
  const published = {};
  
  Object.entries(content.elements).forEach(([id, element]) => {
    if (element.published !== false) {
      published[id] = element;
    }
  });
  
  return published;
}

/**
 * Merge discovered elements with existing content
 * Keeps existing content, adds new elements
 */
export function mergeElements(discoveredElements) {
  const content = getContent();
  let newCount = 0;
  
  discoveredElements.forEach(element => {
    if (!content.elements[element.id]) {
      // New element - add with default content
      content.elements[element.id] = {
        ...element,
        published: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      newCount++;
    } else {
      // Existing element - update metadata but keep content
      content.elements[element.id] = {
        ...content.elements[element.id],
        type: element.type,
        label: element.label || content.elements[element.id].label,
        tag: element.tag || content.elements[element.id].tag
      };
    }
  });
  
  saveContent(content);
  return { merged: discoveredElements.length, new: newCount };
}

/**
 * Get config
 */
export function getConfig() {
  ensureDataDir();
  const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
  return JSON.parse(data);
}

/**
 * Save config
 */
export function saveConfig(config) {
  ensureDataDir();
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
  return config;
}
