<template>
  <div class="podcast-container">
    <div class="podcast-header">
      <h1>AI 播客</h1>
      <p>输入主题，生成个性化播客片段</p>
    </div>
    
    <el-form :model="form" inline class="podcast-form" @submit.prevent="generatePodcast">
      <el-form-item label="主题">
        <el-input v-model="form.topic" placeholder="例如：微服务架构" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="generatePodcast" :loading="loading">生成播客</el-button>
      </el-form-item>
    </el-form>
    
    <el-card v-if="audioUrl" class="podcast-card" shadow="hover">
      <template #header>
        <span>播客片段</span>
      </template>
      <audio :src="audioUrl" controls style="width: 100%" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const form = ref({ topic: '' })
const audioUrl = ref('')
const loading = ref(false)

const generatePodcast = async () => {
  if (!form.value.topic) {
    ElMessage.warning('请先输入主题')
    return
  }
  loading.value = true
  try {
    const resp = await fetch('/api/podcast/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    if (resp.ok) {
      const data = await resp.json()
      audioUrl.value = data.url
    } else {
      ElMessage.error('播客生成失败')
      audioUrl.value = ''
    }
  } catch (e) {
    ElMessage.error('播客生成失败')
    audioUrl.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.podcast-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.podcast-header {
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

.podcast-form {
  max-width: 600px;
  margin: 0 auto 30px;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
}

.podcast-card {
  max-width: 600px;
  margin: 0 auto;
}
</style> 