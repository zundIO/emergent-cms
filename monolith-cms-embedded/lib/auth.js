/**
 * Monolith CMS - Simple Auth System
 * Password-based authentication with JWT
 */

import bcrypt from 'bcryptjs';
import { SignJWT, jwtVerify } from 'jose';

const JWT_SECRET = new TextEncoder().encode(
  process.env.CMS_SECRET || 'monolith-cms-secret-change-in-production-min-32-chars'
);

const ADMIN_PASSWORD = process.env.CMS_ADMIN_PASSWORD || 'admin123';

/**
 * Verify password
 */
export async function verifyPassword(password) {
  // For simplicity: direct comparison in dev, bcrypt in production
  if (process.env.NODE_ENV === 'development' && !ADMIN_PASSWORD.startsWith('$2')) {
    return password === ADMIN_PASSWORD;
  }
  
  // Bcrypt comparison
  try {
    return await bcrypt.compare(password, ADMIN_PASSWORD);
  } catch (err) {
    // Fallback for non-hashed passwords
    return password === ADMIN_PASSWORD;
  }
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
