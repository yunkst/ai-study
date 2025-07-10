<template>
  <div class="practice-container">
    <div class="practice-header">
      <h1>智能练习</h1>
      <p>个性化AI题目推荐系统</p>
    </div>
    
    <div class="coming-soon">
      <el-icon size="64"><Edit /></el-icon>
      <h2>功能开发中...</h2>
      <p>智能练习功能正在紧急开发中，敬请期待！</p>
      <el-button type="primary" @click="$router.push('/')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Edit } from '@element-plus/icons-vue'
</script>

<style lang="scss" scoped>
.practice-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.practice-header {
  text-align: center;
  color: white;
  margin-bottom: 40px;
  
  h1 {
    font-size: 32px;
    margin-bottom: 12px;
  }
  
  p {
    font-size: 16px;
    opacity: 0.8;
  }
}

.coming-soon {
  text-align: center;
  background: white;
  border-radius: 16px;
  padding: 60px 40px;
  max-width: 500px;
  margin: 0 auto;
  
  .el-icon {
    color: #667eea;
    margin-bottom: 24px;
  }
  
  h2 {
    color: #333;
    margin-bottom: 16px;
  }
  
  p {
    color: #666;
    margin-bottom: 32px;
  }
}
</style> 