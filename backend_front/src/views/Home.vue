<template>
  <div class="home-page">
    <div class="empty-state" v-if="subjects.length === 0">
      <div class="empty-content">
        <el-icon class="empty-icon" size="80">
          <folder-add />
        </el-icon>
        <h2>欢迎使用AI学习系统</h2>
        <p>开始创建您的第一个学科吧！</p>
        <el-button type="primary" size="large" @click="showAddDialog = true">
          <el-icon><plus /></el-icon>
          添加学科
        </el-button>
      </div>
    </div>

    <div class="subjects-grid" v-else>
      <div class="subjects-header">
        <h2>我的学科</h2>
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><plus /></el-icon>
          添加学科
        </el-button>
      </div>
      
      <div class="subjects-list">
        <el-card 
          v-for="subject in subjects" 
          :key="subject.id" 
          class="subject-card"
          shadow="hover"
          @click="enterSubject(subject)"
        >
          <div class="subject-content">
            <div class="subject-icon">
              <el-icon size="40">
                <collection />
              </el-icon>
            </div>
            <div class="subject-info">
              <h3>{{ subject.name }}</h3>
              <p>{{ subject.description || '暂无描述' }}</p>
              <div class="subject-stats">
                <span>创建时间：{{ formatDate(subject.created_at) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 添加学科对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加学科"
      width="500px"
      :before-close="handleCloseDialog"
    >
      <el-form
        ref="subjectFormRef"
        :model="subjectForm"
        :rules="subjectRules"
        label-width="80px"
      >
        <el-form-item label="学科名称" prop="name">
          <el-input
            v-model="subjectForm.name"
            placeholder="请输入学科名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="学科描述" prop="description">
          <el-input
            v-model="subjectForm.description"
            type="textarea"
            placeholder="请输入学科描述（可选）"
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseDialog">取消</el-button>
          <el-button type="primary" :loading="loading" @click="handleAddSubject">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type MessageParamsWithType } from 'element-plus'
import {
  Plus,
  FolderAdd,
  Collection
} from '@element-plus/icons-vue'
import { subjectApi, type Subject } from '../services/api'

const router = useRouter()
const subjects = ref<Subject[]>([])
const showAddDialog = ref(false)
const loading = ref(false)
const subjectFormRef = ref<FormInstance>()

const subjectForm = reactive({
  name: '',
  description: ''
})

const subjectRules = {
  name: [
    { required: true, message: '请输入学科名称', trigger: 'blur' },
    { min: 1, max: 50, message: '学科名称长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

// 获取学科列表
const fetchSubjects = async () => {
  try {
    subjects.value = await subjectApi.getSubjects()
  } catch (error) {
    console.error('获取学科列表失败:', error)
    ElMessage.error('获取学科列表失败' as MessageParamsWithType)
  }
}

// 添加学科
const handleAddSubject = async () => {
  if (!subjectFormRef.value) return
  
  try {
    await subjectFormRef.value.validate()
    loading.value = true
    
    const newSubject = await subjectApi.createSubject(subjectForm)
    subjects.value.push(newSubject)
    
    ElMessage.success('学科添加成功' as MessageParamsWithType)
    handleCloseDialog()
  } catch (error) {
    console.error('添加学科失败:', error)
    ElMessage.error('添加学科失败' as MessageParamsWithType)
  } finally {
    loading.value = false
  }
}

// 关闭对话框
const handleCloseDialog = () => {
  showAddDialog.value = false
  subjectForm.name = ''
  subjectForm.description = ''
  if (subjectFormRef.value) {
    subjectFormRef.value.clearValidate()
  }
}

// 进入学科
const enterSubject = (subject: Subject) => {
  // 跳转到学科详情页面，传递学科ID
  router.push({ name: 'SubjectDetail', params: { subjectId: subject.id.toString() } })
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchSubjects()
})
</script>

<style scoped>
.home-page {
  min-height: 100%;
  padding: 20px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.empty-content {
  text-align: center;
  max-width: 400px;
}

.empty-icon {
  color: #c0c4cc;
  margin-bottom: 20px;
}

.empty-content h2 {
  color: #303133;
  margin-bottom: 10px;
}

.empty-content p {
  color: #606266;
  margin-bottom: 30px;
  font-size: 16px;
}

.subjects-grid {
  max-width: 1200px;
  margin: 0 auto;
}

.subjects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.subjects-header h2 {
  color: #303133;
  margin: 0;
}

.subjects-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.subject-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #ebeef5;
}

.subject-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.subject-content {
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.subject-icon {
  color: #409eff;
  flex-shrink: 0;
}

.subject-info {
  flex: 1;
  min-width: 0;
}

.subject-info h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.subject-info p {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.subject-stats {
  font-size: 12px;
  color: #909399;
}

.dialog-footer {
  text-align: right;
}
</style>