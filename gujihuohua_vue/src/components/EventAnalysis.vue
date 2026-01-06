<template>
  <div class="analysis-container fade-in">
    <!-- 标签页选择 -->
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 事件时线展示 -->
      <el-tab-pane label="事件时线" name="timeline">
        <div class="header-row">
          <h2 class="gufeng-title">古籍事件脉络抽取</h2>
          <el-button type="primary" class="gufeng-btn" @click="loadEventData">
            <el-icon style="margin-right:5px"><Timer /></el-icon> 载入事件流
          </el-button>
        </div>

        <div class="timeline-workspace custom-scrollbar">
          <div v-if="events.length === 0" class="empty-state">暂无事件数据</div>

          <el-timeline v-else>
            <el-timeline-item
                v-for="(activity, index) in events"
                :key="index"
                :timestamp="activity.time"
                placement="top"
                :color="activity.color"
                size="large"
            >
              <el-card class="event-card">
                <h4 class="event-title">{{ activity.title }}</h4>
                <p class="event-desc">{{ activity.content }}</p>
                <div class="event-tags">
                  <el-tag size="small" effect="plain" type="danger" v-for="role in activity.roles" :key="role">{{ role }}</el-tag>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
      </el-tab-pane>

      <!-- 时空聚类分析 -->
      <el-tab-pane label="时空聚类分析" name="clustering">
        <div class="clustering-container">
          <div class="header-row" style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
             <h2 class="gufeng-title" style="margin:0">时空聚类分析任务</h2>
             <el-button type="primary" plain @click="showHistoryPanel = true">
               <el-icon style="margin-right:5px"><Memo /></el-icon> 查看历史记录
             </el-button>
          </div>

          <div v-if="!clusteringResults" class="task-creation-panel">
            <!-- 任务配置卡片 -->
            <el-card class="task-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span class="card-title">新建分析任务</span>
                  <el-tag type="info" effect="plain" size="small">请上传所需数据文件</el-tag>
                </div>
              </template>
              
              <div class="upload-grid">
                <!-- 地点数据上传 -->
                <div class="upload-box">
                  <div class="upload-header">
                    <el-icon class="upload-icon"><Location /></el-icon>
                    <span class="upload-label">地点数据 (CSV)</span>
                  </div>
                  <el-upload
                      class="custom-upload"
                      accept=".csv"
                      :auto-upload="false"
                      :on-change="handleLocationFileChange"
                      :file-list="locationFileList"
                      drag
                  >
                    <div class="upload-content">
                      <el-icon class="el-icon--upload"><DocumentCopy /></el-icon>
                      <div class="el-upload__text">
                        拖拽文件到此或 <em>点击上传</em>
                      </div>
                    </div>
                  </el-upload>
                </div>

                <!-- 事件数据上传 -->
                <div class="upload-box">
                  <div class="upload-header">
                    <el-icon class="upload-icon"><Document /></el-icon>
                    <span class="upload-label">事件数据 (JSON)</span>
                  </div>
                  <el-upload
                      class="custom-upload"
                      accept=".json"
                      :auto-upload="false"
                      :on-change="handleEventsFileChange"
                      :file-list="eventsFileList"
                      drag
                  >
                    <div class="upload-content">
                      <el-icon class="el-icon--upload"><DocumentCopy /></el-icon>
                      <div class="el-upload__text">
                        拖拽文件到此或 <em>点击上传</em>
                      </div>
                    </div>
                  </el-upload>
                </div>
              </div>

              <!-- 操作按钮区 -->
              <div class="task-actions">
                <el-button 
                    type="primary" 
                    @click="performClustering" 
                    :loading="clustering"
                    :disabled="!locationFile || !eventsFile"
                    size="large"
                    class="action-btn primary-btn"
                >
                  <el-icon style="margin-right:8px"><VideoPlay /></el-icon> 开始分析
                </el-button>
                <el-button @click="resetFiles" size="large" class="action-btn">
                  <el-icon style="margin-right:8px"><Refresh /></el-icon> 重置
                </el-button>
              </div>
            </el-card>

            <!-- 提示信息 -->
            <div class="task-tips">
              <el-alert
                title="提示：请确保上传的CSV文件包含经纬度信息，JSON文件符合事件数据结构规范。"
                type="info"
                show-icon
                :closable="false"
              />
            </div>
          </div>
          <!-- 结果展示区域 -->
          <ClusteringResults 
              v-if="clusteringResults"
              :results="clusteringResults"
              @close="clusteringResults = null"
              @showHistory="(data) => { showHistoryPanel = true; currentAnalysisId = data.analysisId }"
          />

          <!-- 加载中提示 -->
          <div v-if="clustering" class="loading-state">
            <el-progress type="circle" :percentage="0" status="exception" :width="100"></el-progress>
            <p style="margin-top: 20px;">聚类分析进行中，请稍候...</p>
          </div>

          <!-- 错误提示 -->
          <el-alert 
              v-if="clusteringError"
              :title="clusteringError"
              type="error"
              closable
              @close="clusteringError = ''"
              style="margin-top: 20px;"
          ></el-alert>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 历史记录面板 -->
    <ClusteringHistoryPanel 
        v-model:visible="showHistoryPanel"
        :currentAnalysisId="currentAnalysisId"
        @viewResults="handleViewHistoryResults"
        @rerun-complete="handleRerunComplete"
    />
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref } from 'vue'
import { Timer, VideoPlay, Refresh, DocumentCopy, Memo, Location, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import ClusteringResults from './ClusteringResults.vue'
import ClusteringHistoryPanel from './ClusteringHistoryPanel.vue'

// 标签页状态
const activeTab = ref('timeline')

// 事件时线数据
const events = ref([])

// 文件相关
const locationFile = ref(null)
const eventsFile = ref(null)
const locationFileList = ref([])
const eventsFileList = ref([])

// 聚类相关数据
const clustering = ref(false)
const clusteringResults = ref(null)
const clusteringError = ref('')

// 历史记录面板相关
const showHistoryPanel = ref(false)
const currentAnalysisId = ref(null)

// API基础URL
const apiBaseUrl = 'http://localhost:8080/api'

/**
 * 处理地点文件变化
 */
const handleLocationFileChange = (file) => {
  if (file.raw) {
    locationFile.value = file.raw
    locationFileList.value = [file]
  }
}

/**
 * 处理事件文件变化
 */
const handleEventsFileChange = (file) => {
  if (file.raw) {
    eventsFile.value = file.raw
    eventsFileList.value = [file]
  }
}

/**
 * 重置文件
 */
const resetFiles = () => {
  locationFile.value = null
  eventsFile.value = null
  locationFileList.value = []
  eventsFileList.value = []
  clusteringResults.value = null
  clusteringError.value = ''
  ElMessage.info('文件已重置')
}

/**
 * 执行聚类分析
 */
const performClustering = async () => {
  // 验证文件
  if (!locationFile.value) {
    ElMessage.error('请上传地点数据文件 (CSV)')
    return
  }

  if (!eventsFile.value) {
    ElMessage.error('请上传事件数据文件 (JSON)')
    return
  }

  clustering.value = true
  clusteringError.value = ''

  try {
    // 读取地点文件
    const locationContent = await readFile(locationFile.value)
    
    // 读取事件文件
    const eventsContent = await readFile(eventsFile.value)

    // 验证JSON格式
    try {
      JSON.parse(eventsContent)
    } catch (e) {
      throw new Error('事件数据文件不是有效的JSON格式')
    }

    // 调用API，传递文件名
    const response = await fetch(`${apiBaseUrl}/analysis/event-cluster/cluster`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        locationData: locationContent,
        eventsData: eventsContent,
        locationFileName: locationFile.value.name,
        eventsFileName: eventsFile.value.name
      })
    })

    const result = await response.json()

    if (result.status === 'success') {
      clusteringResults.value = result.data
      clusteringResults.value.analysisId = result.analysisId
      ElMessage.success('聚类分析完成')
      console.log('聚类结果:', result.data)
    } else {
      clusteringError.value = result.message || '聚类分析失败'
      ElMessage.error(clusteringError.value)
    }
  } catch (error) {
    clusteringError.value = `错误: ${error.message}`
    ElMessage.error(clusteringError.value)
    console.error('聚类分析异常:', error)
  } finally {
    clustering.value = false
  }
}

/**
 * 读取文件内容
 */
const readFile = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      resolve(e.target.result)
    }
    reader.onerror = () => {
      reject(new Error('文件读取失败'))
    }
    reader.readAsText(file)
  })
}

/**
 * 加载事件数据
 */
const loadEventData = () => {
  // 模拟数据
  events.value = [
    { time: '秦二世元年（前209年）', title: '斩蛇起义', content: '高祖醉酒，夜径泽中，令一人行前。行前者还报曰："前有大蛇当径，愿还。"高祖醉，曰："壮士行，何畏！"乃前，拔剑击斩蛇。', roles: ['刘邦'], color: '#8e3e3e' },
    { time: '汉元年（前206年）', title: '鸿门宴', content: '项羽大怒，欲击刘邦。沛公左司马曹无伤使人言于项羽... 沛公旦日从百余骑来见项王。', roles: ['项羽', '刘邦', '范增', '项庄'], color: '#b8860b' },
    { time: '汉五年（前202年）', title: '垓下之战', content: '项王军壁垓下，兵少食尽，汉军及诸侯兵围之数重。夜闻汉军四面皆楚歌，项王乃大惊。', roles: ['项羽', '虞姬'], color: '#2b4b64' }
  ]
}

/**
 * 处理历史记录面板的查看结果事件
 */
const handleViewHistoryResults = (data) => {
  if (data && data.data) {
    clusteringResults.value = data.data
    clusteringResults.value.analysisId = data.analysisId
    activeTab.value = 'clustering'
    ElMessage.success('已加载历史记录结果')
  }
}

/**
 * 处理重新运行分析完成事件
 */
const handleRerunComplete = (data) => {
  if (data && data.data) {
    clusteringResults.value = data.data
    clusteringResults.value.analysisId = data.analysisId
    activeTab.value = 'clustering'
    showHistoryPanel.value = false
    ElMessage.success('重新运行分析完成，已显示结果')
  }
}
</script>

<style scoped>
.analysis-container { 
  height: 100%; 
  display: flex; 
  flex-direction: column;
  background: #fcf9f2;
}

/* 标签页相关 */
:deep(.el-tabs) {
  height: 100%;
}

:deep(.el-tabs__content) {
  height: calc(100% - 40px);
  overflow-y: auto;
}

:deep(.el-tab-pane) {
  height: 100%;
}

/* 事件时线标签页 */
.header-row { 
  display: flex; 
  justify-content: space-between; 
  padding-bottom: 10px; 
  border-bottom: 2px solid #e6dcc8; 
  margin-bottom: 20px; 
}

.gufeng-title { 
  color: #5e482d; 
  border-left: 4px solid #8e3e3e; 
  padding-left: 15px; 
  margin: 0; 
}

.gufeng-btn { 
  background: #8e3e3e; 
  border: none; 
  font-family: "KaiTi"; 
}

.timeline-workspace { 
  flex: 1; 
  overflow-y: auto; 
  padding: 20px 100px; 
  background: #fcf9f2; 
}

.event-card { 
  border: 1px solid #e6dcc8; 
  background: #fffdf6; 
}

.event-title { 
  color: #8e3e3e; 
  font-size: 18px; 
  margin: 0 0 10px 0; 
  font-family: "KaiTi"; 
}

.event-desc { 
  color: #555; 
  line-height: 1.6; 
}

.event-tags { 
  margin-top: 10px; 
  display: flex; 
  gap: 5px; 
}

.empty-state { 
  text-align: center; 
  color: #ccc; 
  padding-top: 100px; 
}

/* 聚类分析标签页 */
.clustering-container {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.task-creation-panel {
  max-width: 900px;
  margin: 0 auto;
}

.task-card {
  border: 1px solid #e6dcc8;
  background-color: #fffdf6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #5e482d;
  font-family: "KaiTi";
}

.upload-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-bottom: 30px;
  padding: 10px;
}

.upload-box {
  display: flex;
  flex-direction: column;
}

.upload-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  color: #5e482d;
}

.upload-icon {
  font-size: 18px;
  margin-right: 8px;
  color: #8e3e3e;
}

.upload-label {
  font-weight: 600;
  font-size: 14px;
}

.custom-upload :deep(.el-upload-dragger) {
  border: 2px dashed #d4a574;
  background: #fff;
  border-radius: 8px;
  padding: 30px 10px;
  transition: all 0.3s;
}

.custom-upload :deep(.el-upload-dragger:hover) {
  border-color: #8e3e3e;
  background: #fdfbf7;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.el-icon--upload {
  font-size: 48px;
  color: #d4a574;
  margin-bottom: 10px;
}

.task-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.action-btn {
  min-width: 120px;
}

.primary-btn {
  background: #8e3e3e;
  border-color: #8e3e3e;
}

.primary-btn:hover {
  background: #a84747;
  border-color: #a84747;
}

.primary-btn:disabled {
  background: #dcdfe6;
  border-color: #dcdfe6;
}

.task-tips {
  margin-top: 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #666;
}

/* 滚动条美化 */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #dcc8a6; border-radius: 3px; }

.clustering-container::-webkit-scrollbar { width: 6px; }
.clustering-container::-webkit-scrollbar-thumb { background: #dcc8a6; border-radius: 3px; }

/* 响应式设计 */
@media (max-width: 1200px) {
  .upload-grid {
    grid-template-columns: 1fr;
  }

  .timeline-workspace {
    padding: 20px 50px;
  }
}
</style>