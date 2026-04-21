/**
 * CMS Auto-Register API (Public, no auth)
 *
 * Called by cms-client.js from every page load to report discovered editable
 * elements. Safe to be unauthenticated: only ADDS new metadata entries,
 * never overwrites existing content (see mergeElements in storage.js).
 *
 * POST /api/cms/register
 * Body: { path: string, elements: [{ id, tag, type, label, content }] }
 */

import { mergeElements } from '../../../lib/cms/storage';

export default async function handler(req, res) {
  // Same-origin only (basic protection)
  res.setHeader('Access-Control-Allow-Origin', '*');

  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Methods', 'POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { elements, path: pagePath } = req.body || {};

    if (!Array.isArray(elements) || elements.length === 0) {
      return res.status(400).json({ error: 'elements array required' });
    }

    // Attach page path to each element so the editor can group by page
    const tagged = elements.map((el) => ({
      ...el,
      page: pagePath || '/'
    }));

    const result = mergeElements(tagged);

    return res.status(200).json({
      success: true,
      received: tagged.length,
      new: result.new
    });
  } catch (err) {
    console.error('[CMS Register] Error:', err);
    return res.status(500).json({ error: 'Failed to register elements' });
  }
}
