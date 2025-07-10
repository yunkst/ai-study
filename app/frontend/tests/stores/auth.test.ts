/**
 * 认证Store测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import * as authApi from '@/api/auth'

// 模拟API模块
vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
}))

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    
    // 清理localStorage
    localStorage.clear()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useAuthStore()
      
      expect(store.isAuthenticated).toBe(false)
      expect(store.accessKey).toBe('')
    })

    it('应该从localStorage恢复认证状态', () => {
      // 设置localStorage
      localStorage.setItem('auth_token', 'test-token')
      localStorage.setItem('access_key', 'test-key')
      
      const store = useAuthStore()
      
      // 应该恢复状态
      expect(store.isAuthenticated).toBe(true)
      expect(store.accessKey).toBe('test-key')
    })
  })

  describe('登录功能', () => {
    it('成功登录应该更新状态', async () => {
      const store = useAuthStore()
      const mockResponse = {
        data: {
          success: true,
          message: '登录成功',
          token: 'test-token'
        }
      }
      
      // 模拟API成功响应
      vi.mocked(authApi.login).mockResolvedValue(mockResponse)
      
      const result = await store.login('test-key')
      
      expect(result).toBe(true)
      expect(store.isAuthenticated).toBe(true)
      expect(store.accessKey).toBe('test-key')
      expect(localStorage.getItem('access_key')).toBe('test-key')
    })

    it('登录失败应该保持原状态', async () => {
      const store = useAuthStore()
      
      // 模拟API失败响应
      vi.mocked(authApi.login).mockRejectedValue(new Error('登录失败'))
      
      const result = await store.login('wrong-key')
      
      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      expect(store.accessKey).toBe('')
    })

    it('无密钥模式应该直接成功', async () => {
      const store = useAuthStore()
      const mockResponse = {
        data: {
          success: true,
          message: '无需密钥',
        }
      }
      
      vi.mocked(authApi.login).mockResolvedValue(mockResponse)
      
      const result = await store.login('')
      
      expect(result).toBe(true)
      expect(store.isAuthenticated).toBe(true)
    })
  })

  describe('登出功能', () => {
    it('登出应该清除状态', async () => {
      const store = useAuthStore()
      
      // 先设置登录状态
      store.isAuthenticated = true
      store.accessKey = 'test-key'
      localStorage.setItem('auth_token', 'test-token')
      localStorage.setItem('access_key', 'test-key')
      
      // 模拟API响应
      vi.mocked(authApi.logout).mockResolvedValue({ data: { success: true } })
      
      await store.logout()
      
      expect(store.isAuthenticated).toBe(false)
      expect(store.accessKey).toBe('')
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('access_key')).toBeNull()
    })

    it('登出API失败也应该清除本地状态', async () => {
      const store = useAuthStore()
      
      // 先设置登录状态
      store.isAuthenticated = true
      store.accessKey = 'test-key'
      
      // 模拟API失败
      vi.mocked(authApi.logout).mockRejectedValue(new Error('网络错误'))
      
      await store.logout()
      
      // 即使API失败，本地状态也应该被清除
      expect(store.isAuthenticated).toBe(false)
      expect(store.accessKey).toBe('')
    })
  })

  describe('持久化', () => {
    it('状态变化应该自动保存到localStorage', () => {
      const store = useAuthStore()
      
      // 手动设置状态
      store.isAuthenticated = true
      store.accessKey = 'new-key'
      
      // 应该自动保存
      expect(localStorage.getItem('access_key')).toBe('new-key')
    })

    it('清除状态应该同时清除localStorage', () => {
      const store = useAuthStore()
      
      // 先设置状态
      store.isAuthenticated = true
      store.accessKey = 'test-key'
      
      // 清除状态
      store.isAuthenticated = false
      store.accessKey = ''
      
      // localStorage也应该被清除
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('access_key')).toBeNull()
    })
  })

  describe('错误处理', () => {
    it('应该处理网络错误', async () => {
      const store = useAuthStore()
      
      // 模拟网络错误
      vi.mocked(authApi.login).mockRejectedValue(new Error('网络连接失败'))
      
      const result = await store.login('test-key')
      
      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })

    it('应该处理API错误响应', async () => {
      const store = useAuthStore()
      const errorResponse = {
        response: {
          status: 401,
          data: { message: '密钥无效' }
        }
      }
      
      vi.mocked(authApi.login).mockRejectedValue(errorResponse)
      
      const result = await store.login('invalid-key')
      
      expect(result).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })
  })
}) 