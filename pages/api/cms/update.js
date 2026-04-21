/**
 * CMS Self-Update API (Admin only)
 *
 * GET  /api/cms/update - Compare installed version with latest on GitHub
 * POST /api/cms/update - Re-download all CMS files from the official repo
 *
 * This is what makes the embedded CMS "self-updating" across every website
 * it is installed on: one click in the admin panel pulls the newest code
 * directly from https://github.com/zundIO/emergent-cms (main branch).
 */

import fs from 'fs';
import path from 'path';
import { requireAuth } from '../../../lib/cms/auth';

const REPO = 'zundIO/emergent-cms';
const BRANCH = 'main';
const RAW = `https://raw.githubusercontent.com/${REPO}/${BRANCH}`;
const API = `https://api.github.com/repos/${REPO}`;

// Files that can be safely overwritten on update.
// NOTE: cms-data/* (content) and .env.local (secrets) are NEVER touched.
const FILES = [
  { remote: 'lib/storage.js',             local: 'lib/cms/storage.js' },
  { remote: 'lib/auth.js',                local: 'lib/cms/auth.js' },
  { remote: 'pages/api/cms/auth.js',      local: 'pages/api/cms/auth.js' },
  { remote: 'pages/api/cms/setup.js',     local: 'pages/api/cms/setup.js' },
  { remote: 'pages/api/cms/content.js',   local: 'pages/api/cms/content.js' },
  { remote: 'pages/api/cms/discover.js',  local: 'pages/api/cms/discover.js' },
  { remote: 'pages/api/cms/register.js',  local: 'pages/api/cms/register.js' },
  { remote: 'pages/api/cms/public.js',    local: 'pages/api/cms/public.js' },
  { remote: 'pages/api/cms/update.js',    local: 'pages/api/cms/update.js' },
  { remote: 'public/cms-client.js',       local: 'public/cms-client.js' }
];

const VERSION_FILE = path.join(process.cwd(), 'cms-data', '.cms-version.json');

function readLocalVersion() {
  try {
    if (fs.existsSync(VERSION_FILE)) {
      return JSON.parse(fs.readFileSync(VERSION_FILE, 'utf-8'));
    }
  } catch (e) { /* ignore */ }
  return { sha: null, updated_at: null };
}

function writeLocalVersion(sha) {
  try {
    fs.mkdirSync(path.dirname(VERSION_FILE), { recursive: true });
    fs.writeFileSync(VERSION_FILE, JSON.stringify({
      sha,
      updated_at: new Date().toISOString()
    }, null, 2));
  } catch (e) { /* ignore */ }
}

async function fetchText(url) {
  const res = await fetch(url, { headers: { 'User-Agent': 'monolith-cms' } });
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.text();
}

async function fetchJson(url) {
  const res = await fetch(url, { headers: { 'User-Agent': 'monolith-cms', Accept: 'application/vnd.github+json' } });
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

async function getRemoteSha() {
  try {
    const data = await fetchJson(`${API}/commits/${BRANCH}`);
    return data.sha || null;
  } catch (e) {
    return null;
  }
}

export default async function handler(req, res) {
  try {
    await requireAuth(req);
  } catch (err) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  if (req.method === 'GET') {
    const local = readLocalVersion();
    const remote = await getRemoteSha();
    return res.json({
      local_sha: local.sha,
      remote_sha: remote,
      updated_at: local.updated_at,
      update_available: remote && local.sha !== remote,
      repo: `https://github.com/${REPO}`
    });
  }

  if (req.method === 'POST') {
    const results = [];
    let succeeded = 0;

    for (const f of FILES) {
      try {
        const body = await fetchText(`${RAW}/${f.remote}`);
        const target = path.join(process.cwd(), f.local);
        fs.mkdirSync(path.dirname(target), { recursive: true });
        fs.writeFileSync(target, body);
        results.push({ file: f.local, ok: true });
        succeeded++;
      } catch (err) {
        results.push({ file: f.local, ok: false, error: err.message });
      }
    }

    const remote = await getRemoteSha();
    if (remote) writeLocalVersion(remote);

    return res.json({
      success: succeeded === FILES.length,
      updated: succeeded,
      total: FILES.length,
      new_sha: remote,
      results,
      note: 'Restart the dev server (or redeploy) to load the new server-side code.'
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
