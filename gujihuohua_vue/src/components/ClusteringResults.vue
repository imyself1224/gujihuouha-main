<template>
  <div class="clustering-results-modern">
    <!-- 顶部标题栏 -->
    <div class="modern-header">
      <div class="header-left">
        <div class="title-icon-bg">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="header-text">
          <h3>时空聚类分析报告</h3>
          <span class="subtitle">Spatial-Temporal Clustering Report</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" plain round size="small" @click="showHistoryPanel">
          <el-icon class="el-icon--left"><Memo /></el-icon> 历史记录
        </el-button>
        <el-button type="primary" plain round size="small" @click="exportAsCSV">
          <el-icon class="el-icon--left"><Download /></el-icon> 导出 CSV
        </el-button>
        <el-button type="default" round size="small" @click="$emit('close')">
          <el-icon class="el-icon--left"><Refresh /></el-icon> 重置
        </el-button>
      </div>
    </div>

    <!-- 数据概览卡片 -->
    <div class="stats-dashboard" v-if="processedResults.summary">
      <div class="stat-card primary">
        <div class="stat-icon">
          <el-icon><Files /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">总事件数</span>
          <span class="stat-value">{{ processedResults.summary.total_events }}</span>
        </div>
      </div>
      
      <div class="stat-card success">
        <div class="stat-icon">
          <el-icon><Connection /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">聚类群组</span>
          <span class="stat-value">{{ processedResults.summary.num_clusters }}</span>
        </div>
      </div>

      <div class="stat-card warning">
        <div class="stat-icon">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">离散噪声点</span>
          <span class="stat-value">{{ processedResults.summary.num_noise }}</span>
        </div>
      </div>
    </div>

    <!-- 聚类详情列表 -->
    <div class="clusters-container custom-scrollbar" v-if="processedResults.clusters && processedResults.clusters.length > 0">
      <div 
        v-for="cluster in processedResults.clusters" 
        :key="cluster.cluster_id"
        class="cluster-card"
        :class="{ 'is-noise': cluster.cluster_id === -1 }"
      >
        <div class="cluster-header-row" @click="toggleCluster(cluster.cluster_id)">
          <div class="cluster-title">
            <el-icon 
              class="expand-icon"
              :class="{ 'is-expanded': isExpanded(cluster.cluster_id) }"
            >
              <ArrowRight />
            </el-icon>
            <el-tag 
              :type="cluster.cluster_id === -1 ? 'info' : 'success'" 
              effect="dark"
              round
              class="cluster-tag"
            >
              {{ cluster.cluster_id === -1 ? '噪声' : `#${cluster.cluster_id}` }}
            </el-tag>
            <span class="cluster-name-text">
              {{ cluster.cluster_id === -1 ? '离散事件集合' : `时空聚类群组 ${cluster.cluster_id}` }}
            </span>
          </div>
          <div class="cluster-meta">
            <span class="event-count">{{ cluster.size }} 个事件</span>
          </div>
        </div>

        <div class="cluster-content" v-show="isExpanded(cluster.cluster_id)">
          <el-table 
            :data="cluster.events" 
            style="width: 100%" 
            :header-cell-style="{ background: '#f8f9fa', color: '#606266' }"
            size="small"
            border
          >
            <el-table-column prop="id" label="ID" width="90" align="center">
              <template #default="{ row }">
                <span class="id-text">{{ row.id }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="year" label="年份" width="80" align="center">
              <template #default="{ row }">
                <el-tag size="small" effect="plain" type="info">{{ row.year }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="地点信息" min-width="180">
              <template #default="{ row }">
                <div class="location-cell">
                  <div class="ancient-loc" v-if="row.location_ancient">
                    <el-tag size="small" type="danger" effect="light">古</el-tag> {{ row.location_ancient }}
                  </div>
                  <div class="modern-loc" v-if="row.location_modern">
                    <el-tag size="small" type="info" effect="light">今</el-tag> {{ row.location_modern }}
                  </div>
                  <div class="single-loc" v-if="!row.location_ancient && !row.location_modern && row.location">
                    {{ row.location }}
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="事件描述" min-width="250">
              <template #default="{ row }">
                <span class="desc-text">{{ row.description }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- 地图展示（可选） -->
    <div class="map-section" v-if="showMap">
      <div class="section-header">
        <el-icon><MapLocation /></el-icon> 聚类分布地图
      </div>
      <div id="cluster-map" class="map-box">
        <el-empty description="地图功能需要配置地图库"></el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref, computed, watch } from 'vue'
import { Download, DataAnalysis, Files, Connection, Warning, MapLocation, ArrowRight, Refresh, Memo } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  results: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'showHistory'])

const showMap = ref(false)
const expandedClusters = ref([])

const toggleCluster = (clusterId) => {
  const index = expandedClusters.value.indexOf(clusterId)
  if (index > -1) {
    expandedClusters.value.splice(index, 1)
  } else {
    expandedClusters.value.push(clusterId)
  }
}

const isExpanded = (clusterId) => {
  return expandedClusters.value.includes(clusterId)
}

/**
 * 将 CSV 字符串解析为对象数组
 */
const parseCSV = (csvString) => {
  const emptyResult = { clusters: [], summary: { total_events: 0, num_clusters: 0, num_noise: 0 } }
  if (!csvString || typeof csvString !== 'string') {
    return emptyResult
  }

  const lines = csvString.trim().split('\n')
  if (lines.length < 2) {
    return emptyResult
  }

  // 解析表头，支持多种列名变体
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
  const headerMap = {}
  headers.forEach((header, index) => {
    headerMap[header] = index
  })

  // 获取正确的列索引（支持多种列名变体）
  const getColumnIndex = (alternatives) => {
    for (const alt of alternatives) {
      if (headerMap[alt] !== undefined) {
        return headerMap[alt]
      }
    }
    return -1
  }

  // 解析数据行
  const events = []
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue

    // 处理包含逗号的字段（需要处理引号）
    const parts = []
    let current = ''
    let inQuotes = false
    for (let j = 0; j < line.length; j++) {
      const char = line[j]
      if (char === '"') {
        inQuotes = !inQuotes
      } else if (char === ',' && !inQuotes) {
        parts.push(current.trim())
        current = ''
      } else {
        current += char
      }
    }
    parts.push(current.trim())

    if (parts.length >= headers.length) {
      // 支持多种列名变体
      const idIdx = getColumnIndex(['id', 'd', 'event_id'])
      const yearIdx = getColumnIndex(['year', 'age', 'event_year'])
      const descIdx = getColumnIndex(['description', 'desc', 'event_desc'])
      const locAncientIdx = getColumnIndex(['location_ancient', 'ancient_location', 'location', '古代地名'])
      const locModernIdx = getColumnIndex(['location_modern', 'modern_location', '现代地名'])
      const latIdx = getColumnIndex(['latitude', 'lat'])
      const lonIdx = getColumnIndex(['longitude', 'lon'])
      const clusterIdx = getColumnIndex(['cluster', 'cluster_id'])
      const methodIdx = getColumnIndex(['assigned_method', 'assignment_method', 'method'])

      const event = {
        id: idIdx >= 0 ? (parts[idIdx] || '') : '',
        year: yearIdx >= 0 ? parseInt(parts[yearIdx] || '0') : 0,
        description: descIdx >= 0 ? (parts[descIdx] || '').replace(/^"|"$/g, '') : '',
        location_ancient: locAncientIdx >= 0 ? (parts[locAncientIdx] || '') : '',
        location_modern: locModernIdx >= 0 ? (parts[locModernIdx] || '') : '',
        latitude: latIdx >= 0 ? parseFloat(parts[latIdx] || '0') : 0,
        longitude: lonIdx >= 0 ? parseFloat(parts[lonIdx] || '0') : 0,
        cluster: clusterIdx >= 0 ? parseInt(parts[clusterIdx] || '-1') : -1,
        assigned_method: methodIdx >= 0 ? (parts[methodIdx] || 'unknown') : 'unknown'
      }
      events.push(event)
    }
  }

  // 按聚类 ID 分组
  const clustersMap = {}
  events.forEach(event => {
    const clusterId = event.cluster
    if (!clustersMap[clusterId]) {
      clustersMap[clusterId] = {
        cluster_id: clusterId,
        size: 0,
        events: []
      }
    }
    clustersMap[clusterId].events.push(event)
    clustersMap[clusterId].size++
  })

  const clusters = Object.values(clustersMap).sort((a, b) => a.cluster_id - b.cluster_id)

  // 计算摘要统计
  const noiseCluster = clusters.find(c => c.cluster_id === -1)
  const summary = {
    total_events: events.length,
    num_clusters: clusters.filter(c => c.cluster_id !== -1).length,
    num_noise: noiseCluster ? noiseCluster.size : 0,
    best_params: { eps: 'auto', min_samples: 'auto' }
  }

  return { clusters, summary }
}

/**
 * 根据结果类型选择合适的数据结构
 */
const processedResults = computed(() => {
  // 如果 results 已经是结构化的 JSON 格式
  if (props.results.clusters && Array.isArray(props.results.clusters)) {
    return props.results
  }

  // 如果 results.data 是 CSV 字符串
  if (props.results.data && typeof props.results.data === 'string') {
    return parseCSV(props.results.data)
  }

  // 如果整个 results 是 CSV 字符串
  if (typeof props.results === 'string') {
    return parseCSV(props.results)
  }

  // 降级处理：返回空结果
  return { clusters: [], summary: { total_events: 0, num_clusters: 0, num_noise: 0 } }
})

// 监听结果变化，默认不展开聚类
watch(processedResults, (newVal) => {
  if (newVal && newVal.clusters) {
    // 默认不展开任何聚类
    expandedClusters.value = []
  }
}, { immediate: true })

/**
 * 导出为 CSV
 */
const exportAsCSV = () => {
  try {
    let csvContent = 'id,year,location_ancient,location_modern,description,latitude,longitude,cluster,assigned_method\n'

    if (processedResults.value.clusters) {
      processedResults.value.clusters.forEach((cluster) => {
        cluster.events.forEach((event) => {
          const row = [
            event.id,
            event.year,
            event.location_ancient || '',
            event.location_modern || '',
            `"${event.description || ''}"`,
            event.latitude,
            event.longitude,
            cluster.cluster_id,
            event.assigned_method || 'unknown'
          ].join(',')
          csvContent += row + '\n'
        })
      })
    }

    const dataBlob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `clustering_results_${new Date().getTime()}.csv`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('CSV 导出成功')
  } catch (error) {
    ElMessage.error('CSV 导出失败: ' + error.message)
  }
}

/**
 * 显示历史记录面板
 */
const showHistoryPanel = () => {
  emit('showHistory', {
    analysisId: props.results.analysisId
  })
}
</script>

<style scoped>
.clustering-results-modern {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #2c3e50;
}

/* Header Styles */
.modern-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f2f5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon-bg {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #409eff 0%, #ecf5ff 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.header-text h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.2;
}

.subtitle {
  font-size: 12px;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.close-btn {
  font-size: 20px;
  color: #909399;
  transition: all 0.3s;
}

.close-btn:hover {
  color: #f56c6c;
  background: #fef0f0;
  transform: rotate(90deg);
}

/* Stats Dashboard */
.stats-dashboard {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #ebeef5;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
}

.stat-card.primary .stat-icon { background: #ecf5ff; color: #409eff; }
.stat-card.success .stat-icon { background: #f0f9eb; color: #67c23a; }
.stat-card.warning .stat-icon { background: #fdf6ec; color: #e6a23c; }

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

/* Clusters List */
.clusters-container {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.cluster-card {
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;
  transition: all 0.3s;
}

.cluster-card:hover {
  border-color: #c6e2ff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.cluster-card.is-noise {
  border-style: dashed;
  background: #fafafa;
}

.cluster-header-row {
  padding: 16px 20px;
  background: #fcfcfc;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cluster-header-row:hover {
  background-color: #f5f7fa;
}

.expand-icon {
  font-size: 14px;
  color: #909399;
  transition: transform 0.3s;
  margin-right: 4px;
}

.expand-icon.is-expanded {
  transform: rotate(90deg);
}

.cluster-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cluster-name-text {
  font-weight: 600;
  color: #606266;
  font-size: 15px;
}

.cluster-meta {
  font-size: 13px;
  color: #909399;
}

.cluster-content {
  padding: 0;
}

/* Table Customization */
.location-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ancient-loc, .modern-loc {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.id-text {
  font-family: monospace;
  color: #909399;
}

.desc-text {
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f5f7fa;
}

/* Map Section */
.map-section {
  margin-top: 32px;
  border-top: 1px solid #ebeef5;
  padding-top: 24px;
}

.section-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.map-box {
  height: 400px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #ebeef5;
}
</style>
