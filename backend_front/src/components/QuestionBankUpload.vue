<template>
  <el-dialog
    v-model="visible"
    title="上传题库"
    width="600px"
    @close="handleClose"
  >
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
          placeholder="请输入题库描述"
          :rows="3"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      <el-form-item label="所属学科" prop="subject_id">
        <el-select
          v-model="uploadForm.subject_id"
          placeholder="请选择学科"
          style="width: 100%"
        >
          <el-option
            v-for="subject in subjects"
            :key="subject.id"
            :label="subject.name"
            :value="subject.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="题库文件" prop="file">
        <el-upload
          ref="uploadRef"
          v-model:file-list="fileList"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          accept=".json,.xlsx,.xls"
          drag
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 JSON、Excel 格式文件，文件大小不超过 10MB
            </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          @click="handleUpload"
        >
          {{ uploading ? '上传中...' : '确定上传' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, type FormInstance, type UploadFile, type MessageParamsWithType } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { questionBankApi, type Subject } from '../services/api'

interface UploadForm {
  name: string
  description: string
  subject_id: number
  file: File | null
}

const props = defineProps<{
  modelValue: boolean
  subjects: Subject[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'upload-success': []
}>()

const visible = ref(props.modelValue)
const uploading = ref(false)
const uploadFormRef = ref<FormInstance>()
const uploadRef = ref()
const fileList = ref<UploadFile[]>([])

const uploadForm = reactive<UploadForm>({
  name: '',
  description: '',
  subject_id: 0,
  file: null
})

const uploadRules = {
  name: [{ required: true, message: '请输入题库名称', trigger: 'blur' }],
  subject_id: [{ required: true, message: '请选择学科', trigger: 'change' }],
  file: [{ required: true, message: '请选择题库文件', trigger: 'change' }]
}

watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    // 检查文件大小
    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.raw.size > maxSize) {
      ElMessage.error('文件大小不能超过 10MB' as MessageParamsWithType)
      fileList.value = []
      uploadForm.file = null
      return
    }
    
    uploadForm.file = file.raw
  }
}

const handleFileRemove = () => {
  uploadForm.file = null
}

const handleUpload = async () => {
  if (!uploadFormRef.value) return
  
  try {
    await uploadFormRef.value.validate()
    
    uploading.value = true
    
    const formData = new FormData()
    formData.append('name', uploadForm.name)
    formData.append('description', uploadForm.description)
    formData.append('subject_id', uploadForm.subject_id.toString())
    if (uploadForm.file) {
      formData.append('file', uploadForm.file)
    }
    
    await questionBankApi.uploadQuestionBank({
      name: uploadForm.name,
      description: uploadForm.description,
      subject_id: uploadForm.subject_id!,
      file: uploadForm.file!
    })
    
    ElMessage.success('题库上传成功' as MessageParamsWithType)
    emit('upload-success')
    handleClose()
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('题库上传失败' as MessageParamsWithType)
  } finally {
    uploading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  // 重置表单
  uploadForm.name = ''
  uploadForm.description = ''
  uploadForm.subject_id = 0
  uploadForm.file = null
  fileList.value = []
  uploadFormRef.value?.resetFields()
}
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}

.el-upload__tip {
  color: #999;
  font-size: 12px;
}
</style>