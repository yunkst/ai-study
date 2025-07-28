import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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
      path: '/',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Home',
          component: () => import('../views/Home.vue')
        },
        {
          path: 'subjects',
          name: 'Subjects',
          component: () => import('../views/Subjects.vue')
        },
        {
          path: 'questions',
          name: 'Questions',
          component: () => import('../views/Questions.vue')
        },
        {
          path: 'question-banks',
          name: 'QuestionBanks',
          component: () => import('../views/QuestionBanks.vue')
        },
        {
          path: 'comprehensive-question-banks',
          name: 'ComprehensiveQuestionBanks',
          component: () => import('../views/ComprehensiveQuestionBanks.vue')
        },
        {
          path: 'ai-chat',
          name: 'AIChat',
          component: () => import('../views/AIChat.vue')
        }
      ]
    },
    {
      path: '/dashboard',
      redirect: '/'
    },
    {
      path: '/subject/:subjectId',
      name: 'SubjectDetail',
      component: () => import('../views/SubjectDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/subject/:subjectId/question-banks',
      name: 'SubjectQuestionBanks',
      component: () => import('../views/SubjectQuestionBanks.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/subject/:subjectId/question-banks/:questionBankId/questions',
      name: 'QuestionBankQuestions',
      component: () => import('../views/Questions.vue'),
      meta: { requiresAuth: true }
    }
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