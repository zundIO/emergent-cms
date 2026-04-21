/**
 * Monolith CMS - Simple Auth System
 * Password-based authentication with JWT
 */

import bcrypt from 'bcryptjs';
import { SignJWT, jwtVerify } from 'jose';

const JWT_SECRET = new TextEncoder().encode(
  process.env.CMS_SECRET || 'monolith-cms-secret-change-in-production-min-32-chars'
);

/**
 * Verify password
 */
export async function verifyPassword(password) {
  const adminPassword = process.env.CMS_ADMIN_PASSWORD;
  
  if (!adminPassword) {
    throw new Error('Setup required');
  }
  
  // Check if password is hashed (bcrypt format)
  if (adminPassword.startsWith('$2')) {
    return await bcrypt.compare(password, adminPassword);
  }
  
  // Plain text fallback (for backward compatibility)
  return password === adminPassword;
}

/**
 * Create JWT token
 */
export async function createToken() {
  const token = await new SignJWT({ role: 'admin' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(JWT_SECRET);
  
  return token;
}

/**
 * Verify JWT token
 */
export async function verifyToken(token) {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    return payload;
  } catch (err) {
    return null;
  }
}

/**
 * Get token from request headers or cookies
 */
export function getTokenFromRequest(req) {
  // Check Authorization header
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }
  
  // Check cookie
  const cookies = req.headers.cookie?.split(';').reduce((acc, cookie) => {
    const [key, value] = cookie.trim().split('=');
    acc[key] = value;
    return acc;
  }, {});
  
  return cookies?.['cms-token'] || null;
}

/**
 * Middleware: Require authentication
 */
export async function requireAuth(req) {
  const token = getTokenFromRequest(req);
  if (!token) {
    throw new Error('Unauthorized');
  }
  
  const payload = await verifyToken(token);
  if (!payload) {
    throw new Error('Invalid token');
  }
  
  return payload;
}
