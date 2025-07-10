<template>
  <div class="home-container">
    <!-- 移动端导航栏 -->
    <div class="mobile-nav" v-if="isMobile">
      <h1 class="app-title">AI学习助手</h1>
      <el-button 
        v-if="authStore.requiresKey && !authStore.isAuthenticated"
        type="primary" 
        size="small"
        @click="$router.push('/auth')"
      >
        验证访问
      </el-button>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <h1 v-if="!isMobile" class="welcome-title">软件架构师AI学习助手</h1>
        <p class="welcome-subtitle">AI驱动的个性化学习，让你的架构师之路更高效</p>
        
        <!-- 认证提示 -->
        <div v-if="authStore.requiresKey && !authStore.isAuthenticated" class="auth-notice">
          <el-alert
            title="需要访问密钥"
            description="请输入访问密钥以使用完整功能"
            type="warning"
            show-icon
            :closable="false"
          >
            <template #default>
              <el-button type="primary" @click="$router.push('/auth')">
                立即验证
              </el-button>
            </template>
          </el-alert>
        </div>
      </div>

      <!-- 功能卡片区域 -->
      <div class="features-grid">
        <div 
          class="feature-card" 
          v-for="feature in features" 
          :key="feature.name"
          @click="navigateTo(feature.route)"
        >
          <div class="feature-icon">
            <component :is="feature.icon" />
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-description">{{ feature.description }}</p>
          <div class="feature-badge" v-if="feature.badge">
            {{ feature.badge }}
          </div>
        </div>
      </div>

      <!-- 系统状态 -->
      <div class="status-section" v-if="systemStatus">
        <div class="status-item">
          <span class="status-label">系统状态</span>
          <el-tag :type="systemStatus.status === 'ok' ? 'success' : 'danger'">
            {{ systemStatus.status === 'ok' ? '正常' : '异常' }}
          </el-tag>
        </div>
        <div class="status-item">
          <span class="status-label">AI服务</span>
          <el-tag type="success">在线</el-tag>
        </div>
      </div>
    </div>

    <!-- 桌面端侧边栏导航 -->
    <div class="desktop-nav" v-if="!isMobile">
      <nav class="nav-menu">
        <router-link 
          v-for="nav in navigation" 
          :key="nav.name"
          :to="nav.route" 
          class="nav-item"
          active-class="nav-item-active"
        >
          <component :is="nav.icon" class="nav-icon" />
          <span>{{ nav.title }}</span>
        </router-link>
      </nav>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { 
  House, 
  Edit, 
  Microphone, 
  PieChart, 
  Setting,
  BookOpen,
  Target,
  Headset
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

// 响应式检测
const isMobile = ref(window.innerWidth <= 768)

// 系统状态
const systemStatus = ref<any>(null)

// 功能列表
const features = [
  {
    name: 'practice',
    title: '智能练习',
    description: '个性化题目推荐，AI智能出题',
    icon: Edit,
    route: '/practice',
    badge: '核心功能'
  },
  {
    name: 'podcast',
    title: 'AI播客',
    description: '个性化学习播客，随时随地学习',
    icon: Headset,
    route: '/podcast',
    badge: '新功能'
  },
  {
    name: 'analytics',
    title: '学习分析',
    description: '深度分析学习数据，发现薄弱环节',
    icon: PieChart,
    route: '/analytics',
    badge: null
  }
]

// 导航菜单
const navigation = [
  { name: 'home', title: '首页', icon: House, route: '/' },
  { name: 'practice', title: '练习', icon: Edit, route: '/practice' },
  { name: 'podcast', title: '播客', icon: Microphone, route: '/podcast' },
  { name: 'analytics', title: '分析', icon: PieChart, route: '/analytics' },
  { name: 'admin', title: '管理', icon: Setting, route: '/admin' }
]

// 方法
const navigateTo = (route: string) => {
  router.push(route)
}

const checkSystemStatus = async () => {
  try {
    // TODO: 调用系统状态API
    systemStatus.value = { status: 'ok' }
  } catch (error) {
    console.error('获取系统状态失败:', error)
  }
}

// 监听窗口大小变化
const handleResize = () => {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  checkSystemStatus()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.home-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  @media (max-width: 768px) {
    flex-direction: column;
  }
}

.mobile-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  
  .app-title {
    color: white;
    font-size: 18px;
    font-weight: 600;
    margin: 0;
  }
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  
  @media (max-width: 768px) {
    padding: 16px;
  }
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
  
  .welcome-title {
    color: white;
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 16px;
    
    @media (max-width: 768px) {
      font-size: 24px;
    }
  }
  
  .welcome-subtitle {
    color: rgba(255, 255, 255, 0.8);
    font-size: 18px;
    margin-bottom: 32px;
    
    @media (max-width: 768px) {
      font-size: 16px;
    }
  }
  
  .auth-notice {
    max-width: 500px;
    margin: 0 auto;
  }
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  }
  
  .feature-icon {
    width: 64px;
    height: 64px;
    margin: 0 auto 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 24px;
  }
  
  .feature-title {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 12px;
    color: #333;
  }
  
  .feature-description {
    color: #666;
    line-height: 1.6;
    margin-bottom: 0;
  }
  
  .feature-badge {
    position: absolute;
    top: 16px;
    right: 16px;
    background: #ff6b6b;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }
}

.status-section {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-top: 40px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 16px;
  }
  
  .status-item {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .status-label {
      color: rgba(255, 255, 255, 0.8);
      font-weight: 500;
    }
  }
}

.desktop-nav {
  width: 240px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  
  .nav-menu {
    padding: 24px 16px;
    
    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      color: rgba(255, 255, 255, 0.8);
      text-decoration: none;
      border-radius: 8px;
      margin-bottom: 8px;
      transition: all 0.3s ease;
      
      &:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
      }
      
      &.nav-item-active {
        background: rgba(255, 255, 255, 0.2);
        color: white;
      }
      
      .nav-icon {
        font-size: 18px;
      }
    }
  }
}
</style> 