<template>
  <div class="analysis-container fade-in">
    <h2 class="gufeng-title">古籍事件关系识别</h2>

    <div class="main-layout">
      <!-- 左侧：输入区域 -->
      <div class="input-panel paper-texture">
        <div class="panel-header">
          <span class="panel-title">事件关系分析</span>
          <el-button type="primary" link @click="fillExample" class="example-btn">
            <el-icon><EditPen /></el-icon> 填入示例
          </el-button>
        </div>

        <el-form :model="singleForm" label-position="top" class="analysis-form">
          <el-form-item label="古籍原句">
            <el-input 
              v-model="singleForm.text" 
              type="textarea" 
              :rows="6" 
              class="ancient-input" 
              placeholder="请输入待分析的古籍文本..." 
            />
          </el-form-item>

          <div class="trigger-row">
            <el-form-item label="头部触发词 (Head)" class="trigger-item">
              <el-input v-model="singleForm.head_trigger" placeholder="如：令" :prefix-icon="ArrowLeft" />
            </el-form-item>
            <div class="trigger-arrow">
              <el-icon><Right /></el-icon>
            </div>
            <el-form-item label="尾部触发词 (Tail)" class="trigger-item">
              <el-input v-model="singleForm.tail_trigger" placeholder="如：入" :prefix-icon="ArrowRight" />
            </el-form-item>
          </div>

          <div class="action-area">
            <el-button type="primary" class="gufeng-btn run-btn" @click="predictManual" :loading="singleLoading">
              <el-icon style="margin-right:8px"><Connection /></el-icon> 开始识别
            </el-button>
          </div>
        </el-form>
      </div>

      <!-- 右侧：结果展示 -->
      <div class="result-panel">
        <div v-if="!singleResultStr" class="empty-state">
          <div class="empty-icon-bg">
            <el-icon :size="60" color="#dcc8a6"><Connection /></el-icon>
          </div>
          <p class="empty-text">请输入文本并点击识别</p>
          <p class="empty-subtext">系统将分析两个触发词之间的语义关系</p>
        </div>

        <div v-else class="result-content fade-in">
          <!-- 核心结果卡片 -->
          <div class="result-card">
            <div class="card-label">识别结果</div>
            <div class="relation-display">
              <div class="trigger-box head">{{ singleForm.head_trigger }}</div>
              <div class="relation-arrow">
                <div class="relation-tag" :class="getRelationClass(singleResultStr)">
                  {{ singleResultStr }}
                </div>
                <div class="arrow-line"></div>
              </div>
              <div class="trigger-box tail">{{ singleForm.tail_trigger }}</div>
            </div>
          </div>

          <!-- 置信度分析 -->
          <div class="prob-card">
            <div class="card-label">置信度分析</div>
            <div class="prob-list">
              <div v-for="(prob, type) in singleProbabilities" :key="type" class="prob-item">
                <div class="prob-info">
                  <span class="prob-name">{{ type }}</span>
                  <span class="prob-val">{{ (prob * 100).toFixed(2) }}%</span>
                </div>
                <el-progress 
                  :percentage="Math.round(prob * 100)" 
                  :color="getProbColor(type)" 
                  :stroke-width="10"
                  :show-text="false"
                />
              </div>
            </div>
          </div>

          <!-- 解释说明 -->
          <div class="desc-card">
            <div class="card-label">关系说明</div>
            <p class="desc-text" v-if="singleResultStr === '因果'">
              <el-icon><InfoFilled /></el-icon> 
              <strong>因果关系：</strong> 表示前一个事件是后一个事件的原因，或者后一个事件是前一个事件的结果。
            </p>
            <p class="desc-text" v-else-if="singleResultStr === '并列'">
              <el-icon><InfoFilled /></el-icon> 
              <strong>并列关系：</strong> 表示两个事件地位平等，同时发生或无明显时间先后顺序。
            </p>
            <p class="desc-text" v-else-if="singleResultStr === '顺承'">
              <el-icon><InfoFilled /></el-icon> 
              <strong>顺承关系：</strong> 表示两个事件按照时间顺序依次发生，前一个事件结束后，后一个事件紧接着发生。
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref, reactive } from 'vue'
import { Connection, Right, EditPen, ArrowLeft, ArrowRight, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 状态变量
const singleLoading = ref(false)
const singleResultStr = ref('')
const singleProbabilities = ref({})
const singleForm = reactive({ 
  text: '', 
  head_trigger: '', 
  tail_trigger: '' 
})

// 填入示例
const fillExample = () => {
  singleForm.text = '项羽怨怀王不肯令与沛公俱西入关，而北救赵，後天下约。'
  singleForm.head_trigger = '令'
  singleForm.tail_trigger = '入'
  singleResultStr.value = '' // 清空上次结果
  singleProbabilities.value = {}
}

// 执行预测
const predictManual = async () => {
  if (!singleForm.text || !singleForm.head_trigger || !singleForm.tail_trigger) {
    return ElMessage.warning('请填写完整信息：原句、头部触发词、尾部触发词')
  }
  
  singleLoading.value = true
  singleResultStr.value = ''
  singleProbabilities.value = {}
  
  try {
    const payload = {
      text: singleForm.text,
      head_trigger: singleForm.head_trigger,
      tail_trigger: singleForm.tail_trigger
    }
    
    // 调用 Spring Boot API
    const res = await axios.post('http://localhost:8080/api/analysis/event-relation/predict', payload)
    
    if (res.data.status === 'success') {
      singleResultStr.value = res.data.predicted_relation
      singleProbabilities.value = res.data.probabilities
      ElMessage.success('识别成功')
    } else {
      let errorMsg = res.data.error || '未知错误'
      if (errorMsg.includes('Could not locate entities in text')) {
        errorMsg = '无法在原句中找到指定的触发词，请检查头部和尾部触发词是否正确。'
      }
      ElMessage.error('识别失败: ' + errorMsg)
    }
  } catch (e) {
    console.error(e)
    let errorMsg = e.response?.data?.error || e.message
    if (errorMsg && errorMsg.includes('Could not locate entities in text')) {
       errorMsg = '无法在原句中找到指定的触发词，请检查头部和尾部触发词是否正确。'
    }
    ElMessage.error('调用失败: ' + errorMsg)
  } finally {
    singleLoading.value = false
  }
}

// 辅助函数：获取关系对应的样式类
const getRelationClass = (relation) => {
  const map = {
    '因果': 'tag-causality',
    '并列': 'tag-parallel',
    '顺承': 'tag-succession'
  }
  return map[relation] || 'tag-default'
}

// 辅助函数：获取进度条颜色
const getProbColor = (type) => {
  const map = {
    '因果': '#f56c6c', // 红色
    '并列': '#e6a23c', // 黄色
    '顺承': '#67c23a'  // 绿色
  }
  return map[type] || '#409eff'
}
</script>

<style scoped>
.analysis-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0 20px 20px;
}

.gufeng-title {
  color: #5e482d;
  border-left: 4px solid #8e3e3e;
  padding-left: 15px;
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: bold;
}

.main-layout {
  flex: 1;
  display: flex;
  gap: 30px;
  overflow: hidden;
}

/* 左侧输入面板 */
.input-panel {
  width: 450px;
  background: #fff;
  border: 1px solid #e6dcc8;
  border-radius: 8px;
  padding: 25px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.paper-texture {
  background-image: url("data:image/svg+xml,%3Csvg width='64' height='64' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M8 16c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm0-2c3.314 0 6-2.686 6-6s-2.686-6-6-6-6 2.686-6 6 2.686 6 6 6zm33.414-6l5.95-5.95L45.95.636 38.536 8.05 39.95 9.464l7.464-7.464zM12 12h4v4h-4v-4zm32 32h4v4h-4v-4zm-16-16h4v4h-4v-4zm-16 16h4v4h-4v-4zm32-32h4v4h-4v-4z' fill='%23d6d3c9' fill-opacity='0.15' fill-rule='evenodd'/%3E%3C/svg%3E");
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  border-bottom: 1px dashed #e6dcc8;
  padding-bottom: 15px;
}

.panel-title {
  font-size: 18px;
  font-weight: bold;
  color: #5e482d;
}

.ancient-input :deep(.el-textarea__inner) {
  font-family: "KaiTi", "STKaiti", serif;
  font-size: 18px;
  line-height: 1.8;
  background-color: #fafafa;
  border-color: #dcdfe6;
  padding: 15px;
}

.trigger-row {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 10px;
}

.trigger-item {
  flex: 1;
  margin-bottom: 0 !important;
}

.trigger-arrow {
  color: #909399;
  font-size: 20px;
  margin-top: 30px; /* Align with input box */
}

.action-area {
  margin-top: 30px;
}

.run-btn {
  width: 100%;
  height: 48px;
  font-size: 18px;
  letter-spacing: 4px;
  background-color: #8e3e3e;
  border-color: #8e3e3e;
  transition: all 0.3s;
}

.run-btn:hover {
  background-color: #a64d4d;
  border-color: #a64d4d;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(142, 62, 62, 0.3);
}

/* 右侧结果面板 */
.result-panel {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e6dcc8;
  padding: 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.empty-state {
  text-align: center;
  color: #909399;
}

.empty-icon-bg {
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-text {
  font-size: 18px;
  margin-bottom: 10px;
  color: #606266;
}

.empty-subtext {
  font-size: 14px;
  color: #909399;
}

.result-content {
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.card-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 15px;
  font-weight: bold;
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* 结果卡片 */
.result-card {
  background: #fcf9f2;
  border: 1px solid #e6dcc8;
  border-radius: 8px;
  padding: 25px;
  text-align: center;
}

.relation-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}

.trigger-box {
  padding: 8px 20px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-family: "KaiTi", serif;
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  min-width: 80px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.relation-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  width: 120px;
}

.relation-tag {
  padding: 6px 16px;
  border-radius: 20px;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  z-index: 2;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.tag-causality { background: linear-gradient(135deg, #f56c6c, #ff9999); }
.tag-parallel { background: linear-gradient(135deg, #e6a23c, #f3d19e); }
.tag-succession { background: linear-gradient(135deg, #67c23a, #95d475); }
.tag-default { background: #909399; }

.arrow-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: #dcdfe6;
  z-index: 1;
}

.arrow-line::after {
  content: '';
  position: absolute;
  right: 0;
  top: -4px;
  width: 0;
  height: 0;
  border-left: 8px solid #dcdfe6;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
}

/* 置信度卡片 */
.prob-card {
  padding: 20px;
  border-top: 1px dashed #e6dcc8;
}

.prob-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.prob-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.prob-info {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.prob-name {
  font-weight: bold;
  color: #606266;
}

.prob-val {
  font-family: monospace;
  color: #303133;
}

/* 说明卡片 */
.desc-card {
  background: #f4f4f5;
  border-radius: 6px;
  padding: 15px;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.desc-text {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
