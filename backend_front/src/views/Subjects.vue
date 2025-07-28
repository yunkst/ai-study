<template>
  <div class="subjects-page">
    <div class="page-header">
      <h3>学科管理</h3>
      <div class="header-actions">
        <el-button 
          v-if="selectedSubjects.length > 0" 
          type="danger" 
          @click="batchDeleteSubjects"
          :loading="batchDeleting"
        >
          <el-icon><delete /></el-icon>
          批量删除 ({{ selectedSubjects.length }})
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><plus /></el-icon>
          新增学科
        </el-button>
      </div>
    </div>

    <el-card>
      <el-table 
        :data="subjects" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="学科名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editSubject(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteSubject(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEdit ? '编辑学科' : '新增学科'"
      width="400px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item label="学科名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入学科名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入学科描述"
          />
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
import { ElMessage, ElMessageBox, type FormInstance, type MessageParamsWithType } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { subjectApi, type Subject } from '../services/api'

const loading = ref(false)
const submitting = ref(false)
const batchDeleting = ref(false)
const showCreateDialog = ref(false)
const isEdit = ref(false)
const subjects = ref<Subject[]>([])
const selectedSubjects = ref<Subject[]>([])
const formRef = ref<FormInstance>()

const form = reactive({
  id: 0,
  name: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入学科名称', trigger: 'blur' }]
}

// 获取学科列表
const fetchSubjects = async () => {
  loading.value = true
  try {
    subjects.value = await subjectApi.getSubjects()
  } catch (error: unknown) {
    console.error('获取学科列表失败:', error)
    // 错误处理已在HTTP服务中统一处理
  } finally {
    loading.value = false
  }
}

// 编辑学科
const editSubject = (subject: Subject) => {
  isEdit.value = true
  form.id = subject.id
  form.name = subject.name
  form.description = subject.description || ''
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
          name: form.name,
          description: form.description
        }
        
        if (isEdit.value) {
          await subjectApi.updateSubject(form.id, data)
          ElMessage.success('学科更新成功' as MessageParamsWithType)
        } else {
          await subjectApi.createSubject(data)
          ElMessage.success('学科创建成功' as MessageParamsWithType)
        }
        
        showCreateDialog.value = false
        fetchSubjects()
      } catch (error: unknown) {
        console.error('操作失败:', error)
        // 错误处理已在HTTP服务中统一处理
      } finally {
        submitting.value = false
      }
    }
  })
}

// 删除学科
const deleteSubject = async (subject: Subject) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除学科 "${subject.name}" 吗？\n\n⚠️ 警告：删除学科将会同时删除该学科下的所有题目和题库，此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    )
    
    const result = await subjectApi.deleteSubject(subject.id)
    // 显示删除结果信息
    if (result && typeof result === 'object' && 'deleted_questions' in result) {
      ElMessage.success(`删除成功！已删除 ${result.deleted_questions} 道题目和 ${result.deleted_question_banks} 个题库` as MessageParamsWithType)
    } else {
      ElMessage.success('删除成功' as MessageParamsWithType)
    }
    fetchSubjects()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      // 错误处理已在HTTP服务中统一处理
    }
  }
}

// 处理选择变化
const handleSelectionChange = (selection: Subject[]) => {
  selectedSubjects.value = selection
}

// 批量删除学科
const batchDeleteSubjects = async () => {
  if (selectedSubjects.value.length === 0) {
    ElMessage.warning('请选择要删除的学科' as MessageParamsWithType)
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedSubjects.value.length} 个学科吗？\n\n⚠️ 警告：删除学科将会同时删除这些学科下的所有题目和题库，此操作不可恢复！`,
      '确认批量删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    )
    
    batchDeleting.value = true
    const subjects = [...selectedSubjects.value]
    let totalDeletedQuestions = 0
    let totalDeletedQuestionBanks = 0
    
    // 逐个删除学科（因为批量删除API暂未实现）
    for (const subject of subjects) {
      const result = await subjectApi.deleteSubject(subject.id)
      if (result && typeof result === 'object' && 'deleted_questions' in result) {
        totalDeletedQuestions += result.deleted_questions || 0
        totalDeletedQuestionBanks += result.deleted_question_banks || 0
      }
    }
    
    ElMessage.success(`成功删除 ${subjects.length} 个学科，${totalDeletedQuestions} 道题目，${totalDeletedQuestionBanks} 个题库` as MessageParamsWithType)
    selectedSubjects.value = []
    fetchSubjects()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      // 错误处理已在HTTP服务中统一处理
    }
  } finally {
    batchDeleting.value = false
  }
}

// 重置表单
const resetForm = () => {
  isEdit.value = false
  form.id = 0
  form.name = ''
  form.description = ''
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchSubjects()
})
</script>

<style scoped>
.subjects-page {
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
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>