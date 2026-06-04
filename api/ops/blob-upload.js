// POST /api/ops/blob-upload — client-upload handler for Vercel Blob.
// Lets the ops console upload large guide files DIRECTLY from the browser to
// Blob storage (bypassing the 4.5 MB serverless body limit). The function only
// issues a short-lived upload token; the file never passes through it.
//
// Two phases (Vercel Blob client-upload protocol):
//   'blob.generate-client-token' — from the browser (carries the ops cookie) → gated
//   'blob.upload-completed'       — server→server callback from Vercel → verified by signature
'use strict';
const { handleUpload } = require('@vercel/blob/client');
const ops = require('../_ops');

const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'application/zip',
  'application/x-zip-compressed',
  'application/octet-stream',
  'text/plain',
  '*', // permissive fallback so an odd browser-reported type doesn't block ops
];

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  if (req.method !== 'POST') { res.statusCode = 405; return res.end(JSON.stringify({ error: 'method not allowed' })); }

  let body;
  try { body = await ops.readLargeJson(req, 256 * 1024); }
  catch (e) { res.statusCode = 400; return res.end(JSON.stringify({ error: 'bad body' })); }

  // Gate the token-generation phase (browser request); the completion callback
  // from Vercel has no cookie and is verified by signature inside handleUpload.
  if (body && body.type === 'blob.generate-client-token' && !ops.isAuthed(req)) {
    res.statusCode = 401; return res.end(JSON.stringify({ error: 'unauthorized' }));
  }

  try {
    const json = await handleUpload({
      body: body,
      request: req,
      token: process.env.BLOB_READ_WRITE_TOKEN,
      onBeforeGenerateToken: async function () {
        return { allowedContentTypes: ALLOWED_TYPES, addRandomSuffix: true, maximumSizeInBytes: 50 * 1024 * 1024 };
      },
      onUploadCompleted: async function () { /* nothing to do server-side */ },
    });
    res.statusCode = 200;
    return res.end(JSON.stringify(json));
  } catch (e) {
    console.error('blob-upload failed:', e.message);
    res.statusCode = 400;
    return res.end(JSON.stringify({ error: e.message }));
  }
};
