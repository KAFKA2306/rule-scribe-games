import globals from 'globals'
import js from '@eslint/js'
import reactRecommended from 'eslint-plugin-react/configs/recommended.js'
import reactHooksPlugin from 'eslint-plugin-react-hooks'
import reactRefreshPlugin from 'eslint-plugin-react-refresh'
import prettier from 'eslint-config-prettier'
import babelParser from '@babel/eslint-parser'
export default [
  {
    ignores: ['node_modules', 'dist', 'playwright-report', 'coverage'],
  },
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      parser: babelParser,
      parserOptions: {
        requireConfigFile: false,
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
        babelOptions: { presets: ['@babel/preset-react'] },
      },
      globals: {
        ...globals.browser,
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    plugins: {
      react: reactRecommended.plugins.react,
      'react-hooks': reactHooksPlugin,
      'react-refresh': reactRefreshPlugin,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactRecommended.rules,
      ...reactHooksPlugin.configs.recommended.rules,
      ...reactRefreshPlugin.configs.recommended.rules,
      'react/prop-types': 'off',
      'react/react-in-jsx-scope': 'off',
      'react/jsx-key': 'warn',
      'no-console': 'off',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'no-undef': 'error',
      'no-unexpected-multiline': 'error',
      'no-constant-condition': ['error', { checkLoops: false }],
    },
  },
  {
    files: ['**/*.test.jsx', '**/*.spec.jsx', 'playwright.config.*'],
    languageOptions: {
      globals: {
        ...globals.node,
        jest: true,
      },
    },
  },
  prettier,
]
