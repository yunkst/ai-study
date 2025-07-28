<template>
  <el-dialog
    v-model="visible"
    title="题库详情"
    width="800px"
    @close="handleClose"
  >
    <div v-if="questionBank" class="detail-content">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="题库名称">
          {{ questionBank.name }}
        </el-descriptions-item>
        <el-descriptions-item label="文件名">
          {{ questionBank.file_name }}
        </el-descriptions-item>
        <el-descriptions-item label="所属学科">
          {{ questionBank.subject?.name || '未分类' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(questionBank.status)">
            {{ getStatusText(questionBank.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="总题目数">
          {{ questionBank.total_questions }}
        </el-descriptions-item>
        <el-descriptions-item label="已导入题目数">
          {{ questionBank.imported_questions }}
        </el-descriptions-item>
        <el-descriptions-item label="导入进度">
          <el-progress
            :percentage="getImportProgress(questionBank)"
            :color="getProgressColor(questionBank)"
            :stroke-width="8"
          />
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(questionBank.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间" v-if="questionBank.updated_at">
          {{ formatDate(questionBank.updated_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2" v-if="questionBank.description">
          {{ questionBank.description }}
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="questionBank.error_message">
          <el-alert
            :title="questionBank.error_message"
            type="error"
            :closable="false"
            show-icon
          />
        </el-descriptions-item>
      </el-descriptions>

      <!-- 操作按钮 -->
      <div class="detail-actions">
        <el-button
          v-if="questionBank.status === 'completed'"
          type="primary"
          @click="viewQuestions"
        >
          查看题目
        </el-button>
        <el-button
          v-if="questionBank.status === 'failed'"
          type="warning"
          @click="retryImport"
        >
          重新导入
        </el-button>
        <el-button
          type="danger"
          @click="deleteQuestionBank"
        >
          删除题库
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type MessageParamsWithType } from 'element-plus'
import { useRouter } from 'vue-router'
import { questionBankApi, type QuestionBank } from '../services/api'

const props = defineProps<{
  modelValue: boolean
  questionBank: QuestionBank | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'delete-success': []
  'retry-success': []
}>()

const router = useRouter()
const visible = ref(props.modelValue)

watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

const getImportProgress = (questionBank: QuestionBank): number => {
  if (questionBank.total_questions === 0) return 0
  return Math.round((questionBank.imported_questions / questionBank.total_questions) * 100)
}

const getProgressColor = (questionBank: QuestionBank): string => {
  const progress = getImportProgress(questionBank)
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

const viewQuestions = () => {
  if (props.questionBank) {
    router.push({
      name: 'Questions',
      query: { question_bank_id: props.questionBank.id }
    })
    handleClose()
  }
}

const retryImport = async () => {
  if (!props.questionBank) return
  
  try {
    await ElMessageBox.confirm(
      '确定要重新导入这个题库吗？',
      '确认重新导入',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await questionBankApi.retryImport(props.questionBank.id)
    ElMessage.success('重新导入请求已提交' as MessageParamsWithType)
    emit('retry-success')
    handleClose()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      ElMessage.error('重新导入失败' as MessageParamsWithType)
    }
  }
}

const deleteQuestionBank = async () => {
  if (!props.questionBank) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除题库 "${props.questionBank.name}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await questionBankApi.deleteQuestionBank(props.questionBank.id)
    ElMessage.success('删除成功' as MessageParamsWithType)
    emit('delete-success')
    handleClose()
  } catch (error: unknown) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败' as MessageParamsWithType)
    }
  }
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.detail-content {
  padding: 20px 0;
}

.detail-actions {
  margin-top: 30px;
  text-align: center;
}

.detail-actions .el-button {
  margin: 0 10px;
}

.dialog-footer {
  text-align: right;
}
</style>