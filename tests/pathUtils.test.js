const PathUtils = require('../src/pathUtils');
const path = require('path');
const fs = require('fs');
const os = require('os');

describe('PathUtils', () => {
  describe('normalize', () => {
    it('should normalize a path with redundant separators', () => {
      const result = PathUtils.normalize('/foo//bar///baz');
      expect(result).toBe(path.normalize('/foo//bar///baz'));
    });

    it('should resolve . and .. segments', () => {
      const result = PathUtils.normalize('/foo/bar/../baz/./qux');
      expect(result).toBe(path.normalize('/foo/bar/../baz/./qux'));
    });

    it('should throw error for invalid input', () => {
      expect(() => PathUtils.normalize('')).toThrow('Invalid path: must be a non-empty string');
      expect(() => PathUtils.normalize(null)).toThrow('Invalid path: must be a non-empty string');
      expect(() => PathUtils.normalize(123)).toThrow('Invalid path: must be a non-empty string');
    });
  });

  describe('join', () => {
    it('should join multiple path segments', () => {
      const result = PathUtils.join('foo', 'bar', 'baz');
      expect(result).toBe(path.join('foo', 'bar', 'baz'));
    });

    it('should handle absolute and relative paths', () => {
      const result = PathUtils.join('/foo', 'bar', '../baz');
      expect(result).toBe(path.join('/foo', 'bar', '../baz'));
    });

    it('should throw error when no segments provided', () => {
      expect(() => PathUtils.join()).toThrow('At least one path segment is required');
    });
  });

  describe('resolve', () => {
    it('should resolve to an absolute path', () => {
      const result = PathUtils.resolve('foo', 'bar');
      expect(path.isAbsolute(result)).toBe(true);
    });

    it('should return current directory when no arguments', () => {
      const result = PathUtils.resolve();
      expect(result).toBe(process.cwd());
    });

    it('should resolve multiple segments', () => {
      const result = PathUtils.resolve('/foo', 'bar', 'baz');
      expect(result).toBe(path.resolve('/foo', 'bar', 'baz'));
    });
  });

  describe('relative', () => {
    it('should return relative path between two paths', () => {
      const result = PathUtils.relative('/foo/bar', '/foo/baz');
      expect(result).toBe(path.relative('/foo/bar', '/foo/baz'));
    });

    it('should throw error for missing parameters', () => {
      expect(() => PathUtils.relative('', '/foo')).toThrow('Both from and to paths are required');
      expect(() => PathUtils.relative('/foo', '')).toThrow('Both from and to paths are required');
    });
  });

  describe('dirname', () => {
    it('should return directory name', () => {
      const result = PathUtils.dirname('/foo/bar/baz.txt');
      expect(result).toBe(path.dirname('/foo/bar/baz.txt'));
    });

    it('should throw error for invalid input', () => {
      expect(() => PathUtils.dirname('')).toThrow('Invalid path: must be a non-empty string');
      expect(() => PathUtils.dirname(null)).toThrow('Invalid path: must be a non-empty string');
    });
  });

  describe('basename', () => {
    it('should return base name of path', () => {
      const result = PathUtils.basename('/foo/bar/baz.txt');
      expect(result).toBe('baz.txt');
    });

    it('should remove extension when provided', () => {
      const result = PathUtils.basename('/foo/bar/baz.txt', '.txt');
      expect(result).toBe('baz');
    });

    it('should throw error for invalid input', () => {
      expect(() => PathUtils.basename('')).toThrow('Invalid path: must be a non-empty string');
    });
  });

  describe('extname', () => {
    it('should return file extension', () => {
      const result = PathUtils.extname('/foo/bar/baz.txt');
      expect(result).toBe('.txt');
    });

    it('should return empty string for no extension', () => {
      const result = PathUtils.extname('/foo/bar/baz');
      expect(result).toBe('');
    });

    it('should throw error for invalid input', () => {
      expect(() => PathUtils.extname('')).toThrow('Invalid path: must be a non-empty string');
    });
  });

  describe('parse', () => {
    it('should parse path into components', () => {
      const result = PathUtils.parse('/foo/bar/baz.txt');
      expect(result).toHaveProperty('root');
      expect(result).toHaveProperty('dir');
      expect(result).toHaveProperty('base');
      expect(result).toHaveProperty('ext');
      expect(result).toHaveProperty('name');
      expect(result.base).toBe('baz.txt');
      expect(result.ext).toBe('.txt');
      expect(result.name).toBe('baz');
    });

    it('should throw error for invalid input', () => {
      expect(() => PathUtils.parse('')).toThrow('Invalid path: must be a non-empty string');
    });
  });

  describe('format', () => {
    it('should format path object into string', () => {
      const pathObj = {
        root: '/',
        dir: '/foo/bar',
        base: 'baz.txt',
        ext: '.txt',
        name: 'baz'
      };
      const result = PathUtils.format(pathObj);
      expect(result).toBe(path.format(pathObj));
    });

    it('should throw error for invalid input', () => {
      expect(() => PathUtils.format(null)).toThrow('Invalid path object');
      expect(() => PathUtils.format('string')).toThrow('Invalid path object');
    });
  });

  describe('isAbsolute', () => {
    it('should return true for absolute paths', () => {
      expect(PathUtils.isAbsolute('/foo/bar')).toBe(true);
    });

    it('should return false for relative paths', () => {
      expect(PathUtils.isAbsolute('foo/bar')).toBe(false);
      expect(PathUtils.isAbsolute('./foo')).toBe(false);
    });

    it('should return false for invalid input', () => {
      expect(PathUtils.isAbsolute('')).toBe(false);
      expect(PathUtils.isAbsolute(null)).toBe(false);
    });
  });

  describe('sanitize', () => {
    it('should remove null bytes from path', () => {
      const result = PathUtils.sanitize('foo\0bar');
      expect(result).not.toContain('\0');
    });

    it('should normalize the path', () => {
      const result = PathUtils.sanitize('foo//bar/../baz');
      expect(result).toBe(path.normalize('foo//bar/../baz'));
    });

    it('should restrict path within base directory', () => {
      const baseDir = '/home/user';
      const result = PathUtils.sanitize('docs/file.txt', baseDir);
      expect(result.startsWith(baseDir)).toBe(true);
    });

    it('should throw error for path traversal attempts', () => {
      const baseDir = '/home/user';
      expect(() => PathUtils.sanitize('../../../etc/passwd', baseDir)).toThrow('Path traversal detected');
    });

    it('should throw error for invalid input', () => {
      expect(() => PathUtils.sanitize('')).toThrow('Invalid path: must be a non-empty string');
      expect(() => PathUtils.sanitize(null)).toThrow('Invalid path: must be a non-empty string');
    });
  });

  describe('exists', () => {
    it('should return true for existing paths', () => {
      expect(PathUtils.exists(__filename)).toBe(true);
      expect(PathUtils.exists(__dirname)).toBe(true);
    });

    it('should return false for non-existing paths', () => {
      expect(PathUtils.exists('/nonexistent/path/to/nowhere')).toBe(false);
    });

    it('should return false for invalid input', () => {
      expect(PathUtils.exists('')).toBe(false);
      expect(PathUtils.exists(null)).toBe(false);
    });
  });

  describe('isFile', () => {
    it('should return true for files', () => {
      expect(PathUtils.isFile(__filename)).toBe(true);
    });

    it('should return false for directories', () => {
      expect(PathUtils.isFile(__dirname)).toBe(false);
    });

    it('should return false for non-existing paths', () => {
      expect(PathUtils.isFile('/nonexistent/file.txt')).toBe(false);
    });

    it('should return false for invalid input', () => {
      expect(PathUtils.isFile('')).toBe(false);
      expect(PathUtils.isFile(null)).toBe(false);
    });
  });

  describe('isDirectory', () => {
    it('should return true for directories', () => {
      expect(PathUtils.isDirectory(__dirname)).toBe(true);
    });

    it('should return false for files', () => {
      expect(PathUtils.isDirectory(__filename)).toBe(false);
    });

    it('should return false for non-existing paths', () => {
      expect(PathUtils.isDirectory('/nonexistent/directory')).toBe(false);
    });

    it('should return false for invalid input', () => {
      expect(PathUtils.isDirectory('')).toBe(false);
      expect(PathUtils.isDirectory(null)).toBe(false);
    });
  });

  describe('ensureDir', () => {
    let tempDir;

    beforeEach(() => {
      tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'test-'));
    });

    afterEach(() => {
      if (fs.existsSync(tempDir)) {
        fs.rmSync(tempDir, { recursive: true, force: true });
      }
    });

    it('should create a directory if it does not exist', () => {
      const newDir = path.join(tempDir, 'newdir');
      expect(fs.existsSync(newDir)).toBe(false);
      
      PathUtils.ensureDir(newDir);
      
      expect(fs.existsSync(newDir)).toBe(true);
      expect(fs.statSync(newDir).isDirectory()).toBe(true);
    });

    it('should not fail if directory already exists', () => {
      expect(() => PathUtils.ensureDir(tempDir)).not.toThrow();
      expect(fs.existsSync(tempDir)).toBe(true);
    });

    it('should create nested directories', () => {
      const nestedDir = path.join(tempDir, 'level1', 'level2', 'level3');
      
      PathUtils.ensureDir(nestedDir);
      
      expect(fs.existsSync(nestedDir)).toBe(true);
      expect(fs.statSync(nestedDir).isDirectory()).toBe(true);
    });

    it('should throw error for invalid input', () => {
      expect(() => PathUtils.ensureDir('')).toThrow('Invalid directory path: must be a non-empty string');
      expect(() => PathUtils.ensureDir(null)).toThrow('Invalid directory path: must be a non-empty string');
    });
  });

  describe('separator and delimiter', () => {
    it('should return platform-specific separator', () => {
      expect(PathUtils.separator).toBe(path.sep);
    });

    it('should return platform-specific delimiter', () => {
      expect(PathUtils.delimiter).toBe(path.delimiter);
    });
  });
});
