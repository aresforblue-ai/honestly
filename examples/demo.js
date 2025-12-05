#!/usr/bin/env node

/**
 * Demo script showing the usage of the honestly path utilities library
 */

const { PathUtils } = require('../src/index');

console.log('=== Honestly Path Utilities Demo ===\n');

// 1. Normalize paths
console.log('1. Path Normalization:');
console.log('   Input:  /foo//bar///baz');
console.log('   Output:', PathUtils.normalize('/foo//bar///baz'));
console.log();

// 2. Join paths
console.log('2. Joining Paths:');
console.log('   Input:  "foo", "bar", "baz.txt"');
console.log('   Output:', PathUtils.join('foo', 'bar', 'baz.txt'));
console.log();

// 3. Resolve to absolute
console.log('3. Resolve to Absolute:');
console.log('   Input:  "foo", "bar"');
console.log('   Output:', PathUtils.resolve('foo', 'bar'));
console.log();

// 4. Get relative path
console.log('4. Relative Path:');
console.log('   From:   /foo/bar');
console.log('   To:     /foo/baz/qux');
console.log('   Result:', PathUtils.relative('/foo/bar', '/foo/baz/qux'));
console.log();

// 5. Parse path
console.log('5. Parse Path Components:');
const parsed = PathUtils.parse('/home/user/docs/file.txt');
console.log('   Input:', '/home/user/docs/file.txt');
console.log('   Root:', parsed.root);
console.log('   Dir:', parsed.dir);
console.log('   Base:', parsed.base);
console.log('   Name:', parsed.name);
console.log('   Ext:', parsed.ext);
console.log();

// 6. Check path properties
console.log('6. Path Properties:');
console.log('   __filename is absolute?', PathUtils.isAbsolute(__filename));
console.log('   __filename exists?', PathUtils.exists(__filename));
console.log('   __filename is file?', PathUtils.isFile(__filename));
console.log('   __dirname is directory?', PathUtils.isDirectory(__dirname));
console.log();

// 7. Sanitize path
console.log('7. Path Sanitization:');
try {
  const baseDir = '/home/user';
  console.log('   Base directory:', baseDir);
  console.log('   Safe path:', PathUtils.sanitize('docs/file.txt', baseDir));
  console.log('   Attempting traversal: ../../../etc/passwd');
  PathUtils.sanitize('../../../etc/passwd', baseDir);
} catch (error) {
  console.log('   ✓ Blocked:', error.message);
}
console.log();

// 8. Path utilities
console.log('8. Other Utilities:');
console.log('   Directory name of /foo/bar/baz.txt:', PathUtils.dirname('/foo/bar/baz.txt'));
console.log('   Base name of /foo/bar/baz.txt:', PathUtils.basename('/foo/bar/baz.txt'));
console.log('   Extension of /foo/bar/baz.txt:', PathUtils.extname('/foo/bar/baz.txt'));
console.log('   Platform separator:', PathUtils.separator);
console.log('   Platform delimiter:', PathUtils.delimiter);
console.log();

console.log('=== Demo Complete ===');
