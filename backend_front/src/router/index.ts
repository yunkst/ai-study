import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue')
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/Register.vue')
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/subjects',
      name: 'Subjects',
      component: () => import('../views/Subjects.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/questions',
      name: 'Questions',
      component: () => import('../views/Questions.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/question-banks',
      name: 'QuestionBanks',
      component: () => import('../views/QuestionBanks.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/ai-chat',
      name: 'AIChat',
      component: () => import('../views/AIChat.vue'),
      meta: { requiresAuth: true }
    },
    
  ]
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router