<template>
  <el-container class="container">
    <el-aside width="340px" class="sidebar">
      <el-card shadow="hover" class="sidebar-card">
        <div class="section">
          <div class="section-title">文档目录</div>
          <el-input v-model="documentsPath" placeholder="例如: ./documents" clearable />
          <el-button type="primary" class="mt-4" @click="buildIndex">构建知识库</el-button>
          <div v-if="buildResult" class="mt-2 text-muted">{{ buildResult }}</div>
        </div>

        <el-divider />

        <div class="section">
          <div class="section-title">模型提供者</div>
          <el-select v-model="provider" placeholder="选择模型提供者" style="width:100%">
            <el-option label="后端默认" value=""></el-option>
            <el-option label="OpenAI" value="openai"></el-option>
            <el-option label="Gemini" value="gemini"></el-option>
            <el-option label="Ollama (本地)" value="ollama"></el-option>
          </el-select>

          <div v-if="provider === 'ollama'" class="ollama-config mt-3">
            <div class="sub-label">Ollama 模型</div>
            <el-input v-model="ollamaModel" placeholder="例如: gemma3:4b" clearable />
            <div class="sub-label mt-2">Ollama API URL</div>
            <el-input v-model="ollamaApiUrl" placeholder="例如: http://localhost:11434" clearable />
          </div>
        </div>

        <el-divider />

        <div class="section">
          <div class="status"><strong>状态:</strong> {{ status.vector_store_loaded ? '已加载' : '未加载' }}</div>
        </div>
      </el-card>
    </el-aside>

    <el-container class="main">
      <el-main>
        <el-card class="chat-card">
          <div class="chat">
            <div class="messages">
              <div v-for="(m, i) in messages" :key="i" :class="['message', m.role]">
                <div class="meta">
                  <div class="avatar" :class="m.role">{{ m.role === 'user' ? '你' : '助' }}</div>
                  <div class="role">{{ m.role }}</div>
                </div>
                <div class="content">{{ m.content }}</div>
                <div v-if="m.sources" class="sources">
                  <el-collapse>
                    <el-collapse-item title="参考来源 ({{ m.sources.length }})" name="1">
                      <ul>
                        <li v-for="(s, idx) in m.sources" :key="idx">{{ s.source }} - {{ s.preview }}</li>
                      </ul>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </div>

            <div class="input-area">
              <el-input v-model="question" placeholder="请输入问题，回车发送" class="flex-1" @keyup.enter.native="sendQuestion" />
              <el-button type="primary" @click="sendQuestion">发送</el-button>
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

export default {
  data() {
    return {
      question: '',
      messages: [],
      status: { vector_store_loaded: false },
      documentsPath: './documents',
        provider: '',
        ollamaModel: '',
        ollamaApiUrl: '',
      buildResult: null,
    }
  },
  mounted() {
    // set global light theme by default to match requested white background
    try {
      document.documentElement.setAttribute('data-theme', 'light')
    } catch (e) {
      // ignore if not available
    }
    this.fetchStatus()
  },
  methods: {
    async fetchStatus() {
      try {
        const res = await axios.get(`${API_BASE}/status`)
        this.status = res.data
      } catch (e) {
        console.error(e)
      }
    },
    async buildIndex() {
      this.buildResult = '构建中...'
      try {
        const res = await axios.post(`${API_BASE}/build`, { documents_path: this.documentsPath })
        if (res.data.success) {
          this.buildResult = `构建成功: ${res.data.processed_chunks} 个片段`
          await this.fetchStatus()
        } else {
          this.buildResult = `构建失败: ${res.data.message}`
        }
      } catch (e) {
        this.buildResult = `错误: ${e.message}`
      }
    },
    async sendQuestion() {
      if (!this.question.trim()) return
      const q = this.question.trim()
      this.messages.push({ role: 'user', content: q })
      this.question = ''

      try {
        const payload = { question: q }
        if (this.provider && this.provider.trim()) payload.provider = this.provider.trim()
        if (this.provider === 'ollama') {
          if (this.ollamaModel && this.ollamaModel.trim()) payload.ollama_model = this.ollamaModel.trim()
          if (this.ollamaApiUrl && this.ollamaApiUrl.trim()) payload.ollama_api_url = this.ollamaApiUrl.trim()
        }

        const res = await axios.post(`${API_BASE}/query`, payload)
        const ans = res.data.answer
        const sources = res.data.sources || []
        this.messages.push({ role: 'assistant', content: ans, sources })
      } catch (e) {
        const err = e.response?.data?.detail || e.message
        this.messages.push({ role: 'assistant', content: `错误: ${err}` })
      }
    }
  }
}
</script>

<style>
@import './styles.css';
</style>
