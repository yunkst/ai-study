import { createRouter, createWebHistory, RouteRecordRaw, RouteLocationNormalized } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/views/Home.vue'),
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { 
          title: '首页'
        }
      },
      {
        path: 'practice',
        name: 'Practice',
        component: () => import('@/views/Practice.vue'),
        meta: { 
          title: '智能练习'
        }
      },
      {
        path: 'podcast',
        name: 'Podcast',
        component: () => import('@/views/Podcast.vue'),
        meta: { 
          title: 'AI播客'
        }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue'),
        meta: { 
          title: '学习分析'
        }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/KnowledgeManagement.vue'),
        meta: {
            title: '知识库'
        }
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/Admin.vue'),
        meta: { 
          title: '系统管理'
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { 
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to: RouteLocationNormalized, from: RouteLocationNormalized, savedPosition: any) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

export default router 