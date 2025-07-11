<template>
  <el-container class="home-container">
    <el-aside :width="state.isMenuCollapsed ? '64px' : '200px'" class="aside">
      <div class="logo">
        <!-- 使用图标替代缺失的Logo图片 -->
        <el-icon><House /></el-icon>
        <span v-if="!state.isMenuCollapsed">AI Tutor</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        :collapse="state.isMenuCollapsed"
        @select="handleMenuSelect"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item v-for="item in state.menuItems" :key="item.name" :index="item.route">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button @click="state.isMenuCollapsed = !state.isMenuCollapsed" :icon="state.isMenuCollapsed ? 'Expand' : 'Fold'" text />
          <span>{{ $route.meta.title || '首页' }}</span>
        </div>
        <div class="header-right">
          <div class="user-info">
            <el-dropdown>
              <span class="el-dropdown-link">
                {{ state.user.username }}
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>个人中心</el-dropdown-item>
                  <el-dropdown-item divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  House,
  Edit,
  DataLine,
  Setting,
  Collection,
  Tickets,
  ArrowDown,
  Fold,
  Expand,
  Microphone,
  PieChart
} from '@element-plus/icons-vue'

const router = useRouter()

const state = reactive({
  isMenuCollapsed: false,
  menuItems: [
    { name: 'home', title: '首页', icon: House, route: '/' },
    { name: 'practice', title: '练习', icon: Edit, route: '/practice' },
    { name: 'podcast', title: '播客', icon: Microphone, route: '/podcast' },
    { name: 'analytics', title: '分析', icon: PieChart, route: '/analytics' },
    { name: 'knowledge', title: '知识库', icon: Collection, route: '/knowledge' },
    { name: 'admin', title: '管理', icon: Setting, route: '/admin' }
  ],
  user: {
    username: 'admin',
    role: '管理员'
  },
})

const activeMenu = computed(() => {
  return router.currentRoute.value.path
})

const handleMenuSelect = (index: string) => {
  router.push(index)
}
</script>

<style scoped>
.home-container {
  height: 100vh;
  background-color: #f0f2f5;
}

.aside {
  background-color: #304156;
  transition: width 0.28s;
  overflow-x: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: 600;
}

.logo img {
  width: 32px;
  height: 32px;
  margin-right: 12px;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 200px;
  min-height: 400px;
}
.el-menu {
  border-right: none;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.user-info {
  cursor: pointer;
}

.main-content {
  padding: 20px;
}
</style> 