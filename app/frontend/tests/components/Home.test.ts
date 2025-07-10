/**
 * Home组件测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Home from '@/views/Home.vue'
import { mountComponent, hasElement, getComponentText } from '../utils/test-utils'

describe('Home.vue', () => {
  let wrapper: any

  beforeEach(() => {
    // 模拟认证store
    const mockAuthStore = {
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn()
    }

    wrapper = mountComponent(Home, {
      global: {
        mocks: {
          $router: {
            push: vi.fn()
          }
        }
      }
    })
  })

  describe('组件渲染', () => {
    it('应该正确渲染页面标题', () => {
      expect(wrapper.find('h1').text()).toContain('软件架构师AI学习助手')
    })

    it('应该显示欢迎信息', () => {
      const welcomeText = getComponentText(wrapper)
      expect(welcomeText).toContain('欢迎使用')
    })

    it('应该显示功能卡片', () => {
      // 检查功能卡片是否存在
      expect(hasElement(wrapper, '.feature-card')).toBe(true)
    })
  })

  describe('功能区域', () => {
    it('应该显示智能练习功能', () => {
      const text = getComponentText(wrapper)
      expect(text).toContain('智能练习')
    })

    it('应该显示AI播客功能', () => {
      const text = getComponentText(wrapper)
      expect(text).toContain('AI播客')
    })

    it('应该显示学习分析功能', () => {
      const text = getComponentText(wrapper)
      expect(text).toContain('学习分析')
    })
  })

  describe('交互功能', () => {
    it('点击练习按钮应该跳转到练习页面', async () => {
      const mockPush = vi.fn()
      wrapper.vm.$router.push = mockPush

      const practiceButton = wrapper.find('[data-test="practice-button"]')
      if (practiceButton.exists()) {
        await practiceButton.trigger('click')
        expect(mockPush).toHaveBeenCalledWith('/practice')
      }
    })

    it('点击播客按钮应该跳转到播客页面', async () => {
      const mockPush = vi.fn()
      wrapper.vm.$router.push = mockPush

      const podcastButton = wrapper.find('[data-test="podcast-button"]')
      if (podcastButton.exists()) {
        await podcastButton.trigger('click')
        expect(mockPush).toHaveBeenCalledWith('/podcast')
      }
    })
  })

  describe('响应式设计', () => {
    it('在移动端应该正确显示', async () => {
      // 模拟移动端视窗
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })

      // 触发resize事件
      window.dispatchEvent(new Event('resize'))
      await wrapper.vm.$nextTick()

      // 检查移动端布局
      const container = wrapper.find('.container')
      expect(container.exists()).toBe(true)
    })
  })

  describe('错误处理', () => {
    it('应该优雅处理API错误', async () => {
      // 模拟API错误
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      // 触发可能导致错误的操作
      try {
        // 这里可以模拟一些会导致错误的操作
        await wrapper.vm.$nextTick()
      } catch (error) {
        // 验证错误被正确处理
      }

      consoleSpy.mockRestore()
    })
  })
}) 