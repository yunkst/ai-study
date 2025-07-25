<template>
  <div class="dashboard">
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h2>AI学习系统管理后台</h2>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="el-dropdown-link">
              {{ user?.username }}
              <el-icon class="el-icon--right">
                <arrow-down />
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
        <el-aside width="200px" class="sidebar">
          <el-menu
            :default-active="$route.path"
            router
            class="el-menu-vertical"
          >
            <el-menu-item index="/dashboard">
              <el-icon><house /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/subjects">
              <el-icon><collection /></el-icon>
              <span>学科管理</span>
            </el-menu-item>
            <el-menu-item index="/questions">
              <el-icon><document /></el-icon>
              <span>题目管理</span>
            </el-menu-item>
            <el-menu-item index="/question-banks">
              <el-icon><upload /></el-icon>
              <span>题库管理</span>
            </el-menu-item>
            <el-menu-item index="/ai-chat">
              <el-icon><chat-line-round /></el-icon>
              <span>AI对话</span>
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  ArrowDown,
  House,
  Collection,
  Document,
  Upload,
  ChatLineRound
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const { logout } = authStore

const user = computed(() => authStore.user)

const handleCommand = (command: string) => {
  if (command === 'logout') {
    logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.dashboard {
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
}

.header-left h2 {
  margin: 0;
  color: #333;
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
  background: #f5f5f5;
  border-right: 1px solid #e6e6e6;
  height: calc(100vh - 60px);
}

.el-menu-vertical {
  border-right: none;
  height: 100%;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}
</style>