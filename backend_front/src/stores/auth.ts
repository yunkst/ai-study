import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
}

interface LoginForm {
  username: string
  password: string
}

interface RegisterForm {
  username: string
  email: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  // 设置axios默认headers
  const setAuthHeader = (authToken: string) => {
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
    localStorage.setItem('token', authToken)
    token.value = authToken
  }

  // 清除认证信息
  const clearAuth = () => {
    delete axios.defaults.headers.common['Authorization']
    localStorage.removeItem('token')
    token.value = null
    user.value = null
  }

  // 登录
  const login = async (loginForm: LoginForm) => {
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('username', loginForm.username)
      formData.append('password', loginForm.password)

      const response = await axios.post('/api/v1/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })

      const { access_token } = response.data
      setAuthHeader(access_token)
      
      // 获取用户信息
      await getCurrentUser()
      
      ElMessage.success('登录成功')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '登录失败')
      return false
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (registerForm: RegisterForm) => {
    loading.value = true
    try {
      await axios.post('/api/v1/auth/register', registerForm)
      ElMessage.success('注册成功，请登录')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '注册失败')
      return false
    } finally {
      loading.value = false
    }
  }

  // 获取当前用户信息
  const getCurrentUser = async () => {
    try {
      const response = await axios.get('/api/v1/auth/me')
      user.value = response.data
    } catch (error) {
      clearAuth()
    }
  }

  // 登出
  const logout = () => {
    clearAuth()
    ElMessage.success('已退出登录')
  }

  // 初始化时设置token
  if (token.value) {
    setAuthHeader(token.value)
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
    getCurrentUser
  }
})