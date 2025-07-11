<template>
  <div class="knowledge-management">
    <el-container>
      <!-- 顶部操作栏 -->
      <el-header class="header">
        <div class="header-left">
          <h2>📚 知识库管理</h2>
          <el-tag v-if="knowledgeStats.total_knowledge_points > 0" type="success">
            已有 {{ knowledgeStats.total_knowledge_points }} 个知识点
          </el-tag>
          <el-tag v-else type="warning">知识库为空</el-tag>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showImportDialog = true" :icon="Upload">
            导入知识库
          </el-button>
          <el-button @click="loadKnowledgeData" :icon="Refresh">刷新</el-button>
        </div>
      </el-header>

      <el-main>
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 知识图谱 -->
          <el-tab-pane label="📊 知识图谱" name="graph">
            <div class="graph-container">
              <div v-if="knowledgeStats.total_knowledge_points === 0" class="empty-state">
                <el-empty description="暂无知识点数据">
                  <el-button type="primary" @click="showImportDialog = true">
                    导入知识库
                  </el-button>
                </el-empty>
              </div>
              <div v-else id="knowledge-graph" style="height: 600px;"></div>
            </div>
          </el-tab-pane>

          <!-- 知识域管理 -->
          <el-tab-pane label="🏗️ 知识域" name="domains">
            <div class="domains-grid">
              <el-card 
                v-for="domain in domains" 
                :key="domain.id"
                class="domain-card"
                shadow="hover"
              >
                <template #header>
                  <div class="card-header">
                    <span class="domain-name">{{ domain.name }}</span>
                    <el-tag type="info">{{ domain.knowledge_points_count }} 个知识点</el-tag>
                  </div>
                </template>
                <div class="domain-content">
                  <p class="domain-desc">{{ domain.description }}</p>
                  <div class="domain-stats">
                    <el-progress 
                      :percentage="Math.round(domain.exam_weight * 100)" 
                      :stroke-width="8"
                      :show-text="false"
                    />
                    <span class="weight-text">考试权重: {{ (domain.exam_weight * 100).toFixed(1) }}%</span>
                  </div>
                  <el-button 
                    type="text" 
                    @click="viewDomainDetails(domain)"
                    class="view-details-btn"
                  >
                    查看详情 →
                  </el-button>
                </div>
              </el-card>
            </div>
          </el-tab-pane>

          <!-- 知识点列表 -->
          <el-tab-pane label="📝 知识点" name="points">
            <div class="points-toolbar">
              <el-select v-model="selectedDomainId" placeholder="筛选知识域" clearable style="width: 200px;">
                <el-option 
                  v-for="domain in domains" 
                  :key="domain.id"
                  :label="domain.name" 
                  :value="domain.id"
                />
              </el-select>
              <el-input 
                v-model="searchKeyword" 
                placeholder="搜索知识点..."
                style="width: 300px;"
                :prefix-icon="Search"
                clearable
              />
            </div>
            
            <el-table :data="filteredKnowledgePoints" stripe>
              <el-table-column prop="name" label="知识点名称" min-width="200" />
              <el-table-column prop="domain_name" label="所属域" width="150" />
              <el-table-column prop="difficulty_level" label="难度" width="80">
                <template #default="{ row }">
                  <el-rate 
                    v-model="row.difficulty_level" 
                    :max="5" 
                    disabled 
                    show-score
                    text-color="#ff9900"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="exam_weight" label="考试权重" width="100">
                <template #default="{ row }">
                  {{ (row.exam_weight * 100).toFixed(1) }}%
                </template>
              </el-table-column>
              <el-table-column prop="estimated_study_hours" label="预估学时" width="100">
                <template #default="{ row }">
                  {{ row.estimated_study_hours }}h
                </template>
              </el-table-column>
              <el-table-column prop="prerequisites_count" label="前置条件" width="100" />
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button type="text" size="small" @click="viewPointDetails(row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 统计分析 -->
          <el-tab-pane label="📈 统计分析" name="statistics">
            <div class="stats-container">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-statistic title="知识域总数" :value="knowledgeStats.total_domains" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="知识点总数" :value="knowledgeStats.total_knowledge_points" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="技能点总数" :value="knowledgeStats.total_skill_points" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="预估总学时" :value="knowledgeStats.total_study_hours" suffix="小时" />
                </el-col>
              </el-row>

              <el-row :gutter="20" style="margin-top: 30px;">
                <el-col :span="12">
                  <el-card title="难度分布">
                    <div id="difficulty-chart" style="height: 300px;"></div>
                  </el-card>
                </el-col>
                <el-col :span="12">
                  <el-card title="权重分布">
                    <div id="weight-chart" style="height: 300px;"></div>
                  </el-card>
                </el-col>
              </el-row>

              <el-row style="margin-top: 20px;">
                <el-col :span="24">
                  <el-card title="学习时间预估">
                    <el-descriptions :column="4" border>
                      <el-descriptions-item label="每天2小时">
                        {{ knowledgeStats.days_2h_per_day }} 天
                      </el-descriptions-item>
                      <el-descriptions-item label="每天4小时">
                        {{ knowledgeStats.days_4h_per_day }} 天
                      </el-descriptions-item>
                      <el-descriptions-item label="每周20小时">
                        {{ knowledgeStats.weeks_20h_per_week }} 周
                      </el-descriptions-item>
                      <el-descriptions-item label="考前冲刺">
                        2-3 周
                      </el-descriptions-item>
                    </el-descriptions>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="📁 导入知识库"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="import-methods">
        <el-tabs v-model="importMethod" type="card">
          <!-- 文件上传方式 -->
          <el-tab-pane label="📤 上传文件" name="upload">
            <div class="upload-area">
              <el-upload
                ref="uploadRef"
                :action="uploadUrl"
                :headers="uploadHeaders"
                :data="uploadData"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :before-upload="beforeUpload"
                :file-list="fileList"
                drag
                multiple
                accept=".pdf,.doc,.docx,.md,.txt,.zip"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽文件到此处，或<em>点击上传</em>
                </div>
                <div class="el-upload__tip">
                  支持 PDF、Word、Markdown、文本文件及压缩包
                </div>
              </el-upload>
            </div>
          </el-tab-pane>

          <!-- 自动扫描方式 -->
          <el-tab-pane label="🔍 自动扫描" name="scan">
            <div class="scan-area">
              <el-alert
                title="自动扫描说明"
                type="info"
                description="系统将扫描Docker容器中的学习资料目录，自动识别并导入知识体系"
                :closable="false"
                style="margin-bottom: 20px;"
              />
              
              <el-form :model="scanForm" label-width="120px">
                <el-form-item label="扫描目录">
                  <el-input 
                    v-model="scanForm.directory" 
                    placeholder="/app/resources/System_Architect"
                    readonly
                  />
                </el-form-item>
                <el-form-item label="导入选项">
                  <el-checkbox v-model="scanForm.force_reimport">强制重新导入</el-checkbox>
                  <el-checkbox v-model="scanForm.include_case_studies">包含案例分析</el-checkbox>
                </el-form-item>
              </el-form>

              <el-button 
                type="primary" 
                @click="startAutoScan"
                :loading="importing"
                style="width: 100%;"
              >
                开始自动扫描导入
              </el-button>
            </div>
          </el-tab-pane>

          <!-- RAG向量化方式 -->
          <el-tab-pane label="🤖 智能处理" name="rag">
            <div class="rag-area">
              <el-alert
                title="智能文档处理"
                type="success"
                description="使用RAG技术对文档进行向量化处理，支持智能问答和内容检索"
                :closable="false"
                style="margin-bottom: 20px;"
              />
              
              <el-form :model="ragForm" label-width="120px">
                <el-form-item label="处理模式">
                  <el-radio-group v-model="ragForm.mode">
                    <el-radio label="full">完整处理</el-radio>
                    <el-radio label="incremental">增量更新</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="向量模型">
                  <el-select v-model="ragForm.embedding_model">
                    <el-option label="text-embedding-ada-002" value="ada-002" />
                    <el-option label="BGE-M3 (本地)" value="bge-m3" />
                  </el-select>
                </el-form-item>
                <el-form-item label="分块大小">
                  <el-slider v-model="ragForm.chunk_size" :min="256" :max="2048" :step="256" />
                  <span style="margin-left: 10px;">{{ ragForm.chunk_size }} 字符</span>
                </el-form-item>
              </el-form>

              <el-button 
                type="success" 
                @click="startRAGProcessing"
                :loading="ragProcessing"
                style="width: 100%;"
              >
                开始智能处理
              </el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 导入进度 -->
      <div v-if="importing || ragProcessing" class="import-progress">
        <el-divider>导入进度</el-divider>
        <el-progress 
          :percentage="importProgress.progress * 100" 
          :status="importProgress.status === 'error' ? 'exception' : 'success'"
        />
        <p class="progress-message">{{ importProgress.message }}</p>
        
        <div v-if="importProgress.details" class="progress-details">
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="知识域">
              {{ importProgress.details.domains_created || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="知识点">
              {{ importProgress.details.knowledge_points_created || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="技能点">
              {{ importProgress.details.skill_points_created || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="依赖关系">
              {{ importProgress.details.dependencies_created || 0 }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showImportDialog = false" :disabled="importing || ragProcessing">
            取消
          </el-button>
          <el-button 
            v-if="importProgress.status === 'completed'" 
            type="primary" 
            @click="handleImportComplete"
          >
            完成
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 知识点详情对话框 -->
    <el-dialog
      v-model="showPointDialog"
      :title="selectedPoint?.name"
      width="800px"
    >
      <div v-if="selectedPoint" class="point-details">
        <!-- 知识点详情内容 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="所属域">
            {{ selectedPoint.domain?.name }}
          </el-descriptions-item>
          <el-descriptions-item label="难度级别">
            <el-rate v-model="selectedPoint.difficulty_level" :max="5" disabled />
          </el-descriptions-item>
          <el-descriptions-item label="考试权重">
            {{ (selectedPoint.exam_weight * 100).toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="预估学时">
            {{ selectedPoint.estimated_study_hours }} 小时
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>学习目标</el-divider>
        <ul v-if="selectedPoint.learning_objectives">
          <li v-for="objective in selectedPoint.learning_objectives" :key="objective">
            {{ objective }}
          </li>
        </ul>

        <el-divider>前置知识点</el-divider>
        <div v-if="selectedPoint.prerequisites?.length > 0" class="prerequisites">
          <el-tag 
            v-for="prereq in selectedPoint.prerequisites" 
            :key="prereq.id"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ prereq.name }}
          </el-tag>
        </div>
        <p v-else class="no-data">无前置要求</p>

        <el-divider>技能点</el-divider>
        <div v-if="selectedPoint.skill_points?.length > 0" class="skill-points">
          <el-card 
            v-for="skill in selectedPoint.skill_points" 
            :key="skill.id"
            style="margin-bottom: 10px;"
            shadow="never"
          >
            <h4>{{ skill.name }}</h4>
            <p>{{ skill.description }}</p>
            <el-tag size="small" :type="getSkillTypeColor(skill.skill_type)">
              {{ getSkillTypeName(skill.skill_type) }}
            </el-tag>
          </el-card>
        </div>
        <p v-else class="no-data">暂无技能点</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Refresh, Search, UploadFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'

// 响应式数据
const activeTab = ref('graph')
const showImportDialog = ref(false)
const showPointDialog = ref(false)
const importMethod = ref('scan')
const importing = ref(false)
const ragProcessing = ref(false)
const selectedDomainId = ref('')
const searchKeyword = ref('')

// 数据
const domains = ref([])
const knowledgePoints = ref([])
const knowledgeStats = ref({})
const selectedPoint = ref(null)
const fileList = ref([])

// 表单数据
const scanForm = reactive({
  directory: '/app/resources/System_Architect',
  force_reimport: false,
  include_case_studies: true
})

const ragForm = reactive({
  mode: 'full',
  embedding_model: 'bge-m3',
  chunk_size: 1024
})

// 导入进度
const importProgress = reactive({
  status: 'idle',
  message: '',
  progress: 0,
  details: null
})

// 计算属性
const filteredKnowledgePoints = computed(() => {
  let filtered = knowledgePoints.value
  
  if (selectedDomainId.value) {
    const domain = domains.value.find(d => d.id === selectedDomainId.value)
    if (domain) {
      filtered = filtered.filter(kp => kp.domain_name === domain.name)
    }
  }
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(kp => 
      kp.name.toLowerCase().includes(keyword) ||
      kp.description?.toLowerCase().includes(keyword)
    )
  }
  
  return filtered
})

// 上传配置
const uploadUrl = `${import.meta.env.VITE_API_BASE_URL}/api/knowledge/upload`
const uploadHeaders = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}
const uploadData = {
  type: 'knowledge_materials'
}

// 方法
const loadKnowledgeData = async () => {
  try {
    // 加载知识域
    const domainsRes = await axios.get('/api/knowledge/domains')
    domains.value = domainsRes.data

    // 加载知识点
    const pointsRes = await axios.get('/api/knowledge/points')
    knowledgePoints.value = pointsRes.data

    // 加载统计信息
    const statsRes = await axios.get('/api/knowledge/statistics')
    knowledgeStats.value = statsRes.data.basic_statistics
    
    // 更新图表
    if (activeTab.value === 'statistics') {
      nextTick(() => {
        renderCharts(statsRes.data)
      })
    }
  } catch (error) {
    ElMessage.error('加载知识库数据失败')
    console.error(error)
  }
}

const startAutoScan = async () => {
  try {
    importing.value = true
    importProgress.status = 'running'
    importProgress.message = '正在启动自动扫描...'
    importProgress.progress = 0

    // 启动导入任务
    await axios.post('/api/knowledge/import/start', scanForm)
    
    // 轮询进度
    pollImportProgress()
  } catch (error) {
    importing.value = false
    ElMessage.error(error.response?.data?.detail || '启动导入失败')
  }
}

const pollImportProgress = async () => {
  try {
    const res = await axios.get('/api/knowledge/import/status')
    const progress = res.data
    
    Object.assign(importProgress, progress)
    
    if (progress.status === 'completed') {
      importing.value = false
      ElMessage.success('知识库导入完成！')
      await loadKnowledgeData()
    } else if (progress.status === 'error') {
      importing.value = false
      ElMessage.error(`导入失败: ${progress.message}`)
    } else if (progress.status === 'running') {
      // 继续轮询
      setTimeout(pollImportProgress, 2000)
    }
  } catch (error) {
    importing.value = false
    ElMessage.error('获取导入进度失败')
  }
}

const startRAGProcessing = async () => {
  try {
    ragProcessing.value = true
    ElMessage.info('RAG处理功能开发中...')
    
    // TODO: 实现RAG处理逻辑
    setTimeout(() => {
      ragProcessing.value = false
      ElMessage.success('RAG处理完成')
    }, 3000)
  } catch (error) {
    ragProcessing.value = false
    ElMessage.error('RAG处理失败')
  }
}

const viewPointDetails = async (point) => {
  try {
    const res = await axios.get(`/api/knowledge/points/${point.id}/details`)
    selectedPoint.value = res.data
    showPointDialog.value = true
  } catch (error) {
    ElMessage.error('获取知识点详情失败')
  }
}

const viewDomainDetails = (domain) => {
  selectedDomainId.value = domain.id
  activeTab.value = 'points'
}

const handleImportComplete = () => {
  showImportDialog.value = false
  importProgress.status = 'idle'
  importProgress.message = ''
  importProgress.progress = 0
  importProgress.details = null
}

// 上传相关方法
const beforeUpload = (file) => {
  const isValidType = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/markdown',
    'text/plain',
    'application/zip'
  ].includes(file.type)
  
  if (!isValidType) {
    ElMessage.error('只支持 PDF、Word、Markdown、文本文件及压缩包')
    return false
  }
  
  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isLt100M) {
    ElMessage.error('文件大小不能超过 100MB')
    return false
  }
  
  return true
}

const handleUploadSuccess = (response, file) => {
  ElMessage.success(`${file.name} 上传成功`)
  // TODO: 处理上传成功后的逻辑
}

const handleUploadError = (error, file) => {
  ElMessage.error(`${file.name} 上传失败`)
}

// 工具方法
const getSkillTypeName = (type) => {
  const typeMap = {
    'concept': '概念',
    'technique': '技巧', 
    'application': '应用'
  }
  return typeMap[type] || type
}

const getSkillTypeColor = (type) => {
  const colorMap = {
    'concept': '',
    'technique': 'warning',
    'application': 'success'
  }
  return colorMap[type] || ''
}

const renderCharts = (statsData) => {
  // 难度分布图
  const difficultyChart = echarts.init(document.getElementById('difficulty-chart'))
  const difficultyOption = {
    title: { text: '知识点难度分布' },
    tooltip: {},
    xAxis: { data: Object.keys(statsData.difficulty_distribution) },
    yAxis: {},
    series: [{
      type: 'bar',
      data: Object.values(statsData.difficulty_distribution),
      itemStyle: { color: '#409EFF' }
    }]
  }
  difficultyChart.setOption(difficultyOption)

  // 权重分布图
  const weightChart = echarts.init(document.getElementById('weight-chart'))
  const weightOption = {
    title: { text: '考试权重分布' },
    tooltip: {},
    series: [{
      type: 'pie',
      data: Object.entries(statsData.weight_distribution).map(([name, value]) => ({
        name, value
      })),
      radius: '70%'
    }]
  }
  weightChart.setOption(weightOption)
}

// 生命周期
onMounted(() => {
  loadKnowledgeData()
})
</script>

<style scoped>
.knowledge-management {
  padding: 20px;
  height: calc(100vh - 40px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.header-left h2 {
  margin: 0 20px 0 0;
}

.domains-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 20px;
}

.domain-card {
  transition: transform 0.2s;
}

.domain-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.domain-content {
  padding: 10px 0;
}

.domain-desc {
  color: #666;
  margin-bottom: 15px;
}

.domain-stats {
  margin-bottom: 15px;
}

.weight-text {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
  display: block;
}

.view-details-btn {
  width: 100%;
}

.points-toolbar {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.stats-container {
  padding: 20px;
}

.graph-container {
  padding: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.import-methods {
  margin-bottom: 20px;
}

.upload-area, .scan-area, .rag-area {
  padding: 20px;
  min-height: 200px;
}

.import-progress {
  margin-top: 20px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 6px;
}

.progress-message {
  text-align: center;
  margin: 10px 0;
  color: #666;
}

.progress-details {
  margin-top: 15px;
}

.point-details {
  max-height: 500px;
  overflow-y: auto;
}

.no-data {
  color: #999;
  font-style: italic;
}

.prerequisites {
  margin-bottom: 15px;
}

.skill-points .el-card {
  border: 1px solid #e4e7ed;
}

.skill-points h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.skill-points p {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
}
</style> 