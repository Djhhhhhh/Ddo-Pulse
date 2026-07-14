<template>
  <div class="report-detail-page">
    <header class="page-header">
      <button class="btn-back" @click="goBack">← 返回列表</button>
      <h1>📊 报告详情</h1>
      <span class="timestamp">{{ timestamp }}</span>
    </header>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="fetchReport" class="btn-retry">重试</button>
    </div>

    <div v-else class="report-content">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="tabs">
          <button
            :class="['tab', activeTab === 'html' ? 'active' : '']"
            @click="activeTab = 'html'"
          >
            🌐 HTML 预览
          </button>
          <button
            :class="['tab', activeTab === 'md' ? 'active' : '']"
            @click="activeTab = 'md'"
          >
            📝 Markdown
          </button>
          <button
            v-if="report?.images?.length"
            :class="['tab', activeTab === 'images' ? 'active' : '']"
            @click="activeTab = 'images'"
          >
            🖼️ 图片 ({{ report.images.length }})
          </button>
        </div>
        <div class="actions">
          <button class="btn-action" @click="downloadFile('html')" :disabled="!report?.html_content">
            ⬇️ 下载 HTML
          </button>
          <button class="btn-action" @click="downloadFile('md')" :disabled="!report?.md_content">
            ⬇️ 下载 MD
          </button>
          <button class="btn-action btn-fullscreen" @click="fullscreen">
            ⛶ 全屏
          </button>
        </div>
      </div>

      <!-- HTML 预览 -->
      <div v-if="activeTab === 'html'" class="preview-container">
        <iframe
          ref="iframeRef"
          :srcdoc="report?.html_content"
          class="html-preview"
          frameborder="0"
        ></iframe>
      </div>

      <!-- Markdown 预览 -->
      <div v-if="activeTab === 'md'" class="md-preview">
        <div class="md-content" v-html="renderedMarkdown"></div>
      </div>

      <!-- 图片列表 -->
      <div v-if="activeTab === 'images'" class="images-grid">
        <div
          v-for="(image, index) in report?.images"
          :key="image"
          class="image-card"
        >
          <img
            :src="`/api/reports/${timestamp}/images/${image}`"
            :alt="`Page ${index + 1}`"
            @click="viewImage(image)"
          />
          <span class="image-name">{{ image }}</span>
        </div>
      </div>
    </div>

    <!-- 图片查看器 -->
    <div v-if="viewingImage" class="image-viewer" @click="viewingImage = null">
      <img :src="`/api/reports/${timestamp}/images/${viewingImage}`" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

interface Report {
  timestamp: string
  md_content: string | null
  html_content: string | null
  images: string[]
}

const router = useRouter()
const route = useRoute()
const timestamp = computed(() => route.params.timestamp as string)

const report = ref<Report | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const activeTab = ref<'html' | 'md' | 'images'>('html')
const viewingImage = ref<string | null>(null)
const iframeRef = ref<HTMLIFrameElement | null>(null)

const renderedMarkdown = computed(() => {
  if (!report.value?.md_content) return ''
  // 简单的 Markdown 渲染
  return report.value.md_content
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/!\[(.*?)\]\((.*?)\)/g, '<img alt="$1" src="$2" />')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/\n/g, '<br />')
})

async function fetchReport() {
  loading.value = true
  error.value = null

  try {
    const res = await fetch(`/api/reports/${timestamp.value}`)
    if (!res.ok) throw new Error('Report not found')
    report.value = await res.json()
  } catch (e) {
    error.value = '加载报告失败'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/reports')
}

function downloadFile(type: 'html' | 'md') {
  const content = type === 'html' ? report.value?.html_content : report.value?.md_content
  if (!content) return

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `digest-${timestamp.value}.${type === 'html' ? 'html' : 'md'}`
  a.click()
  URL.revokeObjectURL(url)
}

function fullscreen() {
  const iframe = iframeRef.value
  if (iframe) {
    if (iframe.requestFullscreen) {
      iframe.requestFullscreen()
    }
  }
}

function viewImage(image: string) {
  viewingImage.value = image
}

onMounted(fetchReport)
</script>

<style scoped>
.report-detail-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.btn-back {
  padding: 8px 16px;
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #e0e0e0;
  color: #333;
}

.page-header h1 {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.timestamp {
  font-family: monospace;
  background: #f0f0f0;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
  color: #666;
}

.loading, .error {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: #e74c3c;
}

.btn-retry {
  margin-top: 15px;
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.tabs {
  display: flex;
  gap: 10px;
}

.tab {
  padding: 10px 20px;
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.tab:hover {
  background: #e0e0e0;
}

.tab.active {
  background: #667eea;
  color: white;
}

.actions {
  display: flex;
  gap: 10px;
}

.btn-action {
  padding: 10px 16px;
  background: white;
  border: 2px solid #667eea;
  border-radius: 6px;
  cursor: pointer;
  color: #667eea;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-action:hover:not(:disabled) {
  background: #667eea;
  color: white;
}

.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-fullscreen {
  background: #667eea;
  color: white;
}

.preview-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.html-preview {
  width: 100%;
  height: 80vh;
  border: none;
}

.md-preview {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 30px;
}

.md-content {
  line-height: 1.8;
  color: #333;
}

.md-content :deep(h1) {
  font-size: 28px;
  margin: 20px 0 15px;
  color: #667eea;
}

.md-content :deep(h2) {
  font-size: 22px;
  margin: 18px 0 12px;
  color: #333;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 8px;
}

.md-content :deep(h3) {
  font-size: 18px;
  margin: 15px 0 10px;
  color: #667eea;
}

.md-content :deep(a) {
  color: #667eea;
  text-decoration: none;
}

.md-content :deep(a:hover) {
  text-decoration: underline;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.image-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}

.image-card:hover {
  transform: translateY(-4px);
}

.image-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.image-name {
  display: block;
  padding: 10px;
  text-align: center;
  font-size: 14px;
  color: #666;
}

.image-viewer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  cursor: pointer;
}

.image-viewer img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}
</style>
