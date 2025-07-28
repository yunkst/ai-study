<template>
  <div class="filter-section">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-form-item label="学科筛选">
          <el-select
            :model-value="props.modelValue.subject_id"
            placeholder="学科筛选"
            clearable
            @update:model-value="(val: string | number) => emit('update:modelValue', { ...props.modelValue, subject_id: val })"
            @change="handleFilterChange"
          >
            <el-option label="全部学科" value="" />
            <el-option
              v-for="subject in subjects"
              :key="subject.id"
              :label="subject.name"
              :value="subject.id"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="6">
        <el-form-item label="状态筛选">
          <el-select
            :model-value="props.modelValue.status"
            placeholder="状态筛选"
            clearable
            @update:model-value="(val: string) => emit('update:modelValue', { ...props.modelValue, status: val })"
            @change="handleFilterChange"
          >
            <el-option label="全部状态" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="搜索">
          <el-input
            :model-value="props.modelValue.keyword"
            placeholder="搜索"
            clearable
            @update:model-value="(val: string) => emit('update:modelValue', { ...props.modelValue, keyword: val })"
            @input="handleFilterChange"
          >
            <template #prefix>
              <el-icon><search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
      </el-col>
      <el-col :span="4">
        <el-button @click="resetFilter">重置</el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'

interface Subject {
  id: number
  name: string
  description?: string
  created_at: string
}

interface FilterForm {
  subject_id: string | number
  status: string
  keyword: string
}

const props = defineProps<{
  subjects: Subject[]
  modelValue: FilterForm
}>()

const emit = defineEmits<{
  'update:modelValue': [value: FilterForm]
  'filter-change': []
}>()

// 过滤变化处理
const handleFilterChange = () => {
  emit('filter-change')
}

const resetFilter = () => {
  const newValue = {
    subject_id: '',
    status: '',
    keyword: ''
  }
  emit('update:modelValue', newValue)
  emit('filter-change')
}
</script>

<style scoped>
.filter-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}
</style>