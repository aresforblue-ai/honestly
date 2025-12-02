# honestly

A comprehensive path utilities library for Node.js that provides robust path handling, validation, and sanitization functions.

## Features

- 🛡️ **Path Sanitization**: Prevent directory traversal attacks
- ✅ **Path Validation**: Check if paths exist, are files, or directories
- 🔧 **Path Manipulation**: Normalize, join, resolve, and parse paths
- 🔒 **Security**: Built-in protection against common path-based vulnerabilities
- 📦 **Zero Dependencies**: Uses only Node.js built-in modules

## Installation

```bash
npm install honestly
```

## Usage

```javascript
const { PathUtils } = require('honestly');

// Normalize paths
const normalized = PathUtils.normalize('/foo//bar/../baz');

// Join path segments
const joined = PathUtils.join('foo', 'bar', 'baz.txt');

// Resolve to absolute path
const absolute = PathUtils.resolve('foo', 'bar');

// Sanitize paths to prevent directory traversal
const safe = PathUtils.sanitize('docs/file.txt', '/home/user');

// Check if path exists
if (PathUtils.exists('/path/to/file')) {
  console.log('File exists!');
}

// Ensure directory exists
PathUtils.ensureDir('/path/to/new/directory');
```

## API Reference

### PathUtils.normalize(inputPath)
Normalize a path to remove redundant separators and resolve `.` and `..` segments.

### PathUtils.join(...segments)
Join multiple path segments together.

### PathUtils.resolve(...pathSegments)
Resolve a sequence of paths into an absolute path.

### PathUtils.relative(from, to)
Get the relative path from one location to another.

### PathUtils.dirname(filePath)
Get the directory name of a path.

### PathUtils.basename(filePath, ext)
Get the base name of a path (filename with extension).

### PathUtils.extname(filePath)
Get the extension of a path.

### PathUtils.parse(filePath)
Parse a path into its components (root, dir, base, ext, name).

### PathUtils.format(pathObject)
Format a path object into a path string.

### PathUtils.isAbsolute(inputPath)
Check if a path is absolute.

### PathUtils.sanitize(inputPath, baseDir)
Sanitize a path to prevent directory traversal attacks.

### PathUtils.exists(inputPath)
Check if a path exists.

### PathUtils.isFile(inputPath)
Check if a path is a file.

### PathUtils.isDirectory(inputPath)
Check if a path is a directory.

### PathUtils.ensureDir(dirPath)
Ensure a directory exists, creating it if necessary.

## Security

This library includes built-in security features:
- Null byte removal
- Directory traversal prevention
- Path validation and sanitization

## Testing

```bash
npm test
npm run test:coverage
npm run test:watch
```

## Linting

```bash
npm run lint
npm run lint:fix
```

## License

ISC
