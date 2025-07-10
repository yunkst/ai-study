<template>
  <div class="auth-container">
    <div class="auth-form">
      <div class="auth-header">
        <h1 class="auth-title">访问验证</h1>
        <p class="auth-subtitle">请输入访问密钥以使用系统功能</p>
      </div>

      <el-form 
        :model="form" 
        :rules="rules" 
        ref="formRef"
        @submit.prevent="handleSubmit"
        size="large"
      >
        <el-form-item prop="accessKey">
          <el-input
            v-model="form.accessKey"
            type="password"
            placeholder="请输入访问密钥"
            show-password
            :disabled="loading"
            @keyup.enter="handleSubmit"
          >
            <template #prefix>
              <el-icon><Key /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading"
            @click="handleSubmit"
            style="width: 100%"
          >
            {{ loading ? '验证中...' : '验证访问' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        <el-button 
          type="text" 
          @click="skipAuth"
          v-if="!authStore.requiresKey"
        >
          跳过验证
        </el-button>
        
        <p class="auth-hint">
          <el-icon><InfoFilled /></el-icon>
          如果没有访问密钥，请联系管理员获取
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { Key, InfoFilled } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = reactive({
  accessKey: ''
})

// 验证规则
const rules: FormRules = {
  accessKey: [
    { required: true, message: '请输入访问密钥', trigger: 'blur' }
  ]
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const success = await authStore.verifyAccessKey(form.accessKey)
    
    if (success) {
      // 验证成功，跳转到目标页面或首页
      const redirect = route.query.redirect as string || '/'
      router.replace(redirect)
    }
  } catch (error) {
    console.error('验证失败:', error)
  } finally {
    loading.value = false
  }
}

// 跳过验证
const skipAuth = () => {
  const redirect = route.query.redirect as string || '/'
  router.replace(redirect)
}
</script>

<style lang="scss" scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-form {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 16px;
  padding: 40px 32px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  
  @media (max-width: 768px) {
    padding: 32px 24px;
    margin: 20px;
  }
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
  
  .auth-title {
    font-size: 24px;
    font-weight: 600;
    color: #333;
    margin-bottom: 8px;
  }
  
  .auth-subtitle {
    color: #666;
    font-size: 14px;
    margin: 0;
  }
}

.auth-footer {
  margin-top: 24px;
  text-align: center;
  
  .auth-hint {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-top: 16px;
    color: #999;
    font-size: 12px;
    margin-bottom: 0;
  }
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-input__wrapper) {
  padding: 12px 15px;
  border-radius: 8px;
}

:deep(.el-button) {
  height: 44px;
  border-radius: 8px;
  font-weight: 500;
}
</style> 