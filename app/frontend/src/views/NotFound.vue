<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1 class="error-title">页面未找到</h1>
      <p class="error-message">抱歉，您访问的页面不存在或已被移除</p>
      
      <div class="action-buttons">
        <el-button type="primary" @click="$router.push('/')">
          返回首页
        </el-button>
        <el-button @click="$router.back()">
          返回上页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 404页面不需要额外逻辑
</script>

<style lang="scss" scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.not-found-content {
  text-align: center;
  color: white;
  
  .error-code {
    font-size: 120px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 24px;
    opacity: 0.8;
    
    @media (max-width: 768px) {
      font-size: 80px;
    }
  }
  
  .error-title {
    font-size: 32px;
    font-weight: 600;
    margin-bottom: 16px;
    
    @media (max-width: 768px) {
      font-size: 24px;
    }
  }
  
  .error-message {
    font-size: 16px;
    opacity: 0.8;
    margin-bottom: 40px;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }
  
  .action-buttons {
    display: flex;
    gap: 16px;
    justify-content: center;
    
    @media (max-width: 768px) {
      flex-direction: column;
      align-items: center;
    }
  }
}
</style> 