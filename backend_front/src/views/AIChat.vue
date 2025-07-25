<template>
  <div class="ai-chat">
    <div class="page-header">
      <h3>AI对话</h3>
    </div>

    <el-card class="chat-container">
      <div class="chat-messages" ref="messagesContainer">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message', message.role]"
        >
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.content)"></div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
        <div v-if="isLoading" class="message assistant">
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="请输入您的问题..."
          @keydown.ctrl.enter="sendMessage"
          :disabled="isLoading"
        />
        <div class="input-actions">
          <span class="input-tip">Ctrl + Enter 发送</span>
          <el-button
            type="primary"
            :loading="isLoading"
            @click="sendMessage"
            :disabled="!inputMessage.trim()"
          >
            发送
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement>()
let messageId = 0

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  const userMessage: Message = {
    id: ++messageId,
    role: 'user',
    content: inputMessage.value.trim(),
    timestamp: new Date()
  }
  
  messages.value.push(userMessage)
  const currentInput = inputMessage.value
  inputMessage.value = ''
  
  await scrollToBottom()
  
  isLoading.value = true
  
  try {
    const response = await axios.post('/api/v1/ai/chat', {
      message: currentInput,
      conversation_id: null // 可以实现会话管理
    })
    
    const assistantMessage: Message = {
      id: ++messageId,
      role: 'assistant',
      content: response.data.response,
      timestamp: new Date()
    }
    
    messages.value.push(assistantMessage)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'AI服务暂时不可用')
    
    const errorMessage: Message = {
      id: ++messageId,
      role: 'assistant',
      content: '抱歉，AI服务暂时不可用，请稍后再试。',
      timestamp: new Date()
    }
    
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化消息内容
const formatMessage = (content: string) => {
  // 简单的 Markdown 支持
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

// 格式化时间
const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化欢迎消息
const initWelcomeMessage = () => {
  const welcomeMessage: Message = {
    id: ++messageId,
    role: 'assistant',
    content: '您好！我是AI学习助手，可以帮助您解答学习相关的问题。请随时向我提问！',
    timestamp: new Date()
  }
  messages.value.push(welcomeMessage)
}

onMounted(() => {
  initWelcomeMessage()
})
</script>

<style scoped>
.ai-chat {
  padding: 20px;
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h3 {
  margin: 0;
  color: #333;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 20px;
  max-height: calc(100vh - 300px);
}

.message {
  margin-bottom: 20px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message.assistant .message-content {
  background: white;
  color: #333;
  border: 1px solid #e4e7ed;
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.message.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-time {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 5px;
  text-align: right;
}

.message.assistant .message-time {
  text-align: left;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.chat-input {
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.input-tip {
  font-size: 12px;
  color: #909399;
}
</style>