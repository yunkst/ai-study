<template>
  <div class="practice-container">
    <div class="practice-header">
      <h1>智能练习</h1>
      <p>输入主题，让 AI 为你生成练习题</p>
    </div>
    
    <el-form :model="form" inline class="practice-form" @submit.prevent="generateQuestion">
      <el-form-item label="主题">
        <el-input v-model="form.topic" placeholder="例如：算法" />
      </el-form-item>
      <el-form-item label="难度">
        <el-select v-model="form.difficulty" style="width: 120px">
          <el-option v-for="n in 5" :key="n" :label="n" :value="n" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="generateQuestion" :loading="loading">生成题目</el-button>
      </el-form-item>
    </el-form>
    
    <el-card v-if="question" class="question-card" shadow="hover">
      <template #header>
        <span>练习题</span>
      </template>
      <p>{{ question }}</p>
      <el-input
        v-model="answer"
        type="textarea"
        rows="4"
        placeholder="输入你的答案..."
      />
      <template #footer>
        <el-button type="success" @click="submitAnswer">提交答案</el-button>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

interface PracticeForm {
  topic: string
  difficulty: number
}

const form = ref<PracticeForm>({ topic: '', difficulty: 3 })
const question = ref('')
const answer = ref('')
const loading = ref(false)

// 已移除占位题目生成函数

const generateQuestion = async () => {
  if (!form.value.topic) {
    ElMessage.warning('请先输入主题')
    return
  }
  loading.value = true
  try {
    const resp = await fetch('/api/practice/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    if (resp.ok) {
      const data = await resp.json()
      question.value = data.question
    } else {
      ElMessage.error('题目生成失败')
      question.value = ''
    }
  } catch (e) {
    ElMessage.error('题目生成失败')
    question.value = ''
  } finally {
    loading.value = false
  }
}

const submitAnswer = () => {
  ElMessage.success('答案已提交，稍后将为您提供解析！')
}
</script>

<style lang="scss" scoped>
.practice-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.practice-header {
  text-align: center;
  color: white;
  margin-bottom: 40px;
  
  h1 {
    font-size: 32px;
    margin-bottom: 12px;
  }
 
  p {
    font-size: 16px;
    opacity: 0.8;
  }
}

.practice-form {
  max-width: 600px;
  margin: 0 auto 30px;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
}

.question-card {
  max-width: 600px;
  margin: 0 auto;
}
</style> 