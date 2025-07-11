import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/practice',
    name: 'Practice',
    component: () => import('../views/Practice.vue')
  },
  {
    path: '/podcast',
    name: 'Podcast',
    component: () => import('../views/Podcast.vue')
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('../views/Analytics.vue')
  },
  {
    path: '/knowledge',
    name: 'KnowledgeManagement',
    component: () => import('../views/KnowledgeManagement.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 