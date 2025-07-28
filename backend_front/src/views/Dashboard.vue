<template>
  <div class="dashboard-page">
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="menu-toggle" @click="toggleSidebar">
            <Menu />
          </el-icon>
          <h2>AI学习系统管理后台</h2>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="el-dropdown-link">
              {{ user?.username }}
              <el-icon class="el-icon--right">
                <ArrowDown />
              </el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-container>
        <el-aside :width="sidebarWidth" class="sidebar">
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            :collapse="isCollapsed"
            @select="handleMenuSelect"
          >
            <el-menu-item index="/">
              <el-icon><House /></el-icon>
              <template #title>首页</template>
            </el-menu-item>
            <el-menu-item index="/subjects">
              <el-icon><Collection /></el-icon>
              <template #title>学科管理</template>
            </el-menu-item>
            <el-menu-item index="/questions">
              <el-icon><Document /></el-icon>
              <template #title>题目管理</template>
            </el-menu-item>
            <el-menu-item index="/question-banks">
              <el-icon><Folder /></el-icon>
              <template #title>题库管理</template>
            </el-menu-item>
            <el-menu-item index="/comprehensive-question-banks">
              <el-icon><DataAnalysis /></el-icon>
              <template #title>综合题库管理</template>
            </el-menu-item>
            <el-menu-item index="/ai-chat">
              <el-icon><ChatDotRound /></el-icon>
              <template #title>AI对话</template>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  ArrowDown,
  Menu,
  House,
  Collection,
  Document,
  Folder,
  DataAnalysis,
  ChatDotRound
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { logout } = authStore

const user = computed(() => authStore.user)
const isCollapsed = ref(false)
const activeMenu = ref(route.path)

// 计算侧边栏宽度
const sidebarWidth = computed(() => isCollapsed.value ? '64px' : '200px')

// 切换侧边栏
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

// 处理菜单选择
const handleMenuSelect = (index: string) => {
  router.push(index)
}

// 监听路由变化，更新活跃菜单
watch(
  () => route.path,
  (newPath) => {
    activeMenu.value = newPath
  },
  { immediate: true }
)

const handleCommand = (command: string) => {
  if (command === 'logout') {
    logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.dashboard-page {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.el-container {
  height: 100%;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px !important;
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h2 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.menu-toggle {
  font-size: 20px;
  cursor: pointer;
  color: #666;
  transition: color 0.3s;
}

.menu-toggle:hover {
  color: #409eff;
}

.header-right {
  color: #666;
}

.el-dropdown-link {
  cursor: pointer;
  color: #409eff;
  display: flex;
  align-items: center;
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e6e6e6;
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-menu {
  border-right: none;
  height: 100%;
}

.sidebar-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
  margin: 4px 8px;
  border-radius: 6px;
  transition: all 0.3s;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #f0f9ff;
  color: #409eff;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #409eff;
  color: #fff;
}

.sidebar-menu .el-menu-item.is-active .el-icon {
  color: #fff;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-left h2 {
    display: none;
  }
  
  .sidebar {
    position: fixed;
    left: 0;
    top: 60px;
    height: calc(100vh - 60px);
    z-index: 999;
    box-shadow: 2px 0 6px rgba(0, 0, 0, 0.1);
  }
  
  .main-content {
    margin-left: 0;
  }
}
</style>