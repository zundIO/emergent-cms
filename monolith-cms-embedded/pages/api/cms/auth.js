/**
 * CMS Auth API
 * POST /api/cms/auth/login - Login
 * GET /api/cms/auth/me - Check session
 */

import { verifyPassword, createToken, verifyToken, getTokenFromRequest } from '../../../lib/cms/auth';

export default async function handler(req, res) {
  // Login
  if (req.method === 'POST') {
    const { password } = req.body;
    
    if (!password) {
      return res.status(400).json({ error: 'Password required' });
    }
    
    const valid = await verifyPassword(password);
    if (!valid) {
      return res.status(401).json({ error: 'Invalid password' });
    }
    
    const token = await createToken();
    
    // Set cookie
    res.setHeader('Set-Cookie', `cms-token=${token}; HttpOnly; Path=/; Max-Age=${7 * 24 * 60 * 60}; SameSite=Strict`);
    
    return res.json({ success: true, token });
  }
  
  // Check session
  if (req.method === 'GET') {
    const token = getTokenFromRequest(req);
    if (!token) {
      return res.status(401).json({ authenticated: false });
    }
    
    const payload = await verifyToken(token);
    if (!payload) {
      return res.status(401).json({ authenticated: false });
    }
    
    return res.json({ authenticated: true, role: payload.role });
  }
  
  // Logout
  if (req.method === 'DELETE') {
    res.setHeader('Set-Cookie', 'cms-token=; HttpOnly; Path=/; Max-Age=0');
    return res.json({ success: true });
  }
  
  return res.status(405).json({ error: 'Method not allowed' });
}
