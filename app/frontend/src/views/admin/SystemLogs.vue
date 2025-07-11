<template>
  <div class="logs-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div class="actions">
            <el-button size="small" type="primary" @click="loadLogs" :loading="loading" plain>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="logs" stripe border style="width: 100%" height="500px">
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.level)" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface LogEntry {
  timestamp: string
  level: string
  message: string
}

const logs = ref<LogEntry[]>([])
const loading = ref(false)

// 已移除占位日志

const levelTagType = (level: string) => {
  switch (level) {
    case 'INFO':
      return 'info'
    case 'WARNING':
      return 'warning'
    case 'ERROR':
      return 'danger'
    default:
      return 'default'
  }
}

const loadLogs = async () => {
  loading.value = true
  try {
    const resp = await fetch('/api/logs?limit=100')
    if (resp.ok) {
      logs.value = await resp.json()
    } else {
      logs.value = []
    }
  } catch (e) {
    logs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadLogs)
</script>

<style scoped>
.logs-container {
  padding: 10px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}
</style> 