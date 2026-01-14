<template>
  <div class="portrait-container fade-in">
    <div class="header-section">
      <div class="title-group">
        <div class="decoration-line"></div>
        <h2 class="gufeng-title">历史事件群像</h2>
        <span class="sub-title">Historical Event Portrait</span>
      </div>
      <el-button color="#8e3e3e" class="gufeng-btn" @click="refreshCurrent" :loading="loading" plain>
        <template #icon><el-icon><Refresh /></el-icon></template> 重演
      </el-button>
    </div>

    <div class="main-layout">
      <div class="dimension-sidebar glass-effect">
        <div v-for="tab in tabs" :key="tab.id"
             class="nav-item" :class="{ active: currentTab === tab.id }"
             @click="switchTab(tab.id)">
          <el-icon class="nav-icon"><component :is="tab.icon" /></el-icon>
          <span>{{ tab.name }}</span>
        </div>
      </div>

      <div class="content-area custom-scrollbar" v-loading="loading">

        <div v-if="currentTab === 'causal'" class="view-panel">
          <div class="panel-title">因果演化网络</div>
          <div v-if="causalData" class="chart-col">
            <div class="chart-card glass-effect h-350">
              <div class="chart-header">历史关键路径推推演</div>
              <div ref="causalChainRef" class="echart-main"></div>
            </div>
            <div class="chart-card glass-effect h-500">
              <div class="chart-header">因果演化图谱</div>
              <div ref="causalNetworkRef" class="echart-main"></div>
            </div>
          </div>
          <el-empty v-else description="点击重演加载数据" />
        </div>

        <div v-if="currentTab === 'type'" class="view-panel">
          <div class="panel-header">
            <div class="panel-title">事件语义聚类</div>
            <div class="download-group" v-if="typeData && typeData.files">
              <el-button-group>
                <el-button size="small" @click="viewImage(typeData.files.image)">
                  <el-icon><Picture /></el-icon> 查看图片
                </el-button>
                <el-button size="small" @click="downloadFile(typeData.files.csv, 'event_type_data.csv')">
                  <el-icon><Document /></el-icon> 下载数据
                </el-button>
              </el-button-group>
            </div>
          </div>
          <div v-if="typeData" class="chart-col">
            <div class="stats-row">
              <div class="mini-card glass-effect">
                <span>总类别数</span><strong class="gold">{{ typeData.stats.total_types }}</strong>
              </div>
              <div class="mini-card glass-effect">
                <span>聚类评分</span><strong class="blue">{{ typeData.stats.silhouette.toFixed(2) }}</strong>
              </div>
            </div>
            <div class="chart-card glass-effect h-500">
              <div class="chart-header">事件类型PCA分布</div>
              <div ref="typeScatterRef" class="echart-main"></div>
            </div>
          </div>
        </div>

        <div v-if="currentTab === 'location'" class="view-panel">
          <div class="panel-header">
            <div class="panel-title">地理空间分析</div>
            <div class="download-group" v-if="locData && locData.files">
              <el-button-group>
                <el-button size="small" @click="downloadFile(locData.files.csv, 'location_data.csv')">
                  <el-icon><Document /></el-icon> 下载数据
                </el-button>
              </el-button-group>
            </div>
          </div>
          <div v-if="locData" class="chart-col">
            <div class="chart-row">
              <div class="chart-card glass-effect h-400">
                <div class="chart-header">高频地点 TOP15</div>
                <div ref="locBarRef" class="echart-main"></div>
              </div>
              <div class="chart-card glass-effect h-400">
                <div class="chart-header">地点角色构成</div>
                <div ref="locPieRef" class="echart-main"></div>
              </div>
            </div>
            <div class="chart-card glass-effect h-500">
              <div class="chart-header">地点特征聚类</div>
              <div ref="locScatterRef" class="echart-main"></div>
            </div>
          </div>
        </div>

        <div v-if="currentTab === 'time'" class="view-panel">
          <div class="panel-header">
            <div class="panel-title">时间维度演化</div>
            <div class="download-group" v-if="timeData && timeData.files">
              <el-button-group>
                <el-button size="small" @click="downloadFile(timeData.files.csv, 'time_data.csv')">
                  <el-icon><Document /></el-icon> 下载数据
                </el-button>
              </el-button-group>
            </div>
          </div>
          <div v-if="timeData" class="chart-col">
            <div class="chart-card glass-effect h-400">
              <div class="chart-header">历史事件时间线 (Timeline)</div>
              <div ref="timeTimelineRef" class="echart-main"></div>
            </div>
            <div class="chart-card glass-effect h-300">
              <div class="chart-header">朝代/时期事件密度</div>
              <div ref="timeBarRef" class="echart-main"></div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, shallowRef } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { Refresh, Connection, PriceTag, MapLocation, Timer, Picture, Document } from '@element-plus/icons-vue'

const loading = ref(false)
const currentTab = ref('causal')
const tabs = [
  { id: 'causal', name: '因果演化', icon: Connection },
  { id: 'type', name: '事件类型', icon: PriceTag },
  { id: 'location', name: '空间分布', icon: MapLocation },
  { id: 'time', name: '时间演化', icon: Timer },
]

// Data Storage
const causalData = ref(null)
const typeData = ref(null)
const locData = ref(null)
const timeData = ref(null)

// DOM Refs
const causalChainRef = ref(null)
const causalNetworkRef = ref(null)
const typeScatterRef = ref(null)
const locBarRef = ref(null)
const locPieRef = ref(null)
const locScatterRef = ref(null)
const timeTimelineRef = ref(null)
const timeBarRef = ref(null)

// Chart Instances
const charts = shallowRef({})

// Switching Logic
const switchTab = (id) => {
  currentTab.value = id
  nextTick(() => {
    if (id === 'causal') { if(!causalData.value) fetchCausal(); else renderCausal(); }
    if (id === 'type') { if(!typeData.value) fetchType(); else renderType(); }
    if (id === 'location') { if(!locData.value) fetchLoc(); else renderLoc(); }
    if (id === 'time') { if(!timeData.value) fetchTime(); else renderTime(); }
  })
}

const refreshCurrent = () => {
  if (currentTab.value === 'causal') fetchCausal()
  if (currentTab.value === 'type') fetchType()
  if (currentTab.value === 'location') fetchLoc()
  if (currentTab.value === 'time') fetchTime()
}

const downloadFile = (url, filename) => {
  if (!url) return
  const proxyUrl = `http://localhost:8080/api/analysis/proxy/download?url=${encodeURIComponent(url)}`
  const link = document.createElement('a')
  link.href = proxyUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const viewImage = (url) => {
  if (!url) return
  // 根据 README，使用预览代理在新网页打开图片
  const proxyViewUrl = `http://localhost:8080/api/analysis/proxy/view?url=${encodeURIComponent(url)}`
  window.open(proxyViewUrl, '_blank')
}

const normalizeFiles = (data) => {
  if (!data) return null
  // 优先直接使用 data.files (符合新版 README 结构)
  if (data.files) return data.files
  // 兜底逻辑：处理可能的其他命名格式
  return {
    image: data.image_url || data.image || data.image_path,
    csv: data.csv_url || data.csv || data.csv_path
  }
}

// === API & Render Logic ===

// 1. Causal
const fetchCausal = async () => {
  loading.value = true
  try {
    const res = await axios.post('http://localhost:8080/api/analysis/causal/portrait')
    const rawData = res.data.data
    causalData.value = { ...rawData, files: normalizeFiles(rawData) }
    nextTick(renderCausal)
  } catch(e) { console.error(e) } finally { loading.value = false }
}
const renderCausal = () => {
  if(causalChainRef.value) {
    const chart = echarts.init(causalChainRef.value); charts.value.chain = chart
    const data = causalData.value.chains
    const series = data.map((chain, i) => ({
      type: 'line', smooth: 0.4, data: chain, name: `链${i+1}`,
      symbolSize: 8, label: { show: true, formatter: p=>p.data[2] },
      areaStyle: { opacity: 0.2 }
    }))
    chart.setOption({
      tooltip: { trigger: 'axis' }, grid: { top: 30, bottom: 20 },
      // 因果链是折线图，虽然隐藏了轴，但必须有 xAxis/yAxis
      xAxis: { type: 'value', show: false },
      yAxis: { type: 'category', show: false },
      series
    })
  }
  if(causalNetworkRef.value) {
    const chart = echarts.init(causalNetworkRef.value); charts.value.net = chart
    const g = causalData.value.graph
    chart.setOption({
      tooltip: {}, series: [{
        type: 'graph', layout: 'force', data: g.nodes, links: g.links, roam: true,
        itemStyle: { color: '#8e3e3e' }, lineStyle: { color: '#b8860b', curveness: 0.2 },
        force: { repulsion: 300, edgeLength: 150 }
      }]
    })
  }
}

// 2. Type
const fetchType = async () => {
  loading.value = true
  try {
    const res = await axios.post('http://localhost:8080/api/analysis/event/type')
    const rawData = res.data.data
    typeData.value = { ...rawData, files: normalizeFiles(rawData) }
    nextTick(renderType)
  } catch(e) { console.error(e) } finally { loading.value = false }
}
const renderType = () => {
  if(typeScatterRef.value) {
    const chart = echarts.init(typeScatterRef.value); charts.value.type = chart
    chart.setOption({
      tooltip: { formatter: p => `<b>${p.name}</b><br>ID: ${p.value[2]}` },
      // 【核心修复】散点图必须有 x/y 轴，哪怕不显示
      xAxis: { scale: true, show: false },
      yAxis: { scale: true, show: false },
      visualMap: { show: false, min: 0, max: 5, inRange: { color: ['#d94e5d', '#eac736', '#2b4b64'] } },
      series: [{ type: 'scatter', symbolSize: 15, data: typeData.value.scatter }]
    })
  }
}

// 3. Location
const fetchLoc = async () => {
  loading.value = true
  try {
    const res = await axios.post('http://localhost:8080/api/analysis/event/location')
    const rawData = res.data.data
    locData.value = { ...rawData, files: normalizeFiles(rawData) }
    nextTick(renderLoc)
  } catch(e) { console.error(e) } finally { loading.value = false }
}
const renderLoc = () => {
  if(locBarRef.value) {
    const chart = echarts.init(locBarRef.value)
    chart.setOption({
      tooltip: {},
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: locData.value.bar.categories },
      series: [{ type: 'bar', data: locData.value.bar.values, itemStyle: { color: '#8e3e3e' } }]
    })
  }
  if(locPieRef.value) {
    const chart = echarts.init(locPieRef.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      series: [{ type: 'pie', radius: ['40%', '70%'], data: locData.value.pie }]
    })
  }
  if(locScatterRef.value) {
    const chart = echarts.init(locScatterRef.value)
    chart.setOption({
      tooltip: { formatter: p => p.name },
      // 【核心修复】添加隐藏的坐标轴
      xAxis: { scale: true, show: false },
      yAxis: { scale: true, show: false },
      visualMap: { show: false, min: 0, max: 5, inRange: { color: ['#2b4b64', '#50a3ba'] } },
      series: [{ type: 'scatter', symbolSize: 12, data: locData.value.scatter }]
    })
  }
}

// 4. Time
const fetchTime = async () => {
  loading.value = true
  try {
    const res = await axios.post('http://localhost:8080/api/analysis/event/time')
    const rawData = res.data.data
    timeData.value = { ...rawData, files: normalizeFiles(rawData) }
    nextTick(renderTime)
  } catch(e) { console.error(e) } finally { loading.value = false }
}
const renderTime = () => {
  if(timeTimelineRef.value) {
    const chart = echarts.init(timeTimelineRef.value)
    chart.setOption({
      tooltip: { formatter: p => `<b>${p.data[2]}</b><br>${p.data[3]}<br>Year: ${p.data[0]}` },
      // 时间轴散点图，已经有轴定义
      xAxis: { type: 'value', scale: true, name: '年份' },
      yAxis: { show: false },
      visualMap: { show: false, min: 0, max: 5, dimension: 1, inRange: { color: ['#d94e5d', '#eac736', '#2b4b64'] } },
      series: [{ type: 'scatter', symbolSize: 14, data: timeData.value.timeline }]
    })
  }
  if(timeBarRef.value) {
    const chart = echarts.init(timeBarRef.value)
    chart.setOption({
      tooltip: {},
      xAxis: { type: 'category', data: timeData.value.windows.map(d=>d.name) },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: timeData.value.windows.map(d=>d.value), itemStyle: { color: '#2b4b64' } }]
    })
  }
}

onMounted(() => {
  fetchCausal()
  window.addEventListener('resize', () => Object.values(charts.value).forEach(c => c?.resize()))
})
</script>

<style scoped>
.portrait-container { display: flex; flex-direction: column; height: 100%; background: #fcf9f2; background-image: radial-gradient(#e6dcc8 1px, transparent 1px); background-size: 20px 20px; }
.header-section { padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(142,62,62,0.1); flex-shrink: 0; }
.title-group { display: flex; flex-direction: column; }
.gufeng-title { color: #5e482d; margin: 0; font-size: 24px; font-weight: bold; }
.sub-title { font-size: 12px; color: #999; text-transform: uppercase; letter-spacing: 1px; }

.main-layout { display: flex; flex: 1; overflow: hidden; }
.dimension-sidebar { width: 180px; background: rgba(255,255,255,0.6); border-right: 1px solid rgba(142,62,62,0.1); padding: 20px 0; display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }
.nav-item { padding: 12px 20px; cursor: pointer; display: flex; align-items: center; gap: 10px; color: #5e482d; transition: all 0.3s; border-left: 4px solid transparent; }
.nav-item:hover { background: rgba(142,62,62,0.05); }
.nav-item.active { background: rgba(142,62,62,0.1); border-left-color: #8e3e3e; color: #8e3e3e; font-weight: bold; }

.content-area { flex: 1; padding: 20px; overflow-y: auto; }
.view-panel { display: flex; flex-direction: column; gap: 20px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(142,62,62,0.1); padding-bottom: 10px; margin-bottom: 10px; }
.panel-title { font-size: 18px; font-weight: bold; color: #8e3e3e; border-left: 4px solid #b8860b; padding-left: 10px; margin: 0; }
.download-group { display: flex; align-items: center; }

.chart-col { display: flex; flex-direction: column; gap: 20px; }
.chart-row { display: flex; gap: 20px; }
.chart-row > div { flex: 1; }

.glass-effect { background: rgba(255, 255, 255, 0.65); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.8); border-radius: 12px; box-shadow: 0 4px 15px rgba(139, 69, 19, 0.05); padding: 15px; position: relative; display: flex; flex-direction: column; }
.chart-header { font-weight: bold; color: #5e482d; margin-bottom: 10px; border-bottom: 1px dashed #e6dcc8; padding-bottom: 5px; }

.echart-main { flex: 1; width: 100%; }
.h-300 { height: 300px; } .h-350 { height: 350px; } .h-400 { height: 400px; } .h-500 { height: 500px; }

.stats-row { display: flex; gap: 20px; margin-bottom: 10px; }
.mini-card { flex: 1; display: flex; align-items: center; justify-content: space-between; padding: 15px 25px; }
.gold { color: #b8860b; font-size: 24px; font-family: Georgia; }
.blue { color: #2b4b64; font-size: 24px; font-family: Georgia; }

.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(184, 134, 11, 0.3); border-radius: 3px; }
</style>