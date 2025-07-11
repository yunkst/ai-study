<template>
  <div class="ai-config-container">
    <div class="header">
      <h1>AI 配置管理</h1>
      <p>管理AI供应商、密钥和服务配置</p>
    </div>

    <!-- 当前服务状态 -->
    <el-card class="service-status-card">
      <template #header>
        <div class="card-header">
          <span>当前服务状态</span>
          <el-button @click="refreshStatus" :loading="loading" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <div class="service-grid">
        <div class="service-item">
          <div class="service-title">
            <el-icon><ChatDotSquare /></el-icon>
            大语言模型 (LLM)
          </div>
          <div class="service-info">
            <el-tag v-if="currentConfig.llm_service" type="success">
              {{ currentConfig.llm_service.provider_name }} / {{ currentConfig.llm_service.model_name }}
            </el-tag>
            <el-tag v-else type="info">未配置</el-tag>
          </div>
        </div>
        
        <div class="service-item">
          <div class="service-title">
            <el-icon><Connection /></el-icon>
            嵌入服务 (Embedding)
          </div>
          <div class="service-info">
            <el-tag v-if="currentConfig.embedding_service" type="success">
              {{ currentConfig.embedding_service.provider_name }} / {{ currentConfig.embedding_service.model_name }}
            </el-tag>
            <el-tag v-else type="info">未配置</el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <!-- AI供应商管理 -->
    <el-card class="providers-card">
      <template #header>
        <div class="card-header">
          <span>AI 供应商</span>
          <el-button @click="showAddProvider = true" type="primary" size="small">
            <el-icon><Plus /></el-icon>
            添加供应商
          </el-button>
        </div>
      </template>

      <el-table :data="providers" style="width: 100%">
        <el-table-column prop="display_name" label="名称" width="150" />
        <el-table-column prop="name" label="标识" width="100" />
        <el-table-column prop="provider_type" label="类型" width="100">
          <template #default="scope">
            <el-tag size="small">{{ scope.row.provider_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="API地址" />
        <el-table-column prop="is_local" label="本地服务" width="100">
          <template #default="scope">
            <el-icon v-if="scope.row.is_local" color="green"><Check /></el-icon>
            <el-icon v-else color="gray"><Close /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.is_enabled" type="success" size="small">启用</el-tag>
            <el-tag v-else type="info" size="small">禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button @click="setApiKey(scope.row)" size="small">密钥</el-button>
            <el-button @click="testProvider(scope.row)" size="small" type="warning">测试</el-button>
            <el-button @click="activateService(scope.row)" size="small" type="success">激活</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 设置API密钥对话框 -->
    <el-dialog v-model="showApiKeyDialog" title="设置API密钥" width="400px">
      <el-form :model="apiKeyForm" label-width="80px">
        <el-form-item label="供应商">
          <el-input v-model="apiKeyForm.provider_name" disabled />
        </el-form-item>
        <el-form-item label="API密钥">
          <el-input 
            v-model="apiKeyForm.api_key" 
            type="password" 
            show-password 
            placeholder="请输入API密钥"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showApiKeyDialog = false">取消</el-button>
        <el-button @click="saveApiKey" type="primary" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 激活服务对话框 -->
    <el-dialog v-model="showActivateDialog" title="激活AI服务" width="400px">
      <el-form :model="activateForm" label-width="80px">
        <el-form-item label="供应商">
          <el-input v-model="activateForm.provider_name" disabled />
        </el-form-item>
        <el-form-item label="服务类型">
          <el-select v-model="activateForm.service_type" style="width: 100%">
            <el-option label="大语言模型 (LLM)" value="llm" />
            <el-option label="嵌入服务 (Embedding)" value="embedding" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="activateForm.model_name" style="width: 100%">
            <el-option 
              v-for="model in selectedProviderModels"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showActivateDialog = false">取消</el-button>
        <el-button @click="saveActivateService" type="primary" :loading="saving">激活</el-button>
      </template>
    </el-dialog>

    <!-- Ollama状态卡片 -->
    <el-card v-if="ollamaStatus" class="ollama-card">
      <template #header>
        <div class="card-header">
          <span>Ollama 本地服务</span>
          <el-tag :type="ollamaStatus.is_running ? 'success' : 'danger'">
            {{ ollamaStatus.is_running ? '运行中' : '未运行' }}
          </el-tag>
        </div>
      </template>
      
      <div v-if="ollamaStatus.is_running">
        <p><strong>版本：</strong>{{ ollamaStatus.version }}</p>
        <p><strong>地址：</strong>{{ ollamaStatus.base_url }}</p>
        <p><strong>可用模型：</strong></p>
        <div class="ollama-models">
          <el-tag 
            v-for="model in ollamaStatus.available_models" 
            :key="model.name"
            style="margin: 2px"
          >
            {{ model.name }}
          </el-tag>
        </div>
      </div>
      <div v-else>
        <p>Ollama服务未运行，请先启动Ollama服务</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, ChatDotSquare, Connection, Check, Close } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const providers = ref([])
const currentConfig = ref({})
const ollamaStatus = ref(null)

// 对话框显示状态
const showApiKeyDialog = ref(false)
const showActivateDialog = ref(false)
const showAddProvider = ref(false)

// 表单数据
const apiKeyForm = reactive({
  provider_name: '',
  api_key: ''
})

const activateForm = reactive({
  provider_name: '',
  service_type: 'llm',
  model_name: ''
})

// 计算属性
const selectedProviderModels = computed(() => {
  if (!activateForm.provider_name) return []
  const provider = providers.value.find(p => p.name === activateForm.provider_name)
  return provider ? provider.supported_models : []
})

// 方法
const loadData = async () => {
  loading.value = true
  try {
    // 加载供应商列表
    const providersRes = await adminApi.getAiProviders()
    providers.value = providersRes.data || []
    
    // 加载当前配置
    const configRes = await adminApi.getAiConfig()
    currentConfig.value = configRes.data || {}
    
    // 加载Ollama状态
    try {
      const ollamaRes = await adminApi.getOllamaStatus()
      ollamaStatus.value = ollamaRes.data
    } catch (e) {
      console.warn('获取Ollama状态失败:', e)
    }
    
  } catch (error) {
    ElMessage.error('加载数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const refreshStatus = () => {
  loadData()
}

const setApiKey = (provider) => {
  apiKeyForm.provider_name = provider.name
  apiKeyForm.api_key = ''
  showApiKeyDialog.value = true
}

const saveApiKey = async () => {
  if (!apiKeyForm.api_key.trim()) {
    ElMessage.warning('请输入API密钥')
    return
  }
  
  saving.value = true
  try {
    await adminApi.setApiKey(apiKeyForm.provider_name, {
      provider_name: apiKeyForm.provider_name,
      api_key: apiKeyForm.api_key
    })
    
    ElMessage.success('API密钥设置成功')
    showApiKeyDialog.value = false
  } catch (error) {
    ElMessage.error('设置API密钥失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const testProvider = async (provider) => {
  loading.value = true
  try {
    const result = await adminApi.testAiProvider(provider.name)
    
    if (result.data.success) {
      ElMessage.success(`${provider.display_name} 连接测试成功`)
    } else {
      ElMessage.error(`${provider.display_name} 连接测试失败: ${result.data.message}`)
    }
  } catch (error) {
    ElMessage.error('测试连接失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const activateService = (provider) => {
  activateForm.provider_name = provider.name
  activateForm.service_type = 'llm'
  activateForm.model_name = provider.supported_models[0] || ''
  showActivateDialog.value = true
}

const saveActivateService = async () => {
  if (!activateForm.model_name) {
    ElMessage.warning('请选择模型')
    return
  }
  
  saving.value = true
  try {
    await adminApi.activateAiService(
      activateForm.service_type,
      activateForm.provider_name,
      activateForm.model_name
    )
    
    ElMessage.success('AI服务激活成功')
    showActivateDialog.value = false
    await loadData() // 重新加载配置
  } catch (error) {
    ElMessage.error('激活服务失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.ai-config-container {
  padding: 20px;
  max-width: 1200px;
}

.header {
  margin-bottom: 20px;
}

.header h1 {
  margin: 0 0 10px 0;
  color: #303133;
}

.header p {
  margin: 0;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.service-status-card,
.providers-card,
.ollama-card {
  margin-bottom: 20px;
}

.service-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.service-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fafafa;
}

.service-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 8px;
}

.service-info {
  margin-left: 24px;
}

.ollama-models {
  margin-top: 8px;
}

@media (max-width: 768px) {
  .service-grid {
    grid-template-columns: 1fr;
  }
}
</style> 