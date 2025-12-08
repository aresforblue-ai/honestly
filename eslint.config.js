module.exports = [
  {
    files: ['**/*.js'],
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/coverage/**',
      'backend-graphql/**',  // Has its own config
      'frontend-app/**',     // Has its own config
      'conductme/**',        // Has its own config
    ],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'commonjs',
      globals: {
        // Node.js globals
        __dirname: 'readonly',
        __filename: 'readonly',
        exports: 'writable',
        module: 'readonly',
        require: 'readonly',
        process: 'readonly',
        console: 'readonly',
        Buffer: 'readonly',
        // Jest globals
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        test: 'readonly',
        jest: 'readonly',
      },
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-console': 'off',
      'semi': ['error', 'always'],
      'quotes': ['error', 'single'],
      'indent': ['error', 2],
    },
  },
  // K6 test files use ES modules
  {
    files: ['tests/load/**/*.js', 'tests/perf/**/*.js', 'perf/**/*.js'],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'module',
      globals: {
        __ENV: 'readonly',
        console: 'readonly',
      },
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-console': 'off',
      'semi': ['error', 'always'],
      'quotes': ['error', 'double'],  // k6 examples use double quotes
      'indent': ['error', 2],
    },
  },
];
