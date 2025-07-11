<template>
  <div id="app" class="app-container">
    <router-view />
  </div>
</template>

<script setup lang="ts">
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