/**
 * HTTP客户端服务
 * 提供统一的API请求管理，包括认证、错误处理和令牌刷新
 */
import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage, type MessageParamsWithType } from 'element-plus'
import router from '../router'
import { useAuthStore } from '@/stores/auth'

// 响应数据类型
interface ApiResponse<T = unknown> {
  data: T
  message?: string
  code?: number
}

// 错误响应类型
interface ApiError {
  detail: string
  code?: number
}

class HttpService {
  private axiosInstance: AxiosInstance
  private isRefreshing = false
  private failedQueue: Array<{
    resolve: (value: string) => void
    reject: (error: unknown) => void
  }> = []

  constructor() {
    // 创建axios实例
    this.axiosInstance = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:18000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  /**
   * 设置请求和响应拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = this.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.axiosInstance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response
      },
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

        // 处理401未授权错误
        if (error.response?.status === 401 && !originalRequest._retry) {
          // 如果是登录接口的401错误，直接返回错误，不进行token刷新
          if (originalRequest.url?.includes('/auth/login')) {
            return Promise.reject(error)
          }

          if (this.isRefreshing) {
            // 如果正在刷新令牌，将请求加入队列
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject })
            }).then((token) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`
              }
              return this.axiosInstance(originalRequest)
            }).catch((err) => {
              return Promise.reject(err)
            })
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            const newToken = await this.refreshToken()
            this.processQueue(null, newToken)
            
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
            }
            return this.axiosInstance(originalRequest)
          } catch (refreshError) {
            this.processQueue(refreshError, null)
            this.handleAuthError()
            return Promise.reject(refreshError)
          } finally {
            this.isRefreshing = false
          }
        }

        // 处理其他错误
        this.handleError(error)
        return Promise.reject(error)
      }
    )
  }

  /**
   * 处理队列中的请求
   */
  private processQueue(error: unknown, token: string | null): void {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error)
      } else if (token) {
        resolve(token)
      }
    })
    
    this.failedQueue = []
  }

  /**
   * 获取存储的令牌
   */
  private getToken(): string | null {
    return localStorage.getItem('token')
  }

  /**
   * 获取存储的刷新令牌
   */
  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token')
  }

  /**
   * 设置令牌
   */
  public setToken(token: string): void {
    localStorage.setItem('token', token)
  }

  /**
   * 设置刷新令牌
   */
  public setRefreshToken(refreshToken: string): void {
    localStorage.setItem('refresh_token', refreshToken)
  }

  /**
   * 清除令牌
   */
  public clearToken(): void {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
  }

  /**
   * 刷新令牌
   */
  private async refreshToken(): Promise<string> {
    try {
      const refreshToken = this.getRefreshToken()
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await this.axiosInstance.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      })
      const { access_token, refresh_token: newRefreshToken } = response.data
      this.setToken(access_token)
      this.setRefreshToken(newRefreshToken)
      return access_token
    } catch (error) {
      this.clearToken()
      throw error
    }
  }

  /**
   * 处理认证错误
   */
  private handleAuthError(): void {
    this.clearToken()
    const authStore = useAuthStore()
    authStore.logout()
    ElMessage.error('登录已过期，请重新登录' as MessageParamsWithType)
    router.push('/login')
  }

  /**
   * 处理通用错误
   */
  private handleError(error: AxiosError<ApiError>): void {
    const message = error.response?.data?.detail || error.message || '请求失败'
    
    // 根据状态码显示不同的错误信息
    switch (error.response?.status) {
      case 400:
        ElMessage.error(`请求错误: ${message}` as MessageParamsWithType)
        break
      case 403:
        ElMessage.error('权限不足' as MessageParamsWithType)
        break
      case 404:
        ElMessage.error('请求的资源不存在' as MessageParamsWithType)
        break
      case 500:
        ElMessage.error('服务器内部错误' as MessageParamsWithType)
        break
      default:
        if (error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK') {
          ElMessage.error('网络连接失败，请检查网络设置' as MessageParamsWithType)
        } else {
          ElMessage.error(message as MessageParamsWithType)
        }
    }
  }

  /**
   * GET请求
   */
  public async get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.get<ApiResponse<T>>(url, config)
    return response.data
  }

  /**
   * POST请求
   */
  public async post<T = unknown>(
    url: string, 
    data?: unknown, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.post<ApiResponse<T>>(url, data, config)
    return response.data
  }

  /**
   * PUT请求
   */
  public async put<T = unknown>(
    url: string, 
    data?: unknown, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.put<ApiResponse<T>>(url, data, config)
    return response.data
  }

  /**
   * DELETE请求
   */
  public async delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.delete<ApiResponse<T>>(url, config)
    return response.data
  }

  /**
   * 上传文件
   */
  public async upload<T = unknown>(
    url: string, 
    formData: FormData, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.axiosInstance.post<ApiResponse<T>>(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers
      }
    })
    return response.data
  }

  /**
   * 获取原始axios实例（用于特殊情况）
   */
  public getInstance(): AxiosInstance {
    return this.axiosInstance
  }
}

// 导出单例实例
export const httpService = new HttpService()
export default httpService