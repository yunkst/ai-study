<template>
  <div class="questions">
    <div class="page-header">
      <h3>题目管理</h3>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><plus /></el-icon>
        新增题目
      </el-button>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="学科">
          <el-select v-model="filters.subject_id" placeholder="选择学科" clearable>
            <el-option
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.name"
              :value="subject.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="题目类型">
          <el-select v-model="filters.question_type" placeholder="选择类型" clearable>
            <el-option label="单选题" value="single_choice" />
            <el-option label="多选题" value="multiple_choice" />
            <el-option label="判断题" value="true_false" />
            <el-option label="填空题" value="fill_blank" />
            <el-option label="简答题" value="short_answer" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchQuestions">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 题目列表 -->
    <el-card>
      <el-table :data="questions" v-loading="loading">
        <el-table-column prop="title" label="题目标题" width="200" />
        <el-table-column prop="subject.name" label="学科" width="120" />
        <el-table-column prop="question_type" label="类型" width="120">
          <template #default="{ row }">
            {{ getQuestionTypeText(row.question_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="difficulty" label="难度" width="100">
          <template #default="{ row }">
            <el-tag :type="getDifficultyType(row.difficulty)" size="small">
              {{ getDifficultyText(row.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="题目内容" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editQuestion(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteQuestion(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchQuestions"
          @current-change="fetchQuestions"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEdit ? '编辑题目' : '新增题目'"
      width="800px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="学科" prop="subject_id">
          <el-select v-model="form.subject_id" placeholder="选择学科">
            <el-option
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.name"
              :value="subject.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="题目标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入题目标题" />
        </el-form-item>
        <el-form-item label="题目内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="请输入题目内容"
          />
        </el-form-item>
        <el-form-item label="题目类型" prop="question_type">
          <el-select v-model="form.question_type" placeholder="选择题目类型">
            <el-option label="单选题" value="single_choice" />
            <el-option label="多选题" value="multiple_choice" />
            <el-option label="判断题" value="true_false" />
            <el-option label="填空题" value="fill_blank" />
            <el-option label="简答题" value="short_answer" />
          </el-select>
        </el-form-item>
        <el-form-item label="选项" v-if="['single_choice', 'multiple_choice'].includes(form.question_type)">
          <div v-for="(_option, index) in form.options" :key="index" class="option-item">
            <el-input
              v-model="form.options[index]"
              :placeholder="`选项 ${String.fromCharCode(65 + index)}`"
            />
            <el-button
              v-if="form.options.length > 2"
              type="danger"
              size="small"
              @click="removeOption(index)"
            >
              删除
            </el-button>
          </div>
          <el-button type="primary" size="small" @click="addOption">添加选项</el-button>
        </el-form-item>
        <el-form-item label="正确答案" prop="correct_answer">
          <el-input
            v-model="form.correct_answer"
            placeholder="请输入正确答案"
          />
        </el-form-item>
        <el-form-item label="解析" prop="explanation">
          <el-input
            v-model="form.explanation"
            type="textarea"
            :rows="3"
            placeholder="请输入题目解析"
          />
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-select v-model="form.difficulty" placeholder="选择难度">
            <el-option label="简单" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="困难" value="hard" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="请输入标签，多个标签用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import axios from 'axios'

interface Subject {
  id: number
  name: string
}

interface Question {
  id: number
  title: string
  content: string
  question_type: string
  options: string[]
  correct_answer: string
  explanation: string
  difficulty: string
  tags: string
  subject: Subject
  created_at: string
}

const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const isEdit = ref(false)
const questions = ref<Question[]>([])
const subjects = ref<Subject[]>([])
const formRef = ref<FormInstance>()

const filters = reactive({
  subject_id: '',
  question_type: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const form = reactive({
  id: 0,
  subject_id: '',
  title: '',
  content: '',
  question_type: '',
  options: ['', ''],
  correct_answer: '',
  explanation: '',
  difficulty: '',
  tags: ''
})

const rules = {
  subject_id: [{ required: true, message: '请选择学科', trigger: 'change' }],
  title: [{ required: true, message: '请输入题目标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入题目内容', trigger: 'blur' }],
  question_type: [{ required: true, message: '请选择题目类型', trigger: 'change' }],
  correct_answer: [{ required: true, message: '请输入正确答案', trigger: 'blur' }],
  difficulty: [{ required: true, message: '请选择难度', trigger: 'change' }]
}

// 获取学科列表
const fetchSubjects = async () => {
  try {
    const response = await axios.get('/api/v1/questions/subjects')
    subjects.value = response.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取学科列表失败')
  }
}

// 获取题目列表
const fetchQuestions = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filters
    }
    const response = await axios.get('/api/v1/questions/', { params })
    questions.value = response.data.items
    pagination.total = response.data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取题目列表失败')
  } finally {
    loading.value = false
  }
}

// 重置筛选条件
const resetFilters = () => {
  filters.subject_id = ''
  filters.question_type = ''
  pagination.page = 1
  fetchQuestions()
}

// 添加选项
const addOption = () => {
  form.options.push('')
}

// 删除选项
const removeOption = (index: number) => {
  form.options.splice(index, 1)
}

// 编辑题目
const editQuestion = (question: Question) => {
  isEdit.value = true
  form.id = question.id
  form.subject_id = question.subject.id.toString()
  form.title = question.title
  form.content = question.content
  form.question_type = question.question_type
  form.options = question.options.length > 0 ? [...question.options] : ['', '']
  form.correct_answer = question.correct_answer
  form.explanation = question.explanation
  form.difficulty = question.difficulty
  form.tags = question.tags
  showCreateDialog.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = {
          subject_id: form.subject_id,
          title: form.title,
          content: form.content,
          question_type: form.question_type,
          options: ['single_choice', 'multiple_choice'].includes(form.question_type) 
            ? form.options.filter(opt => opt.trim()) : [],
          correct_answer: form.correct_answer,
          explanation: form.explanation,
          difficulty: form.difficulty,
          tags: form.tags
        }
        
        if (isEdit.value) {
          await axios.put(`/api/v1/questions/${form.id}`, data)
          ElMessage.success('题目更新成功')
        } else {
          await axios.post('/api/v1/questions/', data)
          ElMessage.success('题目创建成功')
        }
        
        showCreateDialog.value = false
        fetchQuestions()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 删除题目
const deleteQuestion = async (question: Question) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除题目 "${question.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/v1/questions/${question.id}`)
    ElMessage.success('删除成功')
    fetchQuestions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 重置表单
const resetForm = () => {
  isEdit.value = false
  form.id = 0
  form.subject_id = ''
  form.title = ''
  form.content = ''
  form.question_type = ''
  form.options = ['', '']
  form.correct_answer = ''
  form.explanation = ''
  form.difficulty = ''
  form.tags = ''
}

// 获取题目类型文本
const getQuestionTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    single_choice: '单选题',
    multiple_choice: '多选题',
    true_false: '判断题',
    fill_blank: '填空题',
    short_answer: '简答题'
  }
  return typeMap[type] || type
}

// 获取难度类型
const getDifficultyType = (difficulty: string) => {
  const difficultyMap: Record<string, string> = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger'
  }
  return difficultyMap[difficulty] || 'info'
}

// 获取难度文本
const getDifficultyText = (difficulty: string) => {
  const difficultyMap: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return difficultyMap[difficulty] || difficulty
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchSubjects()
  fetchQuestions()
})
</script>

<style scoped>
.questions {
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

.filter-card {
  margin-bottom: 20px;
}

.option-item {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}

.option-item .el-input {
  flex: 1;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>