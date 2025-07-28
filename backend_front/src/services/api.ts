/**
 * API服务层
 * 统一管理所有API调用
 */
import httpService from './http'

// 用户相关接口
export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  username: string
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// 学科相关接口
export interface Subject {
  id: number
  name: string
  description?: string
  created_at: string
}

// 题库相关接口
export interface QuestionBank {
  id: number
  name: string
  description?: string
  subject_id: number
  created_at: string
  updated_at: string
}

export interface CreateQuestionBankForm {
  name: string
  description?: string
  subject_id: number
}

// 题目相关接口
export interface Question {
  id: number
  title: string
  content: string
  question_type: string
  options: string[]
  correct_answer: string
  explanation: string
  difficulty: string
  tags: string
  subject_id: number
  question_bank_id?: number
  subject: Subject
  created_at: string
}

export interface CreateQuestionForm {
  title: string
  content: string
  question_type: 'single_choice' | 'multiple_choice' | 'true_false' | 'fill_blank' | 'essay'
  options?: string[]
  correct_answer: string
  explanation?: string
  difficulty: 'easy' | 'medium' | 'hard'
  subject_id: number
  question_bank_id?: number
}

/**
 * 认证相关API
 */
export const authApi = {
  /**
   * 用户登录
   */
  async login(loginForm: LoginForm): Promise<LoginResponse> {
    const formData = new FormData()
    formData.append('username', loginForm.username)
    formData.append('password', loginForm.password)

    const response = await httpService.getInstance().post<LoginResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    return response.data
  },

  /**
   * 用户注册
   */
  async register(registerForm: RegisterForm): Promise<void> {
    await httpService.post('/api/v1/auth/register', registerForm)
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    const response = await httpService.get<User>('/api/v1/auth/me')
    return response.data || response as unknown as User
  },

  /**
   * 刷新令牌
   */
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const response = await httpService.post<LoginResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    })
    return response.data || response as unknown as LoginResponse
  }
}

/**
 * 学科相关API
 */
export const subjectApi = {
  /**
   * 获取所有学科
   */
  async getSubjects(): Promise<Subject[]> {
    const response = await httpService.get<Subject[]>('/api/v1/questions/subjects')
    return response.data || response as unknown as Subject[]
  },

  /**
   * 根据ID获取学科
   */
  async getSubject(id: number): Promise<Subject> {
    const response = await httpService.get<Subject>(`/api/v1/questions/subjects/${id}`)
    return response.data || response as unknown as Subject
  },

  /**
   * 创建学科
   */
  async createSubject(data: { name: string; description?: string }): Promise<Subject> {
    const response = await httpService.post<Subject>('/api/v1/questions/subjects', data)
    return response.data || response as unknown as Subject
  },

  /**
   * 更新学科
   */
  async updateSubject(id: number, data: { name: string; description?: string }): Promise<Subject> {
    const response = await httpService.put<Subject>(`/api/v1/questions/subjects/${id}`, data)
    return response.data || response as unknown as Subject
  },

  /**
   * 删除学科
   */
  async deleteSubject(id: number): Promise<void> {
    await httpService.delete(`/api/v1/questions/subjects/${id}`)
  }
}

/**
 * 题库相关API
 */
export const questionBankApi = {
  /**
   * 获取题库列表
   */
  async getQuestionBanks(subjectId?: number): Promise<QuestionBank[]> {
    const params = subjectId ? `?subject_id=${subjectId}` : ''
    const response = await httpService.get<QuestionBank[]>(`/api/v1/question-banks/${params}`)
    return response.data || response as unknown as QuestionBank[]
  },

  /**
   * 根据ID获取题库
   */
  async getQuestionBank(id: number): Promise<QuestionBank> {
    const response = await httpService.get<QuestionBank>(`/api/v1/question-banks/${id}`)
    return response.data || response as unknown as QuestionBank
  },

  /**
   * 创建题库
   */
  async createQuestionBank(questionBank: CreateQuestionBankForm): Promise<QuestionBank> {
    const response = await httpService.post<QuestionBank>('/api/v1/question-banks/', questionBank)
    return response.data || response as unknown as QuestionBank
  },

  /**
   * 更新题库
   */
  async updateQuestionBank(id: number, questionBank: Partial<CreateQuestionBankForm>): Promise<QuestionBank> {
    const response = await httpService.put<QuestionBank>(`/api/v1/question-banks/${id}`, questionBank)
    return response.data || response as unknown as QuestionBank
  },

  /**
   * 删除题库
   */
  async deleteQuestionBank(id: number): Promise<void> {
    await httpService.delete(`/api/v1/question-banks/${id}`)
  }
}

/**
 * 题目相关API
 */
export const questionApi = {
  /**
   * 获取题目列表
   */
  async getQuestions(params?: {
    page?: number
    size?: number
    subject_id?: string
    question_bank_id?: string
    question_type?: string
  }): Promise<{ items: Question[]; total: number }> {
    const response = await httpService.get<{ items: Question[]; total: number }>('/api/v1/questions/', { params })
    return response.data || response as unknown as { items: Question[]; total: number }
  },

  /**
   * 根据ID获取题目
   */
  async getQuestion(id: number): Promise<Question> {
    const response = await httpService.get<Question>(`/api/v1/questions/${id}`)
    return response.data || response as unknown as Question
  },

  /**
   * 创建题目
   */
  async createQuestion(data: {
    subject_id: string
    title: string
    content: string
    question_type: string
    options?: string[]
    correct_answer: string
    explanation?: string
    difficulty: string
    tags?: string
  }): Promise<Question> {
    const response = await httpService.post<Question>('/api/v1/questions/', data)
    return response.data || response as unknown as Question
  },

  /**
   * 更新题目
   */
  async updateQuestion(id: number, data: {
    subject_id?: string
    title?: string
    content?: string
    question_type?: string
    options?: string[]
    correct_answer?: string
    explanation?: string
    difficulty?: string
    tags?: string
  }): Promise<Question> {
    const response = await httpService.put<Question>(`/api/v1/questions/${id}`, data)
    return response.data || response as unknown as Question
  },

  /**
   * 删除题目
   */
  async deleteQuestion(id: number): Promise<void> {
    await httpService.delete(`/api/v1/questions/${id}`)
  }
}

// 导出所有API
export default {
  auth: authApi,
  subject: subjectApi,
  questionBank: questionBankApi,
  question: questionApi
}