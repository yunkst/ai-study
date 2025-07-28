import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './style.css'
import App from './App.vue'
import router from './router'

// 启用Vue DevTools
if (import.meta.env.DEV) {
  // @ts-expect-error - Vue DevTools global hook type definition
  window.__VUE_DEVTOOLS_GLOBAL_HOOK__ = window.__VUE_DEVTOOLS_GLOBAL_HOOK__ || {
    Vue: null,
    emit: function(event: string, ...args: unknown[]) {
      console.debug('DevTools emit:', event, args)
    },
    on: function(event: string) {
      console.debug('DevTools on:', event)
    },
    once: function(event: string) {
      console.debug('DevTools once:', event)
    },
    off: function(event: string) {
      console.debug('DevTools off:', event)
    },
    apps: [],
    enabled: true
  }
}

const app = createApp(App)
const pinia = createPinia()

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(ElementPlus)
app.use(router)

// 认证状态由HTTP服务自动管理

app.mount('#app')
