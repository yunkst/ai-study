<template>
  <div class="analytics-container">
    <div class="analytics-header">
      <h1>学习分析</h1>
      <p>以下数据基于您的最近学习记录</p>
    </div>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-statistic title="本周学习时长 (小时)" :value="stats.hours" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="已完成练习题" :value="stats.completed" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="平均正确率" :value="stats.accuracy" suffix="%" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="知识覆盖率" :value="stats.coverage" suffix="%" />
      </el-col>
    </el-row>

    <el-card class="progress-card" shadow="hover">
      <template #header>
        <span>知识域进度</span>
      </template>
      <div v-for="item in domainProgress" :key="item.domain" class="progress-item">
        <div class="label">{{ item.domain }}</div>
        <el-progress :percentage="item.percent" :stroke-width="14" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Stats {
  hours: number
  completed: number
  accuracy: number
  coverage: number
}

const stats = ref<Stats>({ hours: 0, completed: 0, accuracy: 0, coverage: 0 })

interface DomainProgress {
  domain: string
  percent: number
}

const domainProgress = ref<DomainProgress[]>([])

const loadStats = async () => {
  try {
    const resp = await fetch('/api/analytics')
    if (resp.ok) {
      const data = await resp.json()
      stats.value = data.summary
      domainProgress.value = data.domain_progress
    } else {
      stats.value = { hours: 0, completed: 0, accuracy: 0, coverage: 0 }
      domainProgress.value = []
    }
  } catch (e) {
    stats.value = { hours: 0, completed: 0, accuracy: 0, coverage: 0 }
    domainProgress.value = []
  }
}

// 已移除 mock 假数据函数

onMounted(loadStats)
</script>

<style lang="scss" scoped>
.analytics-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.analytics-header {
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

.stats-row {
  margin-bottom: 40px;
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.progress-card {
  max-width: 800px;
  margin: 0 auto;
}

.progress-item {
  margin-bottom: 20px;
  .label {
    margin-bottom: 8px;
    font-weight: bold;
  }
}
</style> 