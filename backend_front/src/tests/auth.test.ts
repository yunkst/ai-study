import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import httpService from '@/services/http'
import { authApi } from '@/services/api'
import type { User, LoginForm, RegisterForm } from '@/services/api'

// Mock dependencies
vi.mock('@/services/http')
vi.mock('@/services/api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn()
  }
}))
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))
vi.mock('@/router', () => ({
  default: {
    push: vi.fn()
  }
}))

describe('Auth Store', () => {
  let authStore: ReturnType<typeof useAuthStore>
  
  beforeEach(() => {
    setActivePinia(createPinia())
    authStore = useAuthStore()
    
    // Clear localStorage
    localStorage.clear()
    
    // Reset all mocks
    vi.clearAllMocks()
  })
  
  afterEach(() => {
    localStorage.clear()
  })

  describe('初始化', () => {
    it('应该从localStorage初始化token', () => {
      const testToken = 'test-token'
      vi.mocked(localStorage.getItem).mockReturnValue(testToken)
      
      // 重新创建store以触发初始化
      setActivePinia(createPinia())
      const authStore = useAuthStore()

      expect(authStore.token).toBe(testToken)
      expect(authStore.isAuthenticated).toBe(true)
    })

    it('应该在没有token时保持未认证状态', () => {
      vi.mocked(localStorage.getItem).mockReturnValue(null)
      
      setActivePinia(createPinia())
      const authStore = useAuthStore()

      expect(authStore.token).toBeNull()
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
    })
  })

  describe('登录功能', () => {
    const mockLoginForm: LoginForm = {
      username: 'testuser',
      password: 'testpass'
    }

    const mockLoginResponse = {
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'Bearer'
    }

    const mockUser: User = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z'
    }

    it('应该成功登录并设置token', async () => {
      vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)
      
      const result = await authStore.login(mockLoginForm)
      
      expect(result).toBe(true)
      expect(authStore.token).toBe(mockLoginResponse.access_token)
      expect(authStore.user).toEqual(mockUser)
      expect(authStore.isAuthenticated).toBe(true)
      expect(httpService.setToken).toHaveBeenCalledWith(mockLoginResponse.access_token)
      expect(httpService.setRefreshToken).toHaveBeenCalledWith(mockLoginResponse.refresh_token)
    })

    it('应该处理登录失败', async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error('Login failed'))
      
      const result = await authStore.login(mockLoginForm)
      
      expect(result).toBe(false)
      expect(authStore.token).toBe(null)
       expect(authStore.user).toBe(null)
       expect(authStore.isAuthenticated).toBe(false)
     })

    it('应该在获取用户信息失败时清除认证状态', async () => {
      vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)
      vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error('Get user failed'))
      
      const result = await authStore.login(mockLoginForm)
      
      expect(result).toBe(true)
      // 由于getCurrentUser失败，clearAuth会被调用，token会被清除
      expect(authStore.token).toBe(null)
      expect(authStore.user).toBe(null)
    })
  })

  describe('注册功能', () => {
    const mockRegisterForm: RegisterForm = {
      username: 'newuser',
      email: 'new@example.com',
      password: 'newpass'
    }

    it('应该成功注册', async () => {
      vi.mocked(authApi.register).mockResolvedValue(undefined)
      
      const result = await authStore.register(mockRegisterForm)
      
      expect(result).toBe(true)
      expect(authApi.register).toHaveBeenCalledWith(mockRegisterForm)
    })

    it('应该处理注册失败', async () => {
      vi.mocked(authApi.register).mockRejectedValue(new Error('Register failed'))
      
      const result = await authStore.register(mockRegisterForm)
      
      expect(result).toBe(false)
    })
  })

  describe('登出功能', () => {
    it('应该清除所有认证信息', () => {
      // 先设置一些认证信息
      authStore.token = 'test-token'
      authStore.user = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
        created_at: '2023-01-01T00:00:00Z'
      }
      
      authStore.logout()
      
      expect(authStore.token).toBeNull()
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(httpService.clearToken).toHaveBeenCalled()
    })
  })

  describe('获取当前用户', () => {
    const mockUser: User = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z'
    }

    it('应该成功获取用户信息', async () => {
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)
      
      await authStore.getCurrentUser()
      
      expect(authStore.user).toEqual(mockUser)
    })

    it('应该在获取用户信息失败时清除认证状态', async () => {
      vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error('Unauthorized'))
      
      // 先设置一些认证信息
      authStore.token = 'test-token'
      
      await authStore.getCurrentUser()
      
      expect(authStore.token).toBeNull()
      expect(authStore.user).toBeNull()
      expect(httpService.clearToken).toHaveBeenCalled()
    })
  })

  describe('认证状态管理', () => {
    it('应该正确设置认证token', () => {
      const testToken = 'test-access-token'
      const testRefreshToken = 'test-refresh-token'
      
      authStore.setAuthToken(testToken, testRefreshToken)
      
      expect(authStore.token).toBe(testToken)
      expect(httpService.setToken).toHaveBeenCalledWith(testToken)
      expect(httpService.setRefreshToken).toHaveBeenCalledWith(testRefreshToken)
    })

    it('应该正确清除认证信息', () => {
      // 先设置认证信息
      authStore.token = 'test-token'
      authStore.user = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
        created_at: '2023-01-01T00:00:00Z'
      }
      
      authStore.clearAuth()
      
      expect(authStore.token).toBeNull()
      expect(authStore.user).toBeNull()
      expect(httpService.clearToken).toHaveBeenCalled()
    })
  })
})