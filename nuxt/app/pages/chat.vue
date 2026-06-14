<template>
  <div class="chat-page">
    <div class="chat-messages" ref="messagesRef">
      <div v-if="messages.length === 0" class="chat-empty">
        <MessageOutlined style="font-size: 48px; color: #d9d9d9" />
        <p>Ask me anything about your data</p>
      </div>
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="chat-message"
        :class="[msg.role, msg.content === 'Thinking...' ? 'thinking' : '']"
      >
        <div class="chat-bubble">{{ msg.content }}</div>
      </div>
    </div>
    <div class="chat-input-bar">
      <a-input
        v-model:value="inputText"
        placeholder="Type your question..."
        size="large"
        :disabled="!connected"
        @keydown.enter.prevent="sendMessage"
      >
        <template #prefix>
          <a-badge :status="connected ? 'success' : 'error'" />
        </template>
      </a-input>
      <a-button type="primary" :disabled="!connected || !inputText.trim()" @click="sendMessage">
        Send
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { MessageOutlined } from '@ant-design/icons-vue'

definePageMeta({ middleware: 'auth' })

const config = useRuntimeConfig()
const authStore = useAuthStore()

const messages = ref<{ role: string; content: string }[]>([])
const inputText = ref('')
const connected = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
let socket: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let reconnectAttempts = 0

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function connect() {
  const wsUrl = config.public.wsUrl.replace(/^http/, 'ws') + '/ws/chat'
  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    connected.value = true
    reconnectAttempts = 0
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.content === 'Thinking...') {
      const last = messages.value[messages.value.length - 1]
      if (last?.content === 'Thinking...') return
    }
    messages.value.push(data)
    scrollToBottom()
  }

  socket.onclose = () => {
    connected.value = false
    scheduleReconnect()
  }

  socket.onerror = () => {
    socket?.close()
  }
}

function scheduleReconnect() {
  if (reconnectAttempts >= 5) return
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000)
  reconnectAttempts++
  reconnectTimer = setTimeout(connect, delay)
}

function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !socket || socket.readyState !== WebSocket.OPEN) return
  socket.send(JSON.stringify({ content: text }))
  inputText.value = ''
}

onMounted(connect)

onUnmounted(() => {
  if (reconnectTimer) clearTimeout(reconnectTimer)
  socket?.close()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
  max-width: 800px;
  margin: 0 auto;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fff;
  border-radius: 8px 8px 0 0;
  border: 1px solid #f0f0f0;
  border-bottom: none;
}
.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: #999;
}
.chat-message {
  margin-bottom: 16px;
  display: flex;
}
.chat-message.user {
  justify-content: flex-end;
}
.chat-message.user .chat-bubble {
  background: #1890ff;
  color: #fff;
  border-radius: 12px 12px 4px 12px;
}
.chat-message.assistant .chat-bubble {
  background: #f0f0f0;
  color: #333;
  border-radius: 12px 12px 12px 4px;
}
.chat-message.thinking .chat-bubble {
  background: transparent;
  color: #999;
  font-style: italic;
}
.chat-bubble {
  max-width: 70%;
  padding: 10px 16px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}
.chat-input-bar {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 0 0 8px 8px;
}
.chat-input-bar :deep(.ant-input) {
  border-radius: 6px;
}
</style>
