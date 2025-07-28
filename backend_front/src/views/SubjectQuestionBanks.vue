<template>
  <div class="subject-question-banks-page">
    <div class="page-header">
      <div class="header-left">
        <el-button 
          link 
          @click="goBack"
          class="back-button"
        >
          <el-icon><arrow-left /></el-icon>
          返回
        </el-button>
        <div class="page-info">
          <h1>{{ subject?.name }} - 题库管理</h1>
          <p>管理该学科下的所有题库文件</p>
        </div>
      </div>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><upload /></el-icon>
        上传题库
      </el-button>
    </div>

    <div class="question-banks-content">
      <div class="empty-state" v-if="questionBanks.length === 0 && !loading">
        <div class="empty-content">
          <el-icon class="empty-icon" size="80">
            <folder-opened />
          </el-icon>
          <h3>暂无题库</h3>
          <p>开始上传您的第一个题库文件吧！</p>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><upload /></el-icon>
            上传题库
          </el-button>
        </div>
      </div>

      <div class="question-banks-list" v-else>
        <el-table 
          :data="questionBanks" 
          v-loading="loading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="name" label="题库名称" min-width="200">
            <template #default="{ row }">
              <div class="bank-name">
                <el-icon class="file-icon"><document /></el-icon>
                <span>{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="250">
            <template #default="{ row }">
              <span>{{ row.description || '暂无描述' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="question_count" label="题目数量" width="120" align="center">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.question_count || 0 }} 题</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="上传时间" width="180">
            <template #default="{ row }">
              <span>{{ formatDate(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" align="center">
            <template #default="{ row }">
              <el-button 
                link 
                size="small" 
                @click="viewQuestions(row)"
              >
                查看题目
              </el-button>
              <el-button 
                link 
                size="small" 
                @click="deleteQuestionBank(row)"
                class="delete-btn"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 上传题库对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传题库"
      width="600px"
      :before-close="handleCloseUploadDialog"
    >
      <div class="upload-content">
        <div class="format-info">
          <h4>支持的文件格式：</h4>
          <p>JSON格式的题库文件，请参考示例格式上传</p>
          <el-link type="primary" @click="downloadSample">下载示例文件</el-link>
        </div>
        
        <el-form
          ref="uploadFormRef"
          :model="uploadForm"
          :rules="uploadRules"
          label-width="100px"
        >
          <el-form-item label="题库名称" prop="name">
            <el-input
              v-model="uploadForm.name"
              placeholder="请输入题库名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="题库描述" prop="description">
            <el-input
              v-model="uploadForm.description"
              type="textarea"
              placeholder="请输入题库描述（可选）"
              :rows="3"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="题库文件" prop="file">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :on-exceed="handleExceed"
              :before-upload="beforeUpload"
              accept=".json"
              drag
              @click="handleUploadClick"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  只能上传JSON文件，且不超过10MB
                </div>
              </template>
            </el-upload>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseUploadDialog">取消</el-button>
          <el-button 
            type="primary" 
            :loading="uploadLoading" 
            @click="handleUpload"
            :disabled="!uploadForm.file"
          >
            上传
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type MessageParamsWithType, type UploadFile } from 'element-plus'
import {
  ArrowLeft,
  Upload,
  Document,
  FolderOpened,
  UploadFilled
} from '@element-plus/icons-vue'
import { subjectApi, questionBankApi, type Subject, type QuestionBank } from '../services/api'

// 接口定义已从API服务中导入

const router = useRouter()
const route = useRoute()
const subject = ref<Subject | null>(null)
const questionBanks = ref<QuestionBank[]>([])
const loading = ref(false)
const showUploadDialog = ref(false)
const uploadLoading = ref(false)
const uploadFormRef = ref<FormInstance>()
const uploadRef = ref()

const uploadForm = reactive({
  name: '',
  description: '',
  file: null as File | null
})

const uploadRules = {
  name: [
    { required: true, message: '请输入题库名称', trigger: 'blur' },
    { min: 1, max: 100, message: '题库名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 获取学科详情
const fetchSubjectDetail = async () => {
  try {
    const subjectId = parseInt(route.params.subjectId as string)
    subject.value = await subjectApi.getSubject(subjectId)
  } catch (error: unknown) {
    console.error('获取学科详情失败:', error)
    // 错误处理已在HTTP服务中统一处理
  }
}

// 获取题库列表
const fetchQuestionBanks = async () => {
  try {
    loading.value = true
    const subjectId = parseInt(route.params.subjectId as string)
    questionBanks.value = await questionBankApi.getQuestionBanks(subjectId)
  } catch (error: unknown) {
    console.error('获取题库列表失败:', error)
    // 错误处理已在HTTP服务中统一处理
  } finally {
    loading.value = false
  }
}

// 文件选择处理
const handleFileChange = (file: UploadFile) => {
  console.log('handleFileChange 被调用了！', file)
  console.log('文件名:', file.name)
  console.log('文件大小:', file.size)
  console.log('文件类型:', file.raw?.type)
  console.log('文件状态:', file.status)
  
  if (file.raw) {
    uploadForm.file = file.raw
    console.log('文件已设置到 uploadForm.file:', uploadForm.file)
  } else {
    console.log('警告: file.raw 为空')
  }
}

// 文件移除处理
const handleFileRemove = () => {
  console.log('handleFileRemove 被调用了！')
  uploadForm.file = null
}

// 上传点击处理
const handleUploadClick = () => {
  console.log('上传组件被点击了！')
}

// 文件数量超限处理
const handleExceed = () => {
  console.log('文件数量超限！')
  ElMessage.warning('只能上传一个文件' as MessageParamsWithType)
}

// 上传前处理
const beforeUpload = (file: File) => {
  console.log('beforeUpload 被调用了！', file)
  console.log('文件名:', file.name)
  console.log('文件大小:', file.size)
  console.log('文件类型:', file.type)
  
  // 检查文件类型
  if (file.type !== 'application/json') {
    ElMessage.error('只能上传 JSON 格式的文件！' as MessageParamsWithType)
    return false
  }
  
  // 检查文件大小（10MB = 10 * 1024 * 1024 bytes）
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB！' as MessageParamsWithType)
    return false
  }
  
  console.log('文件验证通过')
  return false // 阻止自动上传
}

// 上传题库
const handleUpload = async () => {
  if (!uploadFormRef.value) return
  
  try {
    await uploadFormRef.value.validate()
    
    if (!uploadForm.file) {
      ElMessage.error('请选择要上传的文件' as MessageParamsWithType )
      return
    }
    
    uploadLoading.value = true
    const subjectId = route.params.subjectId as string
    
    await questionBankApi.uploadQuestionBank({
      name: uploadForm.name,
      description: uploadForm.description,
      subject_id: Number(subjectId),
      file: uploadForm.file!
    })
    
    ElMessage.success('题库上传成功' as MessageParamsWithType)
    handleCloseUploadDialog()
    fetchQuestionBanks()
  } catch (error: unknown) {
    console.error('上传题库失败:', error)
    // 错误处理已在HTTP服务中统一处理
  } finally {
    uploadLoading.value = false
  }
}

// 关闭上传对话框
const handleCloseUploadDialog = () => {
  showUploadDialog.value = false
  uploadForm.name = ''
  uploadForm.description = ''
  uploadForm.file = null
  if (uploadFormRef.value) {
    uploadFormRef.value.clearValidate()
  }
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 查看题目
const viewQuestions = (questionBank: QuestionBank) => {
  const subjectId = route.params.subjectId as string
  router.push(`/subject/${subjectId}/question-banks/${questionBank.id}/questions`)
}

// 删除题库
const deleteQuestionBank = async (questionBank: QuestionBank) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除题库 "${questionBank.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await questionBankApi.deleteQuestionBank(questionBank.id)
    ElMessage.success('题库删除成功' as MessageParamsWithType)
    fetchQuestionBanks()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      console.error('删除题库失败:', error)
      // 错误处理已在HTTP服务中统一处理
    }
  }
}

// 下载示例文件
const downloadSample = () => {
  // 创建示例数据
  const sampleData = {
    "questions": [
      {
        "question": "以下哪个是JavaScript的数据类型？",
        "type": "single_choice",
        "options": [
          "string",
          "number",
          "boolean",
          "以上都是"
        ],
        "answer": "以上都是",
        "explanation": "JavaScript有多种基本数据类型，包括string、number、boolean等。"
      },
      {
        "question": "请选择所有正确的HTML标签：",
        "type": "multiple_choice",
        "options": [
          "<div>",
          "<span>",
          "<section>",
          "<invalid>"
        ],
        "answer": ["<div>", "<span>", "<section>"],
        "explanation": "<div>、<span>和<section>都是有效的HTML标签，而<invalid>不是标准HTML标签。"
      }
    ]
  }
  
  const blob = new Blob([JSON.stringify(sampleData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'question_bank_sample.json'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 返回上一页
const goBack = () => {
  const subjectId = route.params.subjectId as string
  router.push(`/subject/${subjectId}`)
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchSubjectDetail()
  fetchQuestionBanks()
})
</script>

<style scoped>
.subject-question-banks-page {
  min-height: 100%;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.back-button {
  padding: 8px;
  font-size: 16px;
  color: #409eff;
  margin-top: 5px;
}

.back-button:hover {
  background-color: #ecf5ff;
}

.page-info h1 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-info p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.question-banks-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.empty-content {
  text-align: center;
  max-width: 400px;
}

.empty-icon {
  color: #c0c4cc;
  margin-bottom: 20px;
}

.empty-content h3 {
  color: #303133;
  margin-bottom: 10px;
}

.empty-content p {
  color: #606266;
  margin-bottom: 30px;
  font-size: 14px;
}

.bank-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #409eff;
}

.delete-btn {
  color: #f56c6c;
}

.delete-btn:hover {
  color: #f56c6c;
  background-color: #fef0f0;
}

.upload-content {
  padding: 10px 0;
}

.format-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.format-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.format-info p {
  margin: 0 0 10px 0;
  color: #606266;
  font-size: 13px;
}

.dialog-footer {
  text-align: right;
}
</style>