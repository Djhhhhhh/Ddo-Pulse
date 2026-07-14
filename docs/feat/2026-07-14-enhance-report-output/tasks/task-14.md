# Task 14: 前端报告页面

## 关联验收点
- G8: 前端报告预览

## 任务描述
创建前端报告预览页面。

## 具体步骤

1. 创建 `services/web/frontend/src/views/Reports.vue`：
   - 报告列表展示
   - 点击进入预览

2. 创建 `services/web/frontend/src/components/ReportViewer.vue`：
   - iframe 加载 HTML 报告
   - 全屏预览
   - 下载按钮

3. 更新路由配置

## 输出文件
- `services/web/frontend/src/views/Reports.vue`
- `services/web/frontend/src/components/ReportViewer.vue`

## Reports.vue 设计
```vue
<template>
  <div class="reports-page">
    <h1>报告列表</h1>
    <div class="report-list">
      <div v-for="report in reports" :key="report.timestamp" class="report-card">
        <h3>{{ report.timestamp }}</h3>
        <p>MD: {{ report.has_md ? '✅' : '❌' }}</p>
        <p>HTML: {{ report.has_html ? '✅' : '❌' }}</p>
        <p>图片: {{ report.image_count }} 张</p>
        <router-link :to="`/reports/${report.timestamp}`">查看</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const reports = ref([])

onMounted(async () => {
  const res = await fetch('/api/reports')
  const data = await res.json()
  reports.value = data.reports
})
</script>
```

## ReportViewer.vue 设计
```vue
<template>
  <div class="report-viewer">
    <div class="toolbar">
      <button @click="fullscreen">全屏</button>
      <button @click="download('md')">下载 MD</button>
      <button @click="download('html')">下载 HTML</button>
    </div>
    <iframe :src="htmlUrl" frameborder="0"></iframe>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps(['timestamp'])
const htmlUrl = computed(() => `/api/reports/${props.timestamp}/html`)

function fullscreen() {
  document.querySelector('iframe').requestFullscreen()
}

function download(type) {
  window.open(`/api/reports/${props.timestamp}/${type}`, '_blank')
}
</script>
```

## 验证命令
```bash
# 启动 dev server 后访问
curl -s http://localhost:5173/reports || echo "Frontend not running"
```
