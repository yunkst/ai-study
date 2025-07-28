<template>
  <div class="subject-detail-page">
    <div class="subject-header">
      <div class="header-left">
        <el-button 
          link 
          @click="goBack"
          class="back-button"
        >
          <el-icon><arrow-left /></el-icon>
          返回
        </el-button>
        <div class="subject-info">
          <h1>{{ subject?.name }}</h1>
          <p v-if="subject?.description">{{ subject.description }}</p>
        </div>
      </div>
    </div>

    <div class="modules-grid">
      <el-card 
        class="module-card"
        shadow="hover"
        @click="enterModule('question-banks')"
      >
        <div class="module-content">
          <div class="module-icon">
            <el-icon size="60">
              <upload />
            </el-icon>
          </div>
          <div class="module-info">
            <h3>题库管理</h3>
            <p>上传和管理题库文件，支持多种格式的题目导入</p>
            <div class="module-stats">
              <span>题库数量：{{ questionBankCount }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <el-card 
        class="module-card disabled"
        shadow="hover"
      >
        <div class="module-content">
          <div class="module-icon">
            <el-icon size="60">
              <document />
            </el-icon>
          </div>
          <div class="module-info">
            <h3>知识库</h3>
            <p>上传PDF、Word、TXT等文档，自动构建RAG知识库</p>
            <div class="module-stats">
              <el-tag type="info" size="small">即将推出</el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <el-card 
        class="module-card disabled"
        shadow="hover"
      >
        <div class="module-content">
          <div class="module-icon">
            <el-icon size="60">
              <data-analysis />
            </el-icon>
          </div>
          <div class="module-info">
            <h3>学习统计</h3>
            <p>查看学习进度、答题统计和知识掌握情况</p>
            <div class="module-stats">
              <el-tag type="info" size="small">即将推出</el-tag>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type MessageParamsWithType } from 'element-plus'
import {
  ArrowLeft,
  Upload,
  Document,
  DataAnalysis
} from '@element-plus/icons-vue'
import axios from 'axios'

interface Subject {
  id: number
  name: string
  description?: string
  created_at: string
}

const router = useRouter()
const route = useRoute()
const subject = ref<Subject | null>(null)
const questionBankCount = ref(0)

// 获取学科详情
const fetchSubjectDetail = async () => {
  try {
    const subjectId = route.params.subjectId
    const response = await axios.get(`/api/v1/questions/subjects/${subjectId}`)
    subject.value = response.data
  } catch (error) {
    console.error('获取学科详情失败:', error)
    ElMessage.error('获取学科详情失败' as MessageParamsWithType)
    goBack()
  }
}

// 获取题库数量
const fetchQuestionBankCount = async () => {
  try {
    const subjectId = route.params.subjectId
    const response = await axios.get(`/api/v1/question-banks/?subject_id=${subjectId}`)
    questionBankCount.value = response.data.length
  } catch (error) {
    console.error('获取题库数量失败:', error)
  }
}

// 返回上一页
const goBack = () => {
  router.push('/')
}

// 进入模块
const enterModule = (moduleType: string) => {
  const subjectId = route.params.subjectId
  
  switch (moduleType) {
    case 'question-banks':
      router.push(`/subject/${subjectId}/question-banks`)
      break
    case 'knowledge-base':
      ElMessage.info('知识库功能即将推出' as MessageParamsWithType)
      break
    case 'study-stats':
      ElMessage.info('学习统计功能即将推出' as MessageParamsWithType)
      break
  }
}

onMounted(() => {
  fetchSubjectDetail()
  fetchQuestionBankCount()
})
</script>

<style scoped>
.subject-detail-page {
  min-height: 100%;
  padding: 20px;
}

.subject-header {
  margin-bottom: 40px;
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

.subject-info h1 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.subject-info p {
  margin: 0;
  color: #606266;
  font-size: 16px;
  line-height: 1.5;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
  max-width: 1200px;
}

.module-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #ebeef5;
  min-height: 200px;
}

.module-card:hover:not(.disabled) {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.module-card.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.module-card.disabled:hover {
  transform: none;
  box-shadow: none;
}

.module-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px;
  height: 100%;
}

.module-icon {
  color: #409eff;
  margin-bottom: 20px;
}

.module-card.disabled .module-icon {
  color: #c0c4cc;
}

.module-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.module-info h3 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.module-card.disabled .module-info h3 {
  color: #909399;
}

.module-info p {
  margin: 0 0 20px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  flex: 1;
}

.module-card.disabled .module-info p {
  color: #c0c4cc;
}

.module-stats {
  font-size: 14px;
  color: #909399;
}
</style>