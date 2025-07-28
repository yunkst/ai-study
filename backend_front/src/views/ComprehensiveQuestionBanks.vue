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
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-number">{{ totalQuestionBanks }}</div>
              <div class="stats-label">总题库数</div>
            </div>
            <el-icon class="stats-icon"><collection /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-number">{{ totalQuestions }}</div>
              <div class="stats-label">总题目数</div>
            </div>
            <el-icon class="stats-icon"><document /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-number">{{ totalSubjects }}</div>
              <div class="stats-label">学科数量</div>
            </div>
            <el-icon class="stats-icon"><folder /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-number">{{ completedQuestionBanks }}</div>
              <div class="stats-label">已完成导入</div>
            </div>
            <el-icon class="stats-icon"><check /></el-icon>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="学科筛选">
          <el-select
            v-model="filterForm.subject_id"
            placeholder="全部学科"
            clearable
            style="width: 200px"
            @change="handleFilter"
          >
            <el-option label="全部学科" :value="null" />
            <el-option
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.name"
              :value="subject.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态筛选">
          <el-select
            v-model="filterForm.status"
            placeholder="全部状态"
            clearable
            style="width: 150px"
            @change="handleFilter"
          >
            <el-option label="全部状态" :value="null" />
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索题库名称或描述"
            style="width: 250px"
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 题库列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>题库列表</span>
          <div class="table-actions">
            <el-button
              size="small"
              @click="batchDelete"
              :disabled="selectedRows.length === 0"
              type="danger"
            >
              批量删除
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        :data="paginatedQuestionBanks"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="题库名称" min-width="200">
          <template #default="{ row }">
            <div class="question-bank-name">
              <strong>{{ row.name }}</strong>
              <div class="subject-tag" v-if="row.subject">
                <el-tag size="small" type="info">{{ row.subject.name }}</el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            <el-text class="description-text" truncated>
              {{ row.description || '无描述' }}
            </el-text>
          </template>
        </el-table-column>
        <el-table-column label="题目统计" width="150">
          <template #default="{ row }">
            <div class="question-stats">
              <div>总数: {{ row.total_questions }}</div>
              <div>已导入: {{ row.imported_questions }}</div>
              <el-progress
                :percentage="getImportProgress(row)"
                :stroke-width="4"
                :show-text="false"
                :color="getProgressColor(row)"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">
              详情
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click="viewQuestions(row)"
              :disabled="row.imported_questions === 0"
            >
              查看题目
            </el-button>
            <el-button
              size="small"
              type="warning"
              @click="reimportQuestionBank(row)"
              :disabled="row.status === 'completed'"
            >
              重新导入
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteQuestionBank(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredQuestionBanks.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传题库"
      width="600px"
      @close="resetUploadForm"
    >
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="题库名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入题库名称" />
        </el-form-item>
        <el-form-item label="所属学科" prop="subject_id">
          <el-select v-model="uploadForm.subject_id" placeholder="请选择学科" style="width: 100%">
            <el-option
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.name"
              :value="subject.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="题库描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入题库描述（可选）"
          />
        </el-form-item>
        <el-form-item label="题库文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".json"
            :on-change="handleFileChange"
            :file-list="fileList"
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传JSON格式的题库文件，且不超过50MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="uploading"
            @click="handleUpload"
          >
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="题库详情"
      width="700px"
    >
      <div v-if="selectedQuestionBank">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="题库名称" :span="2">
            <strong>{{ selectedQuestionBank.name }}</strong>
          </el-descriptions-item>
          <el-descriptions-item label="所属学科">
            <el-tag v-if="selectedQuestionBank.subject" type="info">
              {{ selectedQuestionBank.subject.name }}
            </el-tag>
            <span v-else>未分类</span>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedQuestionBank.status)">
              {{ getStatusText(selectedQuestionBank.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总题数">
            {{ selectedQuestionBank.total_questions }}
          </el-descriptions-item>
          <el-descriptions-item label="已导入">
            {{ selectedQuestionBank.imported_questions }}
          </el-descriptions-item>
          <el-descriptions-item label="导入进度">
            <el-progress
              :percentage="getImportProgress(selectedQuestionBank)"
              :color="getProgressColor(selectedQuestionBank)"
            />
          </el-descriptions-item>
          <el-descriptions-item label="文件名">
            {{ selectedQuestionBank.file_name }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(selectedQuestionBank.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ selectedQuestionBank.updated_at ? formatDate(selectedQuestionBank.updated_at) : '未更新' }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedQuestionBank.description || '无描述' }}
          </el-descriptions-item>
          <el-descriptions-item
            v-if="selectedQuestionBank.error_message"
            label="错误信息"
            :span="2"
          >
            <el-text type="danger">{{ selectedQuestionBank.error_message }}</el-text>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type UploadFile, type MessageParamsWithType } from 'element-plus'
import {
  Upload,
  Refresh,
  Collection,
  Document,
  Folder,
  Check,
  Search,
  UploadFilled
} from '@element-plus/icons-vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

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
  subject?: Subject
}

interface Subject {
  id: number
  name: string
  description?: string
}

const router = useRouter()
const loading = ref(false)
const uploading = ref(false)
const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const questionBanks = ref<QuestionBank[]>([])
const subjects = ref<Subject[]>([])
const selectedQuestionBank = ref<QuestionBank | null>(null)
const selectedRows = ref<QuestionBank[]>([])
const uploadFormRef = ref<FormInstance>()
const uploadRef = ref()
const fileList = ref<UploadFile[]>([])

// 筛选表单
const filterForm = reactive({
  subject_id: null as number | null,
  status: null as string | null,
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20
})

// 上传表单
const uploadForm = reactive({
  name: '',
  description: '',
  subject_id: null as number | null,
  file: null as File | null
})

const uploadRules = {
  name: [{ required: true, message: '请输入题库名称', trigger: 'blur' }],
  subject_id: [{ required: true, message: '请选择学科', trigger: 'change' }],
  file: [{ required: true, message: '请选择题库文件', trigger: 'change' }]
}

// 计算属性
const totalQuestionBanks = computed(() => questionBanks.value.length)
const totalQuestions = computed(() => 
  questionBanks.value.reduce((sum, bank) => sum + bank.imported_questions, 0)
)
const totalSubjects = computed(() => subjects.value.length)
const completedQuestionBanks = computed(() => 
  questionBanks.value.filter(bank => bank.status === 'completed').length
)

// 筛选后的题库列表
const filteredQuestionBanks = computed(() => {
  let filtered = questionBanks.value

  // 学科筛选
  if (filterForm.subject_id !== null) {
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

// 分页后的题库列表
const paginatedQuestionBanks = computed(() => {
  const start = (pagination.page - 1) * pagination.size
  const end = start + pagination.size
  return filteredQuestionBanks.value.slice(start, end)
})

// 获取学科列表
const fetchSubjects = async () => {
  try {
    const response = await axios.get('/api/v1/questions/subjects')
    subjects.value = response.data
  } catch {
    ElMessage.error('获取学科列表失败' as MessageParamsWithType)
  }
}

// 获取题库列表
const fetchQuestionBanks = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/question-banks/')
    questionBanks.value = response.data
  } catch {
    ElMessage.error('获取题库列表失败' as MessageParamsWithType)
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  await Promise.all([fetchSubjects(), fetchQuestionBanks()])
  ElMessage.success('数据刷新成功' as MessageParamsWithType)
}

// 处理筛选
const handleFilter = () => {
  pagination.page = 1 // 重置到第一页
}

// 处理搜索（防抖）
let searchTimeout: number
const handleSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    pagination.page = 1
  }, 300)
}

// 重置筛选
const resetFilter = () => {
  filterForm.subject_id = null
  filterForm.status = null
  filterForm.keyword = ''
  pagination.page = 1
}

// 处理选择变化
const handleSelectionChange = (selection: QuestionBank[]) => {
  selectedRows.value = selection
}

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
}

// 文件选择处理
const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    // 验证文件类型
    if (!file.name.endsWith('.json')) {
      ElMessage.error('只能上传JSON格式的文件' as MessageParamsWithType)
      uploadRef.value.clearFiles()
      return
    }
    
    // 验证文件大小 (50MB)
    if (file.size && file.size > 50 * 1024 * 1024) {
      ElMessage.error('文件大小不能超过50MB' as MessageParamsWithType)
      uploadRef.value.clearFiles()
      return
    }
    
    uploadForm.file = file.raw
    fileList.value = [file]
  }
}

// 上传题库
const handleUpload = async () => {
  if (!uploadFormRef.value) return
  
  await uploadFormRef.value.validate(async (valid) => {
    if (valid && uploadForm.file) {
      uploading.value = true
      try {
        const formData = new FormData()
        formData.append('name', uploadForm.name)
        formData.append('description', uploadForm.description)
        formData.append('subject_id', uploadForm.subject_id?.toString() || '')
        formData.append('file', uploadForm.file)
        
        await axios.post('/api/v1/question-banks/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        ElMessage.success('题库上传成功' as MessageParamsWithType)
        showUploadDialog.value = false
        fetchQuestionBanks()
      } catch {
        ElMessage.error('上传失败' as MessageParamsWithType)
      } finally {
        uploading.value = false
      }
    }
  })
}

// 重置上传表单
const resetUploadForm = () => {
  uploadForm.name = ''
  uploadForm.description = ''
  uploadForm.subject_id = null
  uploadForm.file = null
  fileList.value = []
  uploadRef.value?.clearFiles()
}

// 查看详情
const viewDetails = (questionBank: QuestionBank) => {
  selectedQuestionBank.value = questionBank
  showDetailDialog.value = true
}

// 查看题目
const viewQuestions = (questionBank: QuestionBank) => {
  router.push({
    name: 'Questions',
    query: {
      subject_id: questionBank.subject_id,
      question_bank_id: questionBank.id
    }
  })
}

// 重新导入题库
const reimportQuestionBank = async (questionBank: QuestionBank) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新导入题库 "${questionBank.name}" 吗？`,
      '确认重新导入',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.post(`/api/v1/question-banks/${questionBank.id}/reimport`)
    ElMessage.success('重新导入成功' as MessageParamsWithType)
    fetchQuestionBanks()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      ElMessage.error('重新导入失败' as MessageParamsWithType)
    }
  }
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
    
    await axios.delete(`/api/v1/question-banks/${questionBank.id}`)
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
  if (selectedRows.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个题库吗？此操作不可恢复！`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const deletePromises = selectedRows.value.map(bank => 
      axios.delete(`/api/v1/question-banks/${bank.id}`)
    )
    
    await Promise.all(deletePromises)
    ElMessage.success('批量删除成功' as MessageParamsWithType)
    selectedRows.value = []
    fetchQuestionBanks()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败' as MessageParamsWithType)
    }
  }
}

// 获取导入进度
const getImportProgress = (questionBank: QuestionBank) => {
  if (questionBank.total_questions === 0) return 0
  return Math.round((questionBank.imported_questions / questionBank.total_questions) * 100)
}

// 获取进度条颜色
const getProgressColor = (questionBank: QuestionBank) => {
  const progress = getImportProgress(questionBank)
  if (progress === 100) return '#67c23a'
  if (progress >= 50) return '#e6a23c'
  return '#f56c6c'
}

// 获取状态类型
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || status
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchSubjects()
  fetchQuestionBanks()
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
  color: #333;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stats-card {
  position: relative;
  overflow: hidden;
}

.stats-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stats-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.stats-label {
  font-size: 14px;
  color: #666;
}

.stats-icon {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 40px;
  color: #409eff;
  opacity: 0.3;
}

.filter-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-actions {
  display: flex;
  gap: 10px;
}

.question-bank-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subject-tag {
  align-self: flex-start;
}

.description-text {
  max-width: 200px;
}

.question-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.el-table {
  font-size: 14px;
}

.el-table .el-table__cell {
  padding: 12px 0;
}

.el-progress {
  margin-top: 4px;
}

.el-upload {
  width: 100%;
}

.el-upload-dragger {
  width: 100%;
}
</style>