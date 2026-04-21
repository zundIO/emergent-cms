/**
 * CMS Content API (Admin only)
 * GET /api/cms/content - Get all content
 * PUT /api/cms/content - Save content
 * PATCH /api/cms/content/:id - Update single element
 */

import { requireAuth } from '../../../lib/cms/auth';
import { getContent, saveContent, updateElement } from '../../../lib/cms/storage';

export default async function handler(req, res) {
  // Require authentication
  try {
    await requireAuth(req);
  } catch (err) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  // Get all content
  if (req.method === 'GET') {
    const content = getContent();
    return res.json(content);
  }
  
  // Save content
  if (req.method === 'PUT') {
    const { elements } = req.body;
    
    if (!elements) {
      return res.status(400).json({ error: 'Elements required' });
    }
    
    const updated = saveContent({ elements });
    return res.json({ success: true, version: updated.version });
  }
  
  // Update single element
  if (req.method === 'PATCH') {
    const { id, ...elementData } = req.body;
    
    if (!id) {
      return res.status(400).json({ error: 'Element ID required' });
    }
    
    const updated = updateElement(id, elementData);
    return res.json({ success: true, version: updated.version });
  }
  
  return res.status(405).json({ error: 'Method not allowed' });
}
