/**
 * 管理API接口
 */

import { request } from './index'

export const adminApi = {
  // ==================== AI配置管理 ====================
  
  /**
   * 获取AI供应商列表
   */
  getAiProviders() {
    return request.get('/admin/ai/providers')
  },

  /**
   * 创建AI供应商
   */
  createAiProvider(data: any) {
    return request.post('/admin/ai/providers', data)
  },

  /**
   * 更新AI供应商
   */
  updateAiProvider(providerName: string, data: any) {
    return request.put(`/admin/ai/providers/${providerName}`, data)
  },

  /**
   * 获取当前AI服务配置
   */
  getAiConfig() {
    return request.get('/admin/ai/config')
  },

  /**
   * 设置API密钥
   */
  setApiKey(providerName: string, data: any) {
    return request.post(`/admin/ai/api-keys/${providerName}`, data)
  },

  /**
   * 激活AI服务
   */
  activateAiService(serviceType: string, providerName: string, modelName: string) {
    return request.post(`/admin/ai/services/${serviceType}/activate`, null, {
      params: {
        provider_name: providerName,
        model_name: modelName
      }
    })
  },

  /**
   * 测试AI供应商连接
   */
  testAiProvider(providerName: string, apiKey?: string, modelName?: string) {
    const params: any = {}
    if (apiKey) params.api_key = apiKey
    if (modelName) params.model_name = modelName
    
    return request.post(`/admin/ai/test/${providerName}`, null, { params })
  },

  /**
   * 获取Ollama状态
   */
  getOllamaStatus() {
    return request.get('/admin/ai/ollama/status')
  },

  /**
   * 初始化默认AI供应商
   */
  initializeAiProviders() {
    return request.post('/admin/ai/initialize')
  },

  // ==================== 系统管理 ====================
  
  /**
   * 获取系统状态
   */
  getSystemStatus() {
    return request.get('/admin/status')
  },

  /**
   * 获取系统配置
   */
  getSystemConfig() {
    return request.get('/admin/config')
  },

  /**
   * 更新系统配置
   */
  updateSystemConfig(data: any) {
    return request.put('/admin/config', data)
  },

  /**
   * 获取系统日志
   */
  getSystemLogs(params?: any) {
    return request.get('/admin/logs', { params })
  },

  /**
   * 获取活跃任务
   */
  getActiveTasks() {
    return request.get('/admin/tasks')
  },

  /**
   * 触发维护任务
   */
  triggerMaintenance(data: any) {
    return request.post('/admin/maintenance', data)
  },

  /**
   * 获取管理员概览
   */
  getAdminOverview() {
    return request.get('/admin/stats/overview')
  },

  /**
   * 清理缓存
   */
  clearCache(cacheType = 'all') {
    return request.post('/admin/cache/clear', null, {
      params: { cache_type: cacheType }
    })
  }
} 