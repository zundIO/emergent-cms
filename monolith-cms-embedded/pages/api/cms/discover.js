/**
 * CMS Auto-Discovery API
 * POST /api/cms/discover - Scan website for data-cms-id elements
 */

import { requireAuth } from '../../../lib/cms/auth';
import { mergeElements } from '../../../lib/cms/storage';
import { JSDOM } from 'jsdom';

export default async function handler(req, res) {
  // Require authentication
  try {
    await requireAuth(req);
  } catch (err) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  const { url } = req.body;
  
  if (!url) {
    return res.status(400).json({ error: 'URL required' });
  }
  
  try {
    // Fetch the page
    const response = await fetch(url);
    const html = await response.text();
    
    // Parse HTML
    const dom = new JSDOM(html);
    const document = dom.window.document;
    
    // Find all elements with data-cms-id
    const elements = document.querySelectorAll('[data-cms-id]');
    const discovered = [];
    
    elements.forEach(el => {
      const id = el.getAttribute('data-cms-id');
      const tag = el.tagName.toLowerCase();
      
      let type = 'text';
      if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tag)) {
        type = 'heading';
      } else if (tag === 'p') {
        type = 'paragraph';
      } else if (tag === 'img') {
        type = 'image';
      } else if (tag === 'a') {
        type = 'link';
      } else if (tag === 'button' || (tag === 'a' && el.getAttribute('role') === 'button')) {
        type = 'button';
      }
      
      const element = {
        id,
        type,
        tag,
        label: el.getAttribute('data-cms-label') || id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        content: {}
      };
      
      // Extract default content
      if (type === 'image') {
        element.content.src = el.getAttribute('src') || '';
        element.content.alt = el.getAttribute('alt') || '';
      } else if (type === 'link' || type === 'button') {
        element.content.text = el.textContent.trim();
        element.content.href = el.getAttribute('href') || '#';
      } else {
        element.content.text = el.textContent.trim();
      }
      
      discovered.push(element);
    });
    
    // Merge with existing content
    const result = mergeElements(discovered);
    
    return res.json({
      success: true,
      discovered: discovered.length,
      merged: result.merged,
      new: result.new,
      elements: discovered
    });
    
  } catch (err) {
    return res.status(500).json({ error: 'Failed to discover elements', message: err.message });
  }
}
