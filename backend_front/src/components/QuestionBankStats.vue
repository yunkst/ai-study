<template>
  <div class="stats-cards">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-number">{{ stats.totalQuestionBanks }}</div>
            <div class="stats-label">总题库数</div>
          </div>
          <el-icon class="stats-icon"><collection /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-number">{{ stats.totalQuestions }}</div>
            <div class="stats-label">总题目数</div>
          </div>
          <el-icon class="stats-icon"><document /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-number">{{ stats.totalSubjects }}</div>
            <div class="stats-label">学科数量</div>
          </div>
          <el-icon class="stats-icon"><folder /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-number">{{ stats.completedQuestionBanks }}</div>
            <div class="stats-label">已完成导入</div>
          </div>
          <el-icon class="stats-icon"><check /></el-icon>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { Collection, Document, Folder, Check } from '@element-plus/icons-vue'

interface StatsData {
  totalQuestionBanks: number
  totalQuestions: number
  totalSubjects: number
  completedQuestionBanks: number
}

defineProps<{
  stats: StatsData
}>()
</script>

<style scoped>
.stats-cards {
  margin-bottom: 20px;
}

.stats-card {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stats-content {
  position: relative;
  z-index: 2;
}

.stats-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stats-label {
  font-size: 14px;
  color: #666;
}

.stats-icon {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 40px;
  color: #409eff;
  opacity: 0.3;
}
</style>