/**
 * ESLint plugin to prevent direct axios usage outside of http.ts
 */

/* eslint-env node */
/* eslint no-undef: "off" */
/* eslint @typescript-eslint/no-require-imports: "off" */

const path = require('path');

module.exports = {
  rules: {
    'no-direct-axios': {
      meta: {
        type: 'problem',
        docs: {
          description: 'Disallow direct axios usage outside of http.ts service',
          category: 'Best Practices',
          recommended: true
        },
        fixable: null,
        schema: []
      },
      create(context) {
        const filename = context.getFilename();
        const normalizedFilename = path.normalize(filename).replace(/\\/g, '/');
        
        // Allow axios usage only in http.ts
        const isHttpService = normalizedFilename.includes('/services/http.ts');
        
        if (isHttpService) {
          return {}; // No rules for http.ts
        }

        return {
          ImportDeclaration(node) {
            // Check for direct axios imports
            if (node.source.value === 'axios') {
              context.report({
                node,
                message: 'Direct axios import is not allowed. Use httpService from @/services/http instead.'
              });
            }
          },
          
          CallExpression(node) {
            // Check for axios method calls
            if (
              node.callee.type === 'MemberExpression' &&
              node.callee.object.name === 'axios'
            ) {
              context.report({
                node,
                message: 'Direct axios usage is not allowed. Use httpService from @/services/http instead.'
              });
            }
            
            // Check for direct axios() calls
            if (
              node.callee.type === 'Identifier' &&
              node.callee.name === 'axios'
            ) {
              context.report({
                node,
                message: 'Direct axios usage is not allowed. Use httpService from @/services/http instead.'
              });
            }
          },
          
          VariableDeclarator(node) {
            // Check for axios destructuring
            if (
              node.init &&
              node.init.type === 'CallExpression' &&
              node.init.callee.name === 'require' &&
              node.init.arguments[0] &&
              node.init.arguments[0].value === 'axios'
            ) {
              context.report({
                node,
                message: 'Direct axios require is not allowed. Use httpService from @/services/http instead.'
              });
            }
          }
        };
      }
    }
  }
};