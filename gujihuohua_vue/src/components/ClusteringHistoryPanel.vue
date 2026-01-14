<template>
  <el-drawer
      v-model="isVisible"
      title="时空聚类分析历史记录"
      direction="rtl"
      size="70%"
      :close-on-click-modal="false"
      @close="handleClose"
      class="history-drawer"
  >
    <div class="history-container">
      <!-- 左侧：日期时间轴 -->
      <div class="history-sidebar custom-scrollbar">
        <div class="sidebar-header">
          <span class="sidebar-title">日期归档</span>
          <el-button link type="primary" @click="loadHistory" :loading="loading" title="刷新列表">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        
        <div v-if="dateList.length === 0" class="empty-sidebar">
          <el-empty description="暂无记录" image-size="60"></el-empty>
        </div>

        <ul v-else class="date-timeline">
          <li 
            v-for="date in dateList" 
            :key="date"
            class="date-item"
            :class="{ active: selectedDate === date }"
            @click="selectDate(date)"
          >
            <div class="date-marker"></div>
            <div class="date-content">
              <span class="date-text">{{ date }}</span>
              <el-tag size="small" round effect="plain" type="info">{{ getRecordCountForDate(date) }}</el-tag>
            </div>
          </li>
        </ul>
      </div>

      <!-- 右侧：记录列表 -->
      <div class="history-content custom-scrollbar">
        <div v-if="!selectedDate" class="content-placeholder">
          <el-icon class="placeholder-icon"><Calendar /></el-icon>
          <p>请选择左侧日期查看历史记录</p>
        </div>

        <div v-else>
          <div class="content-header">
            <h3>{{ selectedDate }}</h3>
            <span class="record-count">共 {{ recordsForSelectedDate.length }} 条记录</span>
          </div>

          <div v-if="recordsForSelectedDate.length === 0" class="no-records">
             <el-empty description="该日期暂无记录"></el-empty>
          </div>

          <div v-else class="records-grid">
            <el-card 
              v-for="record in recordsForSelectedDate" 
              :key="record.analysisId" 
              class="record-card"
              shadow="hover"
            >
              <template #header>
                <div class="card-header">
                  <div class="header-title">
                    <el-tag size="small" effect="dark" type="success">ID</el-tag>
                    <span class="analysis-id" :title="record.analysisId">{{ formatId(record.analysisId) }}</span>
                  </div>
                  <el-button 
                    type="primary" 
                    link 
                    size="small" 
                    @click="copyAnalysisId(record.analysisId)"
                    title="复制完整ID"
                  >
                    <el-icon><DocumentCopy /></el-icon>
                  </el-button>
                </div>
              </template>
              
              <div class="card-body">
                <div class="file-info">
                  <div class="info-item">
                    <el-icon class="info-icon"><Location /></el-icon>
                    <span class="info-label">地点:</span>
                    <span class="info-value" :title="record.locationFileName">{{ record.locationFileName }}</span>
                  </div>
                  <div class="info-item">
                    <el-icon class="info-icon"><Document /></el-icon>
                    <span class="info-label">事件:</span>
                    <span class="info-value" :title="record.eventsFileName">{{ record.eventsFileName }}</span>
                  </div>
                </div>
                
                <div class="card-actions">
                  <el-button 
                    type="primary" 
                    class="action-btn" 
                    @click="rerunAnalysis(record)"
                    :loading="loading"
                    plain
                  >
                    <el-icon style="margin-right: 4px"><VideoPlay /></el-icon> 加载
                  </el-button>
                  <el-button 
                    type="danger" 
                    class="action-btn" 
                    @click="deleteRecord(record)"
                    :loading="loading"
                    plain
                    style="margin-left: 10px;"
                  >
                    <el-icon style="margin-right: 4px"><Delete /></el-icon> 删除
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref, computed, watch, defineProps, defineEmits, defineExpose } from 'vue'
import { Refresh, DocumentCopy, Calendar, Location, Document, VideoPlay, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'rerun-complete'])

const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const loading = ref(false)
const dateList = ref([])
const selectedDate = ref(null)
const historyByDate = ref({})

const apiBaseUrl = 'http://localhost:8080/api'

/**
 * 格式化ID显示 (前8位)
 */
const formatId = (id) => {
  if (!id) return ''
  return id.length > 12 ? id.substring(0, 12) + '...' : id
}

/**
 * 获取指定日期的记录数
 */
const getRecordCountForDate = (date) => {
  return historyByDate.value[date]?.length || 0
}

/**
 * 获取选中日期的记录
 */
const recordsForSelectedDate = computed(() => {
  if (!selectedDate.value) return []
  return historyByDate.value[selectedDate.value] || []
})

/**
 * 加载历史记录
 */
const loadHistory = async () => {
  loading.value = true
  try {
    const response = await fetch(`${apiBaseUrl}/analysis/event-cluster/history/grouped`)
    const result = await response.json()

    if (result.status === 'success') {
      historyByDate.value = result.data || {}
      dateList.value = Object.keys(historyByDate.value).sort((a, b) => b.localeCompare(a))
      
      // 自动选择第一个日期
      if (dateList.value.length > 0 && !selectedDate.value) {
        selectedDate.value = dateList.value[0]
      }
      
      // ElMessage.success('历史记录加载成功')
    } else {
      ElMessage.error(result.message || '加载历史记录失败')
    }
  } catch (error) {
    ElMessage.error('加载历史记录异常: ' + error.message)
    console.error('加载历史记录异常:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 删除记录
 */
const deleteRecord = async (record) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条聚类分析记录吗？对应的文件也将被删除。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    loading.value = true
    const response = await fetch(`${apiBaseUrl}/analysis/event-cluster/history/${record.analysisId}`, {
      method: 'DELETE'
    })
    const result = await response.json()

    if (result.status === 'success') {
      ElMessage.success('删除成功')
      await loadHistory() // 刷新列表
    } else {
      ElMessage.error(result.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除操作异常: ' + error.message)
      console.error('删除操作异常:', error)
    }
  } finally {
    loading.value = false
  }
}

/**
 * 选择日期
 */
const selectDate = (date) => {
  selectedDate.value = date
}

/**
 * 重新运行分析
 */
const rerunAnalysis = async (record) => {
  try {
    loading.value = true

    const response = await fetch(`${apiBaseUrl}/analysis/event-cluster/rerun`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        locationFilePath: record.locationFilePath,
        eventsFilePath: record.eventsFilePath,
        locationFileName: record.locationFileName,
        eventsFileName: record.eventsFileName
      })
    })

    const result = await response.json()

    if (result.status === 'success') {
      ElMessage.success('分析重新运行成功')
      // 发送事件通知父组件刷新结果
      emit('rerun-complete', {
        analysisId: result.analysisId,
        data: result.data
      })
      // 关闭窗口
      isVisible.value = false
    } else {
      ElMessage.error(result.message || '分析重新运行失败')
    }
  } catch (error) {
    ElMessage.error('重新运行分析异常: ' + error.message)
    console.error('重新运行分析异常:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 复制分析ID
 */
const copyAnalysisId = (analysisId) => {
  navigator.clipboard.writeText(analysisId).then(() => {
    ElMessage.success('已复制: ' + analysisId)
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

/**
 * 处理关闭
 */
const handleClose = () => {
  // selectedDate.value = null // 保持选中状态，体验更好
  isVisible.value = false
}

/**
 * 监听visible变化，加载数据
 */
watch(() => isVisible.value, (newVal) => {
  if (newVal) {
    loadHistory()
  }
})

defineExpose({
  loadHistory
})
</script>

<style scoped>
.history-container {
  display: flex;
  height: calc(100vh - 150px); /* 适应Drawer高度 */
  border: 1px solid #eee;
  border-radius: 4px;
  overflow: hidden;
}

.history-sidebar {
  width: 240px;
  background-color: #f9fafc;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  position: sticky;
  top: 0;
  z-index: 1;
}

.sidebar-title {
  font-weight: 600;
  color: #303133;
}

.date-timeline {
  list-style: none;
  padding: 0;
  margin: 0;
}

.date-item {
  position: relative;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.date-item:hover {
  background-color: #f0f2f5;
}

.date-item.active {
  background-color: #e6f7ff;
  border-left-color: #409eff;
}

.date-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date-text {
  font-size: 14px;
  color: #606266;
}

.date-item.active .date-text {
  color: #409eff;
  font-weight: 500;
}

.history-content {
  flex: 1;
  padding: 20px;
  background-color: #fff;
  overflow-y: auto;
}

.content-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #909399;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #dcdfe6;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.content-header h3 {
  margin: 0;
  color: #303133;
}

.record-count {
  font-size: 13px;
  color: #909399;
}

.records-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.record-card {
  transition: all 0.3s;
  border: 1px solid #ebeef5;
}

.record-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.analysis-id {
  font-family: monospace;
  font-size: 13px;
  color: #606266;
}

.card-body {
  padding: 10px 0 0 0;
}

.file-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
}

.info-icon {
  margin-right: 6px;
  color: #909399;
}

.info-label {
  color: #909399;
  margin-right: 8px;
  min-width: 40px;
}

.info-value {
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #f5f7fa;
  padding-top: 12px;
}

.action-btn {
  width: 100%;
}

/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
</style>
