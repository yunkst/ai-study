/**
 * ESLint Plugin: OpenAPI Validator
 * 检查前端代码与OpenAPI文档的一致性
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 读取OpenAPI文档
function loadOpenApiSpec() {
  try {
    const specPath = path.join(__dirname, 'openapi.json');
    const specContent = fs.readFileSync(specPath, 'utf8');
    return JSON.parse(specContent);
  } catch (error) {
    console.error('Failed to load OpenAPI spec:', error);
    return null;
  }
}

// 解析API路径和方法
function parseApiPaths(spec) {
  if (!spec || !spec.paths) return {};
  
  const apiMap = {};
  
  Object.entries(spec.paths).forEach(([path, methods]) => {
    Object.entries(methods).forEach(([method, details]) => {
      const key = `${method.toUpperCase()} ${path}`;
      apiMap[key] = {
        path,
        method: method.toUpperCase(),
        operationId: details.operationId,
        parameters: details.parameters || [],
        requestBody: details.requestBody,
        responses: details.responses,
        security: details.security
      };
    });
  });
  
  return apiMap;
}

// 解析组件schemas
function parseSchemas(spec) {
  if (!spec || !spec.components || !spec.components.schemas) return {};
  return spec.components.schemas;
}

// 解析模板字符串，提取静态路径部分
function parseTemplateLiteral(node) {
  if (node.type !== 'TemplateLiteral') return null;
  
  let staticPath = '';
  let hasVariables = false;
  
  for (let i = 0; i < node.quasis.length; i++) {
    staticPath += node.quasis[i].value.raw;
    if (i < node.expressions.length) {
      // 有变量表达式，用占位符替代
      staticPath += '{param}';
      hasVariables = true;
    }
  }
  
  return { staticPath, hasVariables };
}

// 检查API调用是否与OpenAPI规范一致
function validateApiCall(node, context, apiMap) {
  const errors = [];
  
  // 检查是否是HTTP方法调用
  if (node.type === 'CallExpression' && 
      node.callee && 
      node.callee.type === 'MemberExpression') {
    
    const methodName = node.callee.property?.name;
    const httpMethods = ['get', 'post', 'put', 'delete', 'patch'];
    
    if (httpMethods.includes(methodName)) {
      const urlArg = node.arguments[0];
      let url = null;
      let isTemplate = false;
      
      // 处理字面量字符串
      if (urlArg && urlArg.type === 'Literal' && typeof urlArg.value === 'string') {
        url = urlArg.value;
      }
      // 处理模板字符串
      else if (urlArg && urlArg.type === 'TemplateLiteral') {
        const parsed = parseTemplateLiteral(urlArg);
        if (parsed) {
          url = parsed.staticPath;
          isTemplate = true;
        }
      }
      
      if (url) {
        const method = methodName.toUpperCase();
        const apiKey = `${method} ${url}`;
        
        // 检查API是否在OpenAPI规范中定义
        if (!apiMap[apiKey]) {
          // 尝试匹配路径参数
          const matchedApi = findMatchingApi(url, method, apiMap);
          if (!matchedApi) {
            const displayUrl = isTemplate ? `模板字符串: ${url}` : url;
            errors.push({
              node: urlArg,
              message: `API端点 "${method} ${displayUrl}" 未在OpenAPI规范中定义。请检查路径是否正确。`
            });
          }
        }
        
        // 检查请求体结构（对于POST/PUT请求）
        if (['POST', 'PUT', 'PATCH'].includes(method) && node.arguments[1]) {
          const apiSpec = apiMap[apiKey] || findMatchingApi(url, method, apiMap);
          
          if (apiSpec && apiSpec.requestBody) {
            // 这里可以添加更详细的请求体验证逻辑
            // 由于静态分析的限制，我们主要检查基本结构
          }
        }
      }
    }
  }
  
  return errors;
}

// 标准化路径，将参数占位符统一
function normalizePath(path) {
  return path.replace(/\{[^}]+\}/g, '{param}');
}

// 查找匹配的API（处理路径参数）
function findMatchingApi(url, method, apiMap) {
  const normalizedUrl = normalizePath(url);
  
  for (const api of Object.values(apiMap)) {
    if (api.method === method) {
      const normalizedApiPath = normalizePath(api.path);
      
      // 精确匹配标准化后的路径
      if (normalizedUrl === normalizedApiPath) {
        return api;
      }
      
      // 如果没有精确匹配，尝试正则表达式匹配
      const pathPattern = api.path.replace(/\{[^}]+\}/g, '[^/]+');
      const regex = new RegExp(`^${pathPattern}$`);
      
      if (regex.test(url)) {
        return api;
      }
    }
  }
  return null;
}

// 检查接口定义是否与OpenAPI一致
function validateInterfaceDefinition(node, context, schemas) {
  const errors = [];
  
  if (node.type === 'TSInterfaceDeclaration') {
    const interfaceName = node.id.name;
    
    // 检查是否有对应的OpenAPI schema
    if (schemas[interfaceName]) {
      const schema = schemas[interfaceName];
      
      // 检查接口属性是否与schema一致
      if (node.body && node.body.body) {
        const interfaceProps = new Set();
        const schemaProps = new Set(Object.keys(schema.properties || {}));
        
        node.body.body.forEach(member => {
          if (member.type === 'TSPropertySignature' && member.key) {
            const propName = member.key.name || member.key.value;
            interfaceProps.add(propName);
            
            // 检查属性是否在schema中定义
            if (!schemaProps.has(propName)) {
              errors.push({
                node: member,
                message: `Property "${propName}" in interface "${interfaceName}" is not defined in OpenAPI schema`
              });
            }
          }
        });
        
        // 检查是否缺少必需的属性
        if (schema.required) {
          schema.required.forEach(requiredProp => {
            if (!interfaceProps.has(requiredProp)) {
              errors.push({
                node: node.id,
                message: `Required property "${requiredProp}" is missing in interface "${interfaceName}"`
              });
            }
          });
        }
      }
    }
  }
  
  return errors;
}

// 主规则定义
const openApiValidatorRule = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Validate API calls and interfaces against OpenAPI specification',
      category: 'Possible Errors',
      recommended: true
    },
    fixable: null,
    schema: []
  },
  
  create(context) {
    const openApiSpec = loadOpenApiSpec();
    if (!openApiSpec) {
      return {};
    }
    
    const apiMap = parseApiPaths(openApiSpec);
    const schemas = parseSchemas(openApiSpec);
    
    return {
      CallExpression(node) {
        const errors = validateApiCall(node, context, apiMap);
        errors.forEach(error => {
          context.report({
            node: error.node,
            message: error.message
          });
        });
      },
      
      TSInterfaceDeclaration(node) {
        const errors = validateInterfaceDefinition(node, context, schemas);
        errors.forEach(error => {
          context.report({
            node: error.node,
            message: error.message
          });
        });
      }
    };
  }
};

// 插件导出
export default {
  meta: {
    name: 'eslint-plugin-openapi-validator',
    version: '1.0.0'
  },
  rules: {
    'validate-api-consistency': openApiValidatorRule
  },
  configs: {
    recommended: {
      plugins: ['openapi-validator'],
      rules: {
        'openapi-validator/validate-api-consistency': 'error'
      }
    }
  }
};