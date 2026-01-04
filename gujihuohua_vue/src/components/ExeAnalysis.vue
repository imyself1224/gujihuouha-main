<template>
  <div class="event-analysis-container">
    <div class="main-layout">
      <!-- 左侧：文本输入 -->
      <div class="left-panel">
        <div class="panel-card input-card">
          <div class="card-header">
            <div class="header-left">
              <el-icon><EditPen /></el-icon>
              <span class="title">文本输入</span>
            </div>
          </div>
          
          <div class="card-body input-body">
            <el-input
                v-model="queryForm.text"
                type="textarea"
                placeholder="请输入古籍原文..."
                class="ancient-textarea"
                resize="none"
                show-word-limit
                maxlength="1000"
            />
          </div>

          <div class="card-footer">
            <div class="footer-left">
              <el-button plain size="default" @click="fillExample">
                <el-icon><Document /></el-icon> 填入示例
              </el-button>
              <el-button plain size="default" @click="clearText">
                <el-icon><Delete /></el-icon> 清空
              </el-button>
            </div>
            <div class="footer-right">
              <el-button type="primary" color="#8e3e3e" size="default" @click="queryEvent" :loading="loading">
                <el-icon v-if="!loading"><VideoPlay /></el-icon> 开始抽取
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：分析结果 -->
      <div class="right-panel">
        <div class="panel-card result-card">
          <div class="card-header">
            <div class="header-left">
              <el-icon><DataAnalysis /></el-icon>
              <span class="title">分析结果</span>
            </div>
            <div class="header-right" v-if="queryResult && queryResult.found">
              <el-tag type="success" effect="light" round class="count-tag">
                共找到 {{ queryResult.event_list?.length || 0 }} 个事件
              </el-tag>
            </div>
          </div>

          <div class="card-body result-body" v-loading="loading">
            <!-- 初始空状态 -->
            <div v-if="!queryResult && !loading" class="empty-state">
              <el-empty description="请在左侧输入文本并开始抽取" :image-size="140" />
            </div>

            <!-- 有结果 -->
            <div v-else-if="queryResult" class="result-content">
              <!-- 原文片段 -->
              <div class="section-block">
                <div class="section-title">原文片段</div>
                <div class="origin-text-box">
                  {{ queryResult.text || queryForm.text }}
                </div>
              </div>

              <!-- 抽取详情 -->
              <div class="section-block">
                <div class="section-title">抽取详情</div>
                
                <div v-if="!queryResult.found" class="not-found">
                  <el-result icon="info" title="未找到事件" sub-title="当前文本中未检测到相关事件" />
                </div>

                <div v-else class="event-list">
                  <div v-for="(event, index) in queryResult.event_list" :key="index" class="event-item">
                    <!-- 事件头部：类型与触发词 -->
                    <div class="event-top-row">
                      <div class="event-type-badge">{{ event.event_type }}</div>
                      <div class="trigger-info">
                        <span class="trigger-label">触发词</span>
                        <span class="trigger-word">{{ event.trigger }}</span>
                      </div>
                    </div>

                    <!-- 论元列表 -->
                    <div class="args-row">
                      <div v-for="(arg, argIdx) in event.arguments" :key="argIdx" class="arg-pill">
                        <span class="arg-role">{{ arg.role }}</span>
                        <span class="arg-val">{{ arg.argument }}</span>
                      </div>
                      <div v-if="!event.arguments || event.arguments.length === 0" class="no-args-text">
                        暂无论元
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  EditPen, 
  Document, 
  Delete, 
  VideoPlay, 
  DataAnalysis 
} from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8080/api/analysis/event-extraction'

// ===== 状态管理 =====
const loading = ref(false)
const queryForm = reactive({
  text: '',
  dataset: 'Hangaozubenji'
})

const queryResult = ref(null)




// ===== 示例文本 =====
const examples = [
  '其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。'
]

// ===== 方法 =====

/**
 * 查询事件
 */
const queryEvent = async () => {
  if (!queryForm.text.trim()) {
    ElMessage.warning('请输入古籍原文')
    return
  }

  loading.value = true
  try {
    const response = await axios.post(`${API_BASE}/query-by-text`, {
      text: queryForm.text,
      dataset: queryForm.dataset
    })

    queryResult.value = response.data
    if (response.data.found) {
      ElMessage.success('成功找到事件标注数据')
    } else {
      ElMessage.info('未找到匹配的训练数据')
    }
  } catch (error) {
    console.error('查询失败:', error)
    queryResult.value = {
      status: 'error',
      message: error.response?.data?.message || '查询失败，请检查网络连接',
      found: false
    }
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

/**
 * 填入示例
 */
const fillExample = () => {
  const example = examples[Math.floor(Math.random() * examples.length)]
  queryForm.text = example
}

/**
 * 清空文本
 */
const clearText = () => {
  queryForm.text = ''
  queryResult.value = null
}





// 组件初始化
// initStats()
</script>

<style scoped>
.event-analysis-container {
  height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.main-layout {
  display: flex;
  gap: 20px;
  height: 100%;
  max-width: 1600px;
  margin: 0 auto;
}

/* 通用卡片样式 */
.panel-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 左侧面板 */
.left-panel {
  flex: 0 0 380px;
  min-width: 300px;
}

.input-body {
  display: flex;
  flex-direction: column;
}

.ancient-textarea {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.ancient-textarea :deep(.el-textarea__inner) {
  flex: 1;
  resize: none;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  font-size: 15px;
  line-height: 1.6;
  font-family: "KaiTi", "楷体", serif;
  background-color: #fafafa;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.03);
}

.ancient-textarea :deep(.el-textarea__inner):focus {
  background-color: #fff;
  border-color: #8e3e3e;
}

.card-footer {
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
}

.footer-left {
  display: flex;
  gap: 10px;
}

/* 右侧面板 */
.right-panel {
  flex: 1;
  min-width: 0; /* 防止 flex 子项溢出 */
}

.count-tag {
  font-weight: normal;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #909399;
  padding-left: 4px;
}

.origin-text-box {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 6px;
  font-family: "KaiTi", "楷体", serif;
  font-size: 16px;
  line-height: 1.8;
  color: #606266;
  border: 1px solid #ebeef5;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.event-item {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 20px;
  background-color: #fff;
  transition: all 0.3s;
}

.event-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border-color: #e4e7ed;
}

.event-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #ebeef5;
}

.event-type-badge {
  background-color: #8e3e3e;
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

.trigger-info {
  font-size: 14px;
  color: #606266;
}

.trigger-word {
  font-weight: bold;
  color: #303133;
  margin-left: 6px;
  font-family: "KaiTi", "楷体", serif;
}

.args-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.arg-pill {
  display: inline-flex;
  align-items: center;
  background-color: #f4f4f5;
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 13px;
}

.arg-role {
  color: #909399;
  margin-right: 8px;
}

.arg-val {
  color: #303133;
  font-weight: 600;
  font-family: "KaiTi", "楷体", serif;
}

.no-args-text {
  color: #c0c4cc;
  font-size: 13px;
  font-style: italic;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

/* 响应式 */
@media (max-width: 1000px) {
  .main-layout {
    flex-direction: column;
    height: auto;
    overflow-y: auto;
  }

  .left-panel {
    flex: none;
    height: 500px;
  }

  .right-panel {
    flex: none;
    min-height: 500px;
  }
  
  .event-analysis-container {
    height: auto;
    min-height: 100vh;
  }
}
</style>
