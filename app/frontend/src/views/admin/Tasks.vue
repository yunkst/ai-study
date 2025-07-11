<template>
  <div class="tasks-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务管理</span>
          <el-button type="primary" size="small" @click="loadTasks" :loading="loading" plain>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" min-width="180" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run" label="最后运行" width="160" />
        <el-table-column prop="next_run" label="下次运行" width="160" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="runTask(row.id)">立即执行</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

interface Task {
  id: number
  name: string
  status: string
  last_run: string
  next_run: string
}

const tasks = ref<Task[]>([])
const loading = ref(false)

// 已移除占位任务数据

const statusTagType = (status: string) => {
  switch (status) {
    case '成功':
      return 'success'
    case '失败':
      return 'danger'
    case '排队':
      return 'info'
    default:
      return 'warning'
  }
}

const loadTasks = async () => {
  loading.value = true
  try {
    const resp = await fetch('/api/tasks')
    if (resp.ok) {
      tasks.value = await resp.json()
    } else {
      tasks.value = []
    }
  } catch (e) {
    tasks.value = []
  } finally {
    loading.value = false
  }
}

const runTask = async (taskId: number) => {
  ElMessage.info(`已发送任务 ${taskId} 执行请求`)
  // 这里可以调用后端 API 触发任务执行
}

onMounted(loadTasks)
</script>

<style scoped>
.tasks-container {
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