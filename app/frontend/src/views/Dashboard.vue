<template>
  <div class="dashboard-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>欢迎使用 AI 学习助手</span>
        </div>
      </template>
      <div class="card-content">
        <p>在这里，您可以开始您的个性化学习之旅。</p>
        <p>请从左侧菜单中选择一个功能开始：</p>
        <ul>
          <li><strong>练习：</strong> 进行智能练习，巩固知识点。</li>
          <li><strong>播客：</strong> 收听 AI 生成的学习播客。</li>
          <li><strong>分析：</strong> 查看您的学习进度和分析报告。</li>
          <li><strong>知识库：</strong> 管理和查阅您的知识库。</li>
          <li><strong>管理：</strong> 进行系统设置和管理。</li>
        </ul>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// No script logic needed for this simple component
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background-color: #f9fafb;
  height: 100%;
}
.card-header {
  font-size: 20px;
  font-weight: bold;
}
.card-content p {
  line-height: 1.8;
}
ul {
  list-style-position: inside;
  padding-left: 0;
}
li {
  margin-bottom: 10px;
}
</style> 