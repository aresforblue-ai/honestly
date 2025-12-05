/**
 * Honestly - Path Utilities Library
 * A comprehensive set of tools for path handling, validation, and sanitization
 */

const PathUtils = require('./pathUtils');

module.exports = {
  PathUtils,
  // Export individual methods for convenience
  normalize: PathUtils.normalize.bind(PathUtils),
  join: PathUtils.join.bind(PathUtils),
  resolve: PathUtils.resolve.bind(PathUtils),
  relative: PathUtils.relative.bind(PathUtils),
  dirname: PathUtils.dirname.bind(PathUtils),
  basename: PathUtils.basename.bind(PathUtils),
  extname: PathUtils.extname.bind(PathUtils),
  parse: PathUtils.parse.bind(PathUtils),
  format: PathUtils.format.bind(PathUtils),
  isAbsolute: PathUtils.isAbsolute.bind(PathUtils),
  sanitize: PathUtils.sanitize.bind(PathUtils),
  exists: PathUtils.exists.bind(PathUtils),
  isFile: PathUtils.isFile.bind(PathUtils),
  isDirectory: PathUtils.isDirectory.bind(PathUtils),
  ensureDir: PathUtils.ensureDir.bind(PathUtils),
};
