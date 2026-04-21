/**
 * CMS First-Time Setup API
 * POST /api/cms/setup - Create first admin user
 */

import { createToken } from '../../../lib/cms/auth';
import bcrypt from 'bcryptjs';
import fs from 'fs';
import path from 'path';

const SETUP_LOCK_FILE = path.join(process.cwd(), 'cms-data', '.setup-complete');

export default async function handler(req, res) {
  // Check if setup already completed
  if (fs.existsSync(SETUP_LOCK_FILE)) {
    return res.status(403).json({ error: 'Setup already completed' });
  }
  
  if (req.method === 'GET') {
    // Check if setup is needed
    return res.json({ setupRequired: true });
  }
  
  if (req.method === 'POST') {
    const { email, password, name } = req.body;
    
    // Validate input
    if (!email || !password || !name) {
      return res.status(400).json({ error: 'Email, password, and name are required' });
    }
    
    if (password.length < 8) {
      return res.status(400).json({ error: 'Password must be at least 8 characters' });
    }
    
    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);
    
    // Create .env.local if doesn't exist
    const envPath = path.join(process.cwd(), '.env.local');
    let envContent = '';
    
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf-8');
    }
    
    // Generate random secret
    const secret = Array.from({ length: 32 }, () => 
      Math.random().toString(36).charAt(2)
    ).join('');
    
    // Add CMS config to .env.local
    if (!envContent.includes('CMS_ADMIN_PASSWORD')) {
      envContent += `\n# Monolith CMS Configuration\n`;
      envContent += `CMS_ADMIN_EMAIL=${email}\n`;
      envContent += `CMS_ADMIN_PASSWORD=${hashedPassword}\n`;
      envContent += `CMS_ADMIN_NAME=${name}\n`;
      envContent += `CMS_SECRET=${secret}\n`;
    }
    
    fs.writeFileSync(envPath, envContent);
    
    // Create setup lock file
    const cmsDataDir = path.join(process.cwd(), 'cms-data');
    if (!fs.existsSync(cmsDataDir)) {
      fs.mkdirSync(cmsDataDir, { recursive: true });
    }
    
    fs.writeFileSync(SETUP_LOCK_FILE, JSON.stringify({
      completedAt: new Date().toISOString(),
      adminEmail: email,
      adminName: name
    }, null, 2));
    
    // Create token for immediate login
    const token = await createToken();
    res.setHeader('Set-Cookie', `cms-token=${token}; HttpOnly; Path=/; Max-Age=${7 * 24 * 60 * 60}; SameSite=Strict`);
    
    return res.json({ 
      success: true, 
      message: 'Admin user created successfully',
      token 
    });
  }
  
  return res.status(405).json({ error: 'Method not allowed' });
}
