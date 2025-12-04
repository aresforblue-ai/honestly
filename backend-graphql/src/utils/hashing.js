import crypto from 'crypto';

export function hashContent(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

export function md5Hash(content) {
  return crypto.createHash('md5').update(content).digest('hex');
}

export function generateId() {
  return crypto.randomBytes(16).toString('hex');
}
