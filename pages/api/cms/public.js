/**
 * CMS Public Content API (No auth required)
 * GET /api/cms/public - Get published content
 */

import { getPublishedContent } from '../../../lib/cms/storage';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  res.setHeader('Cache-Control', 'public, max-age=60, stale-while-revalidate=300');
  
  const content = getPublishedContent();
  return res.json(content);
}
