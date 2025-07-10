import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const accessKey = ref<string>('')
  const isAuthenticated = ref<boolean>(false)
  const clientInfo = ref<any>({})
  const requiresKey = ref<boolean>(false)

  // 计算属性
  const hasAdminAccess = computed(() => {
    return isAuthenticated.value && accessKey.value
  })

  // 检查认证状态
  const checkAuthStatus = async () => {
    try {
      const response = await authApi.getStatus()
      requiresKey.value = response.requires_key
      isAuthenticated.value = response.authenticated
      clientInfo.value = response.client_info

      // 如果需要密钥但未认证，从localStorage恢复
      if (requiresKey.value && !isAuthenticated.value) {
        const storedKey = localStorage.getItem('access_key')
        if (storedKey) {
          await verifyAccessKey(storedKey)
        }
      }
    } catch (error) {
      console.error('检查认证状态失败:', error)
    }
  }

  // 验证访问密钥
  const verifyAccessKey = async (key: string) => {
    try {
      const response = await authApi.verify(key)
      
      if (response.valid) {
        accessKey.value = key
        isAuthenticated.value = true
        clientInfo.value = response.client_info
        
        // 保存到localStorage
        localStorage.setItem('access_key', key)
        ElMessage.success('访问密钥验证成功')
        
        return true
      } else {
        ElMessage.error('访问密钥无效')
        logout()
        return false
      }
    } catch (error) {
      console.error('验证访问密钥失败:', error)
      ElMessage.error('验证失败，请检查网络连接')
      return false
    }
  }

  // 登出
  const logout = () => {
    accessKey.value = ''
    isAuthenticated.value = false
    clientInfo.value = {}
    localStorage.removeItem('access_key')
  }

  // 获取访问密钥（用于API请求）
  const getAccessKey = () => {
    return accessKey.value || localStorage.getItem('access_key') || ''
  }

  return {
    // 状态
    accessKey,
    isAuthenticated,
    clientInfo,
    requiresKey,
    
    // 计算属性
    hasAdminAccess,
    
    // 方法
    checkAuthStatus,
    verifyAccessKey,
    logout,
    getAccessKey
  }
}) 