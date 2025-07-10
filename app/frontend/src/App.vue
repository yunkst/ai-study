<template>
  <div id="app" class="app-container">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // 应用启动时检查认证状态
  authStore.checkAuthStatus()
})
</script>

<style lang="scss">
.app-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  
  // 响应式设计
  @media (max-width: 768px) {
    height: 100vh;
    height: 100dvh; // 动态视口高度
  }
}
</style> 