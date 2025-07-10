/**
 * 测试工具函数
 */

import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import { Component } from 'vue'

// 创建测试路由器
export function createTestRouter(routes: any[] = []) {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
      { path: '/test', name: 'test', component: { template: '<div>Test</div>' } },
      ...routes
    ]
  })
}

// 创建测试store
export function createTestPinia() {
  return createPinia()
}

// 组件挂载工具
export function mountComponent(component: Component, options: any = {}) {
  const router = createTestRouter()
  const pinia = createTestPinia()
  
  return mount(component, {
    global: {
      plugins: [router, pinia],
      stubs: {
        'router-link': true,
        'router-view': true,
        ...options.stubs
      }
    },
    ...options
  })
}

// 等待异步操作
export function waitFor(ms: number = 0) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// 模拟API响应
export function mockApiResponse(data: any, delay: number = 0) {
  return new Promise(resolve => {
    setTimeout(() => resolve({ data }), delay)
  })
}

// 模拟API错误
export function mockApiError(error: any, delay: number = 0) {
  return new Promise((_, reject) => {
    setTimeout(() => reject(error), delay)
  })
}

// 获取组件文本内容
export function getComponentText(wrapper: VueWrapper<any>) {
  return wrapper.text().replace(/\s+/g, ' ').trim()
}

// 触发组件事件
export async function triggerEvent(wrapper: VueWrapper<any>, selector: string, event: string) {
  const element = wrapper.find(selector)
  await element.trigger(event)
  await wrapper.vm.$nextTick()
}

// 模拟用户输入
export async function userInput(wrapper: VueWrapper<any>, selector: string, value: string) {
  const input = wrapper.find(selector)
  await input.setValue(value)
  await wrapper.vm.$nextTick()
}

// 检查元素是否存在
export function hasElement(wrapper: VueWrapper<any>, selector: string) {
  return wrapper.find(selector).exists()
}

// 检查元素是否可见
export function isElementVisible(wrapper: VueWrapper<any>, selector: string) {
  const element = wrapper.find(selector)
  return element.exists() && element.isVisible()
} 