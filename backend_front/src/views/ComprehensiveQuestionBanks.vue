<template>
  <div class="comprehensive-question-banks">
    <div class="page-header">
      <h2>综合题库管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><upload /></el-icon>
          上传题库
        </el-button>
        <el-button @click="refreshData">
          <el-icon><refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <QuestionBankStats :stats="stats" />

    <!-- 筛选表单 -->
    <QuestionBankFilter
      v-model="filterForm"
      :subjects="subjects"
      @filter-change="handleFilterChange"
    />

    <!-- 题库列表 -->
    <QuestionBankTable
      :question-banks="filteredQuestionBanks"
      :loading="loading"
      :pagination="pagination"
      :total="total"
      @batch-delete="batchDelete"
      @view-detail="viewDetail"
      @delete-item="deleteQuestionBank"
      @page-change="handlePageChange"
    />

    <!-- 上传对话框 -->
    <QuestionBankUpload
      v-model="showUploadDialog"
      :subjects="subjects"
      @upload-success="handleUploadSuccess"
    />

    <!-- 详情对话框 -->
    <QuestionBankDetail
      v-model="showDetailDialog"
      :question-bank="selectedQuestionBank"
      @delete-success="handleDeleteSuccess"
      @retry-success="handleRetrySuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type MessageParamsWithType } from 'element-plus'
import { Upload, Refresh } from '@element-plus/icons-vue'
import { subjectApi, questionBankApi, questionApi, type Subject, type QuestionBank } from '../services/api'
import QuestionBankStats from '@/components/QuestionBankStats.vue'
import QuestionBankFilter from '@/components/QuestionBankFilter.vue'
import QuestionBankTable from '@/components/QuestionBankTable.vue'
import QuestionBankUpload from '@/components/QuestionBankUpload.vue'
import QuestionBankDetail from '@/components/QuestionBankDetail.vue'

// 接口定义已从API服务中导入

const loading = ref(false)
const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const questionBanks = ref<QuestionBank[]>([])
const subjects = ref<Subject[]>([])
const selectedQuestionBank = ref<QuestionBank | null>(null)

// 筛选表单
const filterForm = reactive({
  subject_id: '' as string | number,
  status: '' as string,
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20
})

// 统计数据
const stats = ref({
  totalQuestionBanks: 0,
  totalQuestions: 0,
  totalSubjects: 0,
  completedQuestionBanks: 0
})

// 筛选后的题库列表
const filteredQuestionBanks = computed(() => {
  let filtered = questionBanks.value

  // 学科筛选
  if (filterForm.subject_id) {
    filtered = filtered.filter(bank => bank.subject_id === filterForm.subject_id)
  }

  // 状态筛选
  if (filterForm.status) {
    filtered = filtered.filter(bank => bank.status === filterForm.status)
  }

  // 关键词搜索
  if (filterForm.keyword) {
    const keyword = filterForm.keyword.toLowerCase()
    filtered = filtered.filter(bank => 
      bank.name.toLowerCase().includes(keyword) ||
      (bank.description && bank.description.toLowerCase().includes(keyword))
    )
  }

  return filtered
})

// 总数
const total = computed(() => filteredQuestionBanks.value.length)

// 获取统计数据
const fetchStats = async () => {
  try {
    // 获取题库总数
    const questionBanks = await questionBankApi.getQuestionBanks()
    stats.value.totalQuestionBanks = questionBanks.length
    stats.value.completedQuestionBanks = questionBanks.filter((bank: QuestionBank) => bank.status === 'completed').length
    
    // 获取总题目数
    const questionsResponse = await questionApi.getQuestions({ size: 1 })
    stats.value.totalQuestions = questionsResponse.total || 0
    
    // 获取学科总数
    const subjects = await subjectApi.getSubjects()
    stats.value.totalSubjects = subjects.length
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取题库列表
const fetchQuestionBanks = async () => {
  loading.value = true
  try {
    questionBanks.value = await questionBankApi.getQuestionBanks()
  } catch (error: unknown) {
    console.error('获取题库列表失败:', error)
    ElMessage.error('获取题库列表失败' as MessageParamsWithType)
  } finally {
    loading.value = false
  }
}

// 获取学科列表
const fetchSubjects = async () => {
  try {
    subjects.value = await subjectApi.getSubjects()
  } catch (error: unknown) {
    console.error('获取学科列表失败:', error)
    ElMessage.error('获取学科列表失败' as MessageParamsWithType)
  }
}

// 刷新数据
const refreshData = async () => {
  await Promise.all([fetchSubjects(), fetchQuestionBanks(), fetchStats()])
  ElMessage.success('数据刷新成功' as MessageParamsWithType)
}

// 筛选变化处理
const handleFilterChange = () => {
  pagination.page = 1
}

// 分页变化处理
const handlePageChange = (event?: { type: string; value: number }) => {
  if (!event) return
  
  if (event.type === 'page') {
    pagination.page = event.value
  } else if (event.type === 'size') {
    pagination.size = event.value
    pagination.page = 1 // 重置到第一页
  }
}

// 查看详情
const viewDetail = (questionBank: QuestionBank) => {
  selectedQuestionBank.value = questionBank
  showDetailDialog.value = true
}

// 删除题库
const deleteQuestionBank = async (questionBank: QuestionBank) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除题库 "${questionBank.name}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await questionBankApi.deleteQuestionBank(questionBank.id)
    ElMessage.success('删除成功' as MessageParamsWithType)
    fetchQuestionBanks()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败' as MessageParamsWithType)
    }
  }
}

// 批量删除
const batchDelete = async () => {
  // 这个功能需要在QuestionBankTable组件中实现选择逻辑
  ElMessage.info('批量删除功能待实现' as MessageParamsWithType)
}

// 上传成功处理
const handleUploadSuccess = () => {
  fetchQuestionBanks()
  fetchStats()
}

// 删除成功处理
const handleDeleteSuccess = () => {
  fetchQuestionBanks()
  fetchStats()
}

// 重试成功处理
const handleRetrySuccess = () => {
  fetchQuestionBanks()
  fetchStats()
}

onMounted(() => {
  fetchSubjects()
  fetchQuestionBanks()
  fetchStats()
})
</script>

<style scoped>
.comprehensive-question-banks {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}
</style>