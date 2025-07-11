<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <div class="admin-sidebar">
      <div class="sidebar-header">
        <h2>系统管理</h2>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        @select="handleMenuSelect"
        background-color="#2c3e50"
        text-color="#ecf0f1"
        active-text-color="#3498db"
      >
        <el-menu-item index="ai-config">
          <el-icon><Setting /></el-icon>
          <span>AI 配置</span>
        </el-menu-item>
        
        <el-menu-item index="logs">
          <el-icon><Document /></el-icon>
          <span>系统日志</span>
        </el-menu-item>
        
        <el-menu-item index="tasks">
          <el-icon><Timer /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <el-button @click="$router.push('/')" type="info" size="small">
          <el-icon><ArrowLeft /></el-icon>
          返回首页
        </el-button>
      </div>
    </div>
    
    <!-- 主内容区域 -->
    <div class="admin-main">
      <!-- 头部 -->
      <div class="admin-header">
        <h1>{{ currentPageTitle }}</h1>
        <div class="header-actions">
          <el-button @click="refreshPage" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
      
      <!-- 内容区域 -->
      <div class="admin-content">
        <!-- AI配置 -->
        <AIConfig v-if="activeMenu === 'ai-config'" />

        <!-- 任务管理 -->
        <Tasks v-else-if="activeMenu === 'tasks'" />

        <!-- 系统日志 -->
        <SystemLogs v-else-if="activeMenu === 'logs'" />

        <!-- 未知页面占位 -->
        <div v-else class="placeholder">
          <el-icon size="64"><Setting /></el-icon>
          <h3>{{ currentPageTitle }}</h3>
          <p>请选择左侧菜单功能。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  Setting, 
  Document, 
  Timer, 
  ArrowLeft, 
  Refresh
} from '@element-plus/icons-vue'
import AIConfig from './admin/AIConfig.vue'
import Tasks from './admin/Tasks.vue'
import SystemLogs from './admin/SystemLogs.vue'

// 当前激活的菜单
const activeMenu = ref('ai-config')

// 页面标题映射
const pageTitles = {
  'ai-config': 'AI 配置管理',
  'logs': '系统日志',
  'tasks': '任务管理'
}

// 计算当前页面标题
const currentPageTitle = computed(() => {
  return pageTitles[activeMenu.value as keyof typeof pageTitles] || '管理页面'
})

// 处理菜单选择
const handleMenuSelect = (key: string) => {
  activeMenu.value = key
}

// 刷新页面
const refreshPage = () => {
  // 这里可以添加刷新当前页面数据的逻辑
  location.reload()
}
</script>

<style lang="scss" scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}

.admin-sidebar {
  width: 200px;
  background: #2c3e50;
  display: flex;
  flex-direction: column;
  
  .sidebar-header {
    padding: 20px;
    border-bottom: 1px solid #34495e;
    
    h2 {
      color: #ecf0f1;
      margin: 0;
      font-size: 18px;
    }
  }
  
  .el-menu {
    border: none;
    flex: 1;
  }
  
  .sidebar-footer {
    padding: 20px;
    border-top: 1px solid #34495e;
  }
}

.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.admin-header {
  background: white;
  padding: 16px 24px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  h1 {
    margin: 0;
    font-size: 24px;
    color: #303133;
  }
}

.admin-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.dashboard {
  .stat-item {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: #303133;
    }
    
    .stat-label {
      font-size: 14px;
      color: #909399;
    }
  }
}

.placeholder {
  text-align: center;
  padding: 60px 20px;
  
  .el-icon {
    color: #c0c4cc;
    margin-bottom: 16px;
  }
  
  h3 {
    color: #303133;
    margin-bottom: 8px;
  }
  
  p {
    color: #909399;
    margin: 0;
  }
}
</style> 