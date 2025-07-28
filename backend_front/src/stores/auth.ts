import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage, type MessageParamsWithType } from 'element-plus'
import { authApi, type User, type LoginForm, type RegisterForm } from '../services/api'
import httpService from '../services/http'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  // 设置认证令牌
  const setAuthToken = (authToken: string, refreshToken?: string) => {
    httpService.setToken(authToken)
    if (refreshToken) {
      httpService.setRefreshToken(refreshToken)
    }
    token.value = authToken
  }

  // 清除认证信息
  const clearAuth = () => {
    httpService.clearToken()
    token.value = null
    user.value = null
  }

  // 登录
  const login = async (loginForm: LoginForm) => {
    loading.value = true
    try {
      const response = await authApi.login(loginForm)
      const { access_token, refresh_token } = response
      setAuthToken(access_token, refresh_token)
      
      // 获取用户信息
      await getCurrentUser()
      
      ElMessage.success('登录成功' as MessageParamsWithType)
      return true
    } catch (error: unknown) {
      // 针对登录接口的特定错误处理
      if (error && typeof error === 'object' && 'response' in error) {
        const httpError = error as { response?: { status?: number; data?: { detail?: string } } }
        if (httpError.response?.status === 401) {
          const errorMessage = httpError.response?.data?.detail || '用户名或密码错误'
          ElMessage.error(errorMessage as MessageParamsWithType)
        }
      }
      // 其他错误已在HTTP服务中统一处理
      return false
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (registerForm: RegisterForm) => {
    loading.value = true
    try {
      await authApi.register(registerForm)
      ElMessage.success('注册成功，请登录' as MessageParamsWithType)
      return true
    } catch {
      // 错误处理已在HTTP服务中统一处理
      return false
    } finally {
      loading.value = false
    }
  }

  // 获取当前用户信息
  const getCurrentUser = async () => {
    try {
      const userData = await authApi.getCurrentUser()
      user.value = userData
    } catch {
      clearAuth()
    }
  }

  // 登出
  const logout = () => {
    clearAuth()
    ElMessage.success('已退出登录' as MessageParamsWithType)
  }

  // 初始化时设置token
  if (token.value) {
    setAuthToken(token.value)
    getCurrentUser()
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    getCurrentUser,
    setAuthToken,
    clearAuth
  }
})