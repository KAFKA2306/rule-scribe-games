module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
  },
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  plugins: ['react', 'react-hooks', 'react-refresh'],
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:react-refresh/recommended',
    'prettier',
  ],
  rules: {
    'react/prop-types': 'off',
    'react/react-in-jsx-scope': 'off',
    'react/jsx-key': 'warn',
    'no-console': 'off',
    'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    'no-undef': 'error',
    'no-unexpected-multiline': 'error',
    'no-constant-condition': ['error', { checkLoops: false }],
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    'react-refresh/only-export-components': 'warn',
  },
  overrides: [
    {
      files: ['*.test.jsx', '*.spec.jsx', 'playwright.config.*'],
      env: {
        node: true,
        jest: true,
      },
    },
  ],
}
