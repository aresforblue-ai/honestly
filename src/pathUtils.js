const path = require('path');
const fs = require('fs');

/**
 * Path Utilities Module
 * Provides comprehensive path handling, validation, and sanitization functions
 */

class PathUtils {
  /**
   * Normalize a path to remove redundant separators and resolve . and .. segments
   * @param {string} inputPath - The path to normalize
   * @returns {string} The normalized path
   */
  static normalize(inputPath) {
    if (!inputPath || typeof inputPath !== 'string') {
      throw new Error('Invalid path: must be a non-empty string');
    }
    return path.normalize(inputPath);
  }

  /**
   * Join multiple path segments together
   * @param {...string} segments - Path segments to join
   * @returns {string} The joined path
   */
  static join(...segments) {
    if (segments.length === 0) {
      throw new Error('At least one path segment is required');
    }
    return path.join(...segments);
  }

  /**
   * Resolve a sequence of paths into an absolute path
   * @param {...string} pathSegments - Path segments to resolve
   * @returns {string} The resolved absolute path
   */
  static resolve(...pathSegments) {
    if (pathSegments.length === 0) {
      return process.cwd();
    }
    return path.resolve(...pathSegments);
  }

  /**
   * Get the relative path from one location to another
   * @param {string} from - The source path
   * @param {string} to - The destination path
   * @returns {string} The relative path
   */
  static relative(from, to) {
    if (!from || !to) {
      throw new Error('Both from and to paths are required');
    }
    return path.relative(from, to);
  }

  /**
   * Get the directory name of a path
   * @param {string} filePath - The file path
   * @returns {string} The directory name
   */
  static dirname(filePath) {
    if (!filePath || typeof filePath !== 'string') {
      throw new Error('Invalid path: must be a non-empty string');
    }
    return path.dirname(filePath);
  }

  /**
   * Get the base name of a path (filename with extension)
   * @param {string} filePath - The file path
   * @param {string} ext - Optional extension to remove
   * @returns {string} The base name
   */
  static basename(filePath, ext = '') {
    if (!filePath || typeof filePath !== 'string') {
      throw new Error('Invalid path: must be a non-empty string');
    }
    return path.basename(filePath, ext);
  }

  /**
   * Get the extension of a path
   * @param {string} filePath - The file path
   * @returns {string} The extension (including the dot)
   */
  static extname(filePath) {
    if (!filePath || typeof filePath !== 'string') {
      throw new Error('Invalid path: must be a non-empty string');
    }
    return path.extname(filePath);
  }

  /**
   * Parse a path into its components
   * @param {string} filePath - The file path
   * @returns {object} Object with root, dir, base, ext, and name properties
   */
  static parse(filePath) {
    if (!filePath || typeof filePath !== 'string') {
      throw new Error('Invalid path: must be a non-empty string');
    }
    return path.parse(filePath);
  }

  /**
   * Format a path object into a path string
   * @param {object} pathObject - Object with root, dir, base, ext, and/or name properties
   * @returns {string} The formatted path
   */
  static format(pathObject) {
    if (!pathObject || typeof pathObject !== 'object') {
      throw new Error('Invalid path object');
    }
    return path.format(pathObject);
  }

  /**
   * Check if a path is absolute
   * @param {string} inputPath - The path to check
   * @returns {boolean} True if the path is absolute
   */
  static isAbsolute(inputPath) {
    if (!inputPath || typeof inputPath !== 'string') {
      return false;
    }
    return path.isAbsolute(inputPath);
  }

  /**
   * Sanitize a path to prevent directory traversal attacks
   * @param {string} inputPath - The path to sanitize
   * @param {string} baseDir - Optional base directory to restrict the path within
   * @returns {string} The sanitized path
   */
  static sanitize(inputPath, baseDir = null) {
    if (!inputPath || typeof inputPath !== 'string') {
      throw new Error('Invalid path: must be a non-empty string');
    }

    // Remove null bytes
    const cleaned = inputPath.replace(/\0/g, '');
    
    // Normalize the path
    const normalized = path.normalize(cleaned);

    // If baseDir is provided, ensure the path stays within it
    if (baseDir) {
      const resolvedBase = path.resolve(baseDir);
      const resolvedPath = path.resolve(resolvedBase, normalized);
      
      // Check if the resolved path is within the base directory
      if (!resolvedPath.startsWith(resolvedBase)) {
        throw new Error('Path traversal detected: path is outside base directory');
      }
      
      return resolvedPath;
    }

    return normalized;
  }

  /**
   * Check if a path exists
   * @param {string} inputPath - The path to check
   * @returns {boolean} True if the path exists
   */
  static exists(inputPath) {
    if (!inputPath || typeof inputPath !== 'string') {
      return false;
    }
    try {
      fs.accessSync(inputPath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if a path is a file
   * @param {string} inputPath - The path to check
   * @returns {boolean} True if the path is a file
   */
  static isFile(inputPath) {
    if (!inputPath || typeof inputPath !== 'string') {
      return false;
    }
    try {
      const stats = fs.statSync(inputPath);
      return stats.isFile();
    } catch {
      return false;
    }
  }

  /**
   * Check if a path is a directory
   * @param {string} inputPath - The path to check
   * @returns {boolean} True if the path is a directory
   */
  static isDirectory(inputPath) {
    if (!inputPath || typeof inputPath !== 'string') {
      return false;
    }
    try {
      const stats = fs.statSync(inputPath);
      return stats.isDirectory();
    } catch {
      return false;
    }
  }

  /**
   * Ensure a directory exists, creating it if necessary
   * @param {string} dirPath - The directory path
   * @returns {boolean} True if the directory was created or already exists
   */
  static ensureDir(dirPath) {
    if (!dirPath || typeof dirPath !== 'string') {
      throw new Error('Invalid directory path: must be a non-empty string');
    }
    try {
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
      }
      return true;
    } catch (error) {
      throw new Error(`Failed to create directory: ${error.message}`);
    }
  }

  /**
   * Get the platform-specific path separator
   * @returns {string} The path separator (/ or \)
   */
  static get separator() {
    return path.sep;
  }

  /**
   * Get the platform-specific path delimiter
   * @returns {string} The path delimiter (; or :)
   */
  static get delimiter() {
    return path.delimiter;
  }
}

module.exports = PathUtils;
