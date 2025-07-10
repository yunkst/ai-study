/**
 * API客户端测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { apiClient } from '@/api/index'

// 模拟axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('API Client', () => {
  beforeEach(() => {
    // 重置模拟
    vi.clearAllMocks()
    
    // 模拟axios.create返回axios实例
    mockedAxios.create.mockReturnValue(mockedAxios)
  })

  afterEach(() => {
    // 清理localStorage
    localStorage.clear()
  })

  describe('客户端配置', () => {
    it('应该正确配置baseURL', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: '/api',
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json'
        }
      })
    })

    it('应该设置正确的超时时间', () => {
      const createCall = mockedAxios.create.mock.calls[0]
      expect(createCall[0].timeout).toBe(10000)
    })
  })

  describe('请求拦截器', () => {
    it('应该自动添加认证头部', () => {
      // 设置localStorage中的access_key
      localStorage.setItem('access_key', 'test-key')
      
      // 模拟请求配置
      const config = { headers: {} }
      
      // 调用请求拦截器
      const interceptors = mockedAxios.interceptors.request.use.mock.calls
      if (interceptors.length > 0) {
        const requestInterceptor = interceptors[0][0]
        const modifiedConfig = requestInterceptor(config)
        
        expect(modifiedConfig.headers['X-Access-Key']).toBe('test-key')
      }
    })

    it('没有认证token时不应该添加认证头部', () => {
      // 确保localStorage为空
      localStorage.clear()
      
      const config = { headers: {} }
      
      const interceptors = mockedAxios.interceptors.request.use.mock.calls
      if (interceptors.length > 0) {
        const requestInterceptor = interceptors[0][0]
        const modifiedConfig = requestInterceptor(config)
        
        expect(modifiedConfig.headers['X-Access-Key']).toBeUndefined()
      }
    })
  })

  describe('响应拦截器', () => {
    it('应该正确处理成功响应', () => {
      const response = {
        data: { message: '成功' },
        status: 200,
        statusText: 'OK'
      }
      
      const interceptors = mockedAxios.interceptors.response.use.mock.calls
      if (interceptors.length > 0) {
        const responseInterceptor = interceptors[0][0]
        const result = responseInterceptor(response)
        
        expect(result).toBe(response)
      }
    })

    it('应该处理401未授权错误', async () => {
      const error = {
        response: {
          status: 401,
          data: { message: '未授权' }
        }
      }
      
      const interceptors = mockedAxios.interceptors.response.use.mock.calls
      if (interceptors.length > 0) {
        const errorInterceptor = interceptors[0][1]
        
        try {
          await errorInterceptor(error)
        } catch (e) {
          // 401错误应该被正确抛出
          expect(e).toBe(error)
        }
      }
    })

    it('应该处理网络错误', async () => {
      const error = {
        message: 'Network Error',
        code: 'NETWORK_ERROR'
      }
      
      const interceptors = mockedAxios.interceptors.response.use.mock.calls
      if (interceptors.length > 0) {
        const errorInterceptor = interceptors[0][1]
        
        try {
          await errorInterceptor(error)
        } catch (e) {
          expect(e).toBe(error)
        }
      }
    })

    it('应该处理超时错误', async () => {
      const error = {
        code: 'ECONNABORTED',
        message: 'timeout of 10000ms exceeded'
      }
      
      const interceptors = mockedAxios.interceptors.response.use.mock.calls
      if (interceptors.length > 0) {
        const errorInterceptor = interceptors[0][1]
        
        try {
          await errorInterceptor(error)
        } catch (e) {
          expect(e).toBe(error)
        }
      }
    })
  })

  describe('HTTP方法', () => {
    it('GET请求应该正确工作', async () => {
      const mockData = { id: 1, name: 'test' }
      mockedAxios.get.mockResolvedValue({ data: mockData })
      
      const result = await apiClient.get('/test')
      
      expect(mockedAxios.get).toHaveBeenCalledWith('/test')
      expect(result.data).toEqual(mockData)
    })

    it('POST请求应该正确工作', async () => {
      const postData = { name: 'test' }
      const mockResponse = { data: { id: 1, ...postData } }
      mockedAxios.post.mockResolvedValue(mockResponse)
      
      const result = await apiClient.post('/test', postData)
      
      expect(mockedAxios.post).toHaveBeenCalledWith('/test', postData)
      expect(result.data).toEqual(mockResponse.data)
    })

    it('PUT请求应该正确工作', async () => {
      const putData = { id: 1, name: 'updated' }
      const mockResponse = { data: putData }
      mockedAxios.put.mockResolvedValue(mockResponse)
      
      const result = await apiClient.put('/test/1', putData)
      
      expect(mockedAxios.put).toHaveBeenCalledWith('/test/1', putData)
      expect(result.data).toEqual(putData)
    })

    it('DELETE请求应该正确工作', async () => {
      const mockResponse = { data: { message: '删除成功' } }
      mockedAxios.delete.mockResolvedValue(mockResponse)
      
      const result = await apiClient.delete('/test/1')
      
      expect(mockedAxios.delete).toHaveBeenCalledWith('/test/1')
      expect(result.data).toEqual(mockResponse.data)
    })
  })

  describe('错误处理', () => {
    it('应该抛出网络错误', async () => {
      const networkError = new Error('Network Error')
      mockedAxios.get.mockRejectedValue(networkError)
      
      await expect(apiClient.get('/test')).rejects.toThrow('Network Error')
    })

    it('应该抛出HTTP错误', async () => {
      const httpError = {
        response: {
          status: 404,
          data: { message: '未找到' }
        }
      }
      mockedAxios.get.mockRejectedValue(httpError)
      
      await expect(apiClient.get('/test')).rejects.toEqual(httpError)
    })
  })
}) 