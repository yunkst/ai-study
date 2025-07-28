<template>
  <div class="question-banks">
    <div class="page-header">
      <h3>题库管理</h3>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><upload /></el-icon>
        上传题库
      </el-button>
    </div>

    <!-- 题库列表 -->
    <el-card>
      <el-table :data="questionBanks" v-loading="loading">
        <el-table-column prop="name" label="题库名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="total_questions" label="总题数" width="100" />
        <el-table-column prop="imported_questions" label="已导入" width="100" />
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
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetails(row)">详情</el-button>
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
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传题库"
      width="500px"
      @close="resetUploadForm"
    >
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef">
        <el-form-item label="题库名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入题库名称" />
        </el-form-item>
        <el-form-item label="学科" prop="subject_id">
          <el-select v-model="uploadForm.subject_id" placeholder="请选择学科" style="width: 100%">
            <el-option
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.name"
              :value="subject.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入题库描述"
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
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                只能上传JSON格式的题库文件，且不超过10MB
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
      width="600px"
    >
      <div v-if="selectedQuestionBank">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="题库名称">
            {{ selectedQuestionBank.name }}
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
          <el-descriptions-item label="文件名">
            {{ selectedQuestionBank.file_name }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(selectedQuestionBank.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedQuestionBank.description || '无' }}
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type UploadFile, type MessageParamsWithType } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import axios from 'axios'

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
  updated_at: string
}

interface Subject {
  id: number
  name: string
  description?: string
}

const loading = ref(false)
const uploading = ref(false)
const showUploadDialog = ref(false)
const showDetailDialog = ref(false)
const questionBanks = ref<QuestionBank[]>([])
const selectedQuestionBank = ref<QuestionBank | null>(null)
const uploadFormRef = ref<FormInstance>()
const uploadRef = ref()
const fileList = ref<UploadFile[]>([])
const subjects = ref<Subject[]>([])

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

// 文件选择处理
const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    // 验证文件类型
    if (!file.name.endsWith('.json')) {
      ElMessage.error('只能上传JSON格式的文件' as MessageParamsWithType)
      uploadRef.value.clearFiles()
      return
    }
    
    // 验证文件大小 (10MB)
    if (file.size && file.size > 10 * 1024 * 1024) {
      ElMessage.error('文件大小不能超过10MB' as MessageParamsWithType)
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

// 删除题库
const deleteQuestionBank = async (questionBank: QuestionBank) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除题库 "${questionBank.name}" 吗？`,
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
.question-banks {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h3 {
  margin: 0;
  color: #333;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>