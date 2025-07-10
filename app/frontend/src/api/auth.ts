import { api } from './index'

export interface AuthResponse {
  valid: boolean
  message: string
  client_info: {
    ip: string
    user_agent: string
    device_type: string
  }
}

export interface AuthStatusResponse {
  authenticated: boolean
  requires_key: boolean
  client_info: {
    ip: string
    user_agent: string
    device_type: string
  }
}

export const authApi = {
  // 验证访问密钥
  verify: (accessKey: string): Promise<AuthResponse> => {
    return api.post('/auth/verify', { access_key: accessKey })
  },

  // 获取认证状态
  getStatus: (): Promise<AuthStatusResponse> => {
    return api.get('/auth/status')
  }
} 