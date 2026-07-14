<template>
  <div class="reports-page">
    <header class="page-header">
      <h1>📊 报告列表</h1>
      <p class="subtitle">查看每日精选报告</p>
    </header>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
      <button @click="fetchReports" class="btn-retry">重试</button>
    </div>

    <div v-else-if="reports.length === 0" class="empty">
      <p>📭 暂无报告</p>
      <p class="hint">运行 pipeline 后将自动生成报告</p>
    </div>

    <div v-else class="reports-grid">
      <div
        v-for="report in reports"
        :key="report.timestamp"
        class="report-card"
        @click="viewReport(report.timestamp)"
      >
        <div class="card-header">
          <span class="timestamp">{{ report.timestamp }}</span>
          <span class="date">{{ formatDate(report.timestamp) }}</span>
        </div>
        <div class="card-body">
          <div class="stats">
            <div class="stat">
              <span class="stat-icon">📝</span>
              <span class="stat-label">MD</span>
              <span :class="['stat-value', report.has_md ? 'has' : 'no']">
                {{ report.has_md ? '✓' : '✗' }}
              </span>
            </div>
            <div class="stat">
              <span class="stat-icon">🌐</span>
              <span class="stat-label">HTML</span>
              <span :class="['stat-value', report.has_html ? 'has' : 'no']">
                {{ report.has_html ? '✓' : '✗' }}
              </span>
            </div>
            <div class="stat">
              <span class="stat-icon">🖼️</span>
              <span class="stat-label">图片</span>
              <span class="stat-value">{{ report.image_count }}</span>
            </div>
          </div>
        </div>
        <div class="card-footer">
          <button class="btn-view">查看报告 →</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

interface Report {
  timestamp: string
  has_md: boolean
  has_html: boolean
  image_count: number
}

const router = useRouter()
const reports = ref<Report[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function fetchReports() {
  loading.value = true
  error.value = null

  try {
    const res = await fetch('/api/reports')
    if (!res.ok) throw new Error('Failed to fetch reports')
    const data = await res.json()
    reports.value = data.reports || []
  } catch (e) {
    error.value = '加载报告失败，请检查服务是否启动'
    console.error(e)
  } finally {
    loading.value = false
  }
}

function viewReport(timestamp: string) {
  router.push(`/reports/${timestamp}`)
}

function formatDate(timestamp: string): string {
  // 从 2026-07-14-083000 格式解析
  const parts = timestamp.split('-')
  if (parts.length >= 4) {
    const date = parts.slice(0, 3).join('-')
    const time = parts[3].replace(/(\d{2})(\d{2})(\d{2})/, '$1:$2:$3')
    return `${date} ${time}`
  }
  return timestamp
}

onMounted(fetchReports)
</script>

<style scoped>
.reports-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  color: #333;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #666;
  margin: 0;
}

.loading, .error, .empty {
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

.btn-retry:hover {
  background: #5a6fd6;
}

.hint {
  font-size: 14px;
  color: #999;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.report-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.report-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
}

.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timestamp {
  font-size: 14px;
  font-family: monospace;
}

.date {
  font-size: 12px;
  opacity: 0.9;
}

.card-body {
  padding: 20px;
}

.stats {
  display: flex;
  justify-content: space-around;
}

.stat {
  text-align: center;
}

.stat-icon {
  display: block;
  font-size: 20px;
  margin-bottom: 5px;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 3px;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
}

.stat-value.has {
  color: #27ae60;
}

.stat-value.no {
  color: #e74c3c;
}

.card-footer {
  padding: 15px 20px;
  border-top: 1px solid #f0f0f0;
}

.btn-view {
  width: 100%;
  padding: 10px;
  background: transparent;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-view:hover {
  background: #667eea;
  color: white;
}
</style>
