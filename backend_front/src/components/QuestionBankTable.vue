<template>
  <div class="question-bank-table">
    <div class="table-header">
      <div class="table-title">
        <h3>题库列表</h3>
      </div>
      <div class="table-actions">
        <el-button
          type="danger"
          :disabled="selectedRows.length === 0"
          @click="$emit('batch-delete')"
        >
          批量删除
        </el-button>
      </div>
    </div>

    <el-table
      v-loading="loading"
      :data="questionBanks"
      @selection-change="handleSelectionChange"
      stripe
      style="width: 100%"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="题库名称" min-width="150">
        <template #default="{ row }">
          <el-link
            type="primary"
            @click="$emit('view-detail', row)"
          >
            {{ row.name }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="题目统计" width="200">
        <template #default="{ row }">
          <div class="question-stats">
            <div>总数: {{ row.total_questions }}</div>
            <div>已导入: {{ row.imported_questions }}</div>
            <el-progress
              :percentage="getImportProgress(row)"
              :color="getProgressColor(row)"
              :stroke-width="6"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            @click="$emit('view-detail', row)"
          >
            查看详情
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click="$emit('delete-item', row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        :current-page="pagination.page"
        :page-size="pagination.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="(size: number) => $emit('page-change', { type: 'size', value: size })"
        @current-change="(page: number) => $emit('page-change', { type: 'page', value: page })"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface QuestionBank {
  id: number
  name: string
  description?: string
  file_name: string
  total_questions: number
  imported_questions: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message?: string
  created_at: string
  updated_at?: string
  subject_id?: number
}

interface Pagination {
  page: number
  size: number
}

defineProps<{
  questionBanks: QuestionBank[]
  loading: boolean
  pagination: Pagination
  total: number
}>()

defineEmits<{
  'batch-delete': []
  'view-detail': [questionBank: QuestionBank]
  'delete-item': [questionBank: QuestionBank]
  'page-change': [event: { type: string; value: number }]
}>()

const selectedRows = ref<QuestionBank[]>([])

const handleSelectionChange = (selection: QuestionBank[]) => {
  selectedRows.value = selection
}

const getImportProgress = (row: QuestionBank): number => {
  if (row.total_questions === 0) return 0
  return Math.round((row.imported_questions / row.total_questions) * 100)
}

const getProgressColor = (row: QuestionBank): string => {
  const progress = getImportProgress(row)
  if (progress === 100) return '#67c23a'
  if (progress >= 50) return '#e6a23c'
  return '#f56c6c'
}

const getStatusType = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.question-bank-table {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.table-title h3 {
  margin: 0;
  color: #303133;
}

.question-stats {
  font-size: 12px;
}

.question-stats > div {
  margin-bottom: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>