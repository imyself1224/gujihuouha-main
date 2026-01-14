<template>
  <div class="analysis-container fade-in">
    <h2 class="gufeng-title">古籍人物画像生成与分析</h2>

    <div class="portrait-workspace">
      <div class="control-panel">
        <div class="header-left">
          <span>特征提取</span>
          <el-button type="primary" link @click="fillExample" style="margin-left: 10px;">(填入示例)</el-button>
        </div>
        <el-form label-position="top">
          <el-form-item label="选取人物文本描述">
            <el-input type="textarea" :rows="6" v-model="desc" class="ancient-input" placeholder="请输入古籍原句..."></el-input>
            <div class="auto-tip" style="margin-top: 10px;">
              <el-alert title="系统将自动识别实体并推断关系" type="info" :closable="false" show-icon />
            </div>
          </el-form-item>
          <el-button type="primary" class="generate-btn" @click="generate" :loading="loading">
            <el-icon><Brush /></el-icon> 丹青绘制与分析
          </el-button>
        </el-form>
      </div>

      <div class="result-panel">
        <div v-if="!generated" class="placeholder-content">
          <el-empty description="请在左侧输入文本并点击生成" />
        </div>
        <div v-else class="analysis-content fade-in">
          <el-tabs v-model="activeTab" type="border-card" class="analysis-tabs">
            <el-tab-pane label="实体识别" name="entities">
              <div class="entity-group" v-for="(items, type) in entities" :key="type">
                <h3 class="entity-title">{{ getEntityLabel(type) }}</h3>
                <div class="tags-box">
                  <el-tag v-for="(item, index) in items" :key="index" :type="getEntityType(type)" effect="light" class="entity-tag">
                    {{ item.text }}
                  </el-tag>
                  <span v-if="items.length === 0" class="no-data">无</span>
                </div>
              </div>
            </el-tab-pane>
            
            <el-tab-pane label="语义相似度" name="similarity">
              <el-table :data="similarityResults" style="width: 100%" stripe height="500">
                <el-table-column prop="entity1" label="实体一" width="120" />
                <el-table-column prop="entity2" label="实体二" width="120" />
                <el-table-column prop="type" label="关系类型" width="150">
                  <template #default="scope">
                    {{ getRelationTypeLabel(scope.row.type) }}
                  </template>
                </el-table-column>
                <el-table-column prop="similarity" label="相似度" sortable>
                  <template #default="scope">
                    <el-progress :percentage="Math.round(scope.row.similarity * 100)" :color="customColors" />
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            
            <el-tab-pane label="共现分析" name="cooccurrence">
              <el-table :data="cooccurrenceResults" style="width: 100%" stripe height="500">
                <el-table-column prop="entity1" label="实体一" width="120" />
                <el-table-column prop="entity2" label="实体二" width="120" />
                <el-table-column prop="count" label="共现次数" sortable />
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref, computed } from 'vue'
import { Brush } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const desc = ref('')
const loading = ref(false)
const generated = ref(false)
const activeTab = ref('entities')
const analysisData = ref(null)

const entities = computed(() => {
  if (!analysisData.value) return {}
  // Prefer extracted entities from similarity as they seem cleaner in the example
  return analysisData.value.similarity?.extracted_entities || {}
})

const similarityResults = computed(() => {
  if (!analysisData.value) return []
  return analysisData.value.similarity?.top_results || []
})

const cooccurrenceResults = computed(() => {
  if (!analysisData.value) return []
  return analysisData.value.cooccurrence?.top_results || []
})

const customColors = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 },
]

const fillExample = () => {
  desc.value = '高祖，沛丰邑中阳里人，姓刘氏，字季。'
}

const getEntityLabel = (type) => {
  const map = {
    'PER': '人物 (PER)',
    'LOC': '地点 (LOC)',
    'OFI': '官职 (OFI)',
    'TIME': '时间 (TIME)'
  }
  return map[type] || type
}

const getEntityType = (type) => {
  const map = {
    'PER': 'danger',
    'LOC': 'success',
    'OFI': 'warning',
    'TIME': 'info'
  }
  return map[type] || ''
}

const getRelationTypeLabel = (type) => {
  const map = {
    'PER-PER': '人物-人物',
    'PER-LOC': '人物-地点',
    'PER-OFI': '人物-官职',
    'PER-TIME': '人物-时间',
    'LOC-LOC': '地点-地点',
    'LOC-PER': '地点-人物',
    'LOC-OFI': '地点-官职',
    'LOC-TIME': '地点-时间',
    'OFI-PER': '官职-人物',
    'OFI-LOC': '官职-地点',
    'OFI-OFI': '官职-官职',
    'OFI-TIME': '官职-时间',
    'TIME-PER': '时间-人物',
    'TIME-LOC': '时间-地点',
    'TIME-OFI': '时间-官职',
    'TIME-TIME': '时间-时间'
  }
  return map[type] || type
}

const generate = async () => {
  if (!desc.value) return ElMessage.warning('请输入描述')
  loading.value = true
  try {
    const res = await axios.post('http://localhost:8080/api/analysis/pof/generate', { text: desc.value })
    
    if (res.data.port5002Response && res.data.port5002Response.data) {
      analysisData.value = res.data.port5002Response.data
      generated.value = true
      activeTab.value = 'entities'
      ElMessage.success('分析成功')
    } else {
      ElMessage.warning('未获取到有效分析结果')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('生成失败: ' + (e.response?.data?.error || e.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.analysis-container { height: 100%; display: flex; flex-direction: column; }
.gufeng-title { color: #5e482d; border-left: 4px solid #8e3e3e; padding-left: 15px; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; margin-bottom: 20px; font-size: 18px; color: #5e482d; font-weight: bold; }
.portrait-workspace { flex: 1; display: flex; gap: 30px; overflow: hidden; }
.control-panel { width: 350px; background: #fff; padding: 20px; border: 1px solid #e6dcc8; border-radius: 4px; display: flex; flex-direction: column; }
.result-panel { flex: 1; background: #fff; border-radius: 4px; border: 1px solid #e6dcc8; padding: 20px; overflow: hidden; display: flex; flex-direction: column; }

.placeholder-content { flex: 1; display: flex; justify-content: center; align-items: center; }
.analysis-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.analysis-tabs { flex: 1; display: flex; flex-direction: column; }
.analysis-tabs :deep(.el-tabs__content) { flex: 1; overflow-y: auto; }

.ancient-input :deep(.el-textarea__inner) { font-family: "KaiTi"; font-size: 16px; background: #fafafa; }
.generate-btn { width: 100%; background: #8e3e3e; border-color: #8e3e3e; height: 45px; font-size: 16px; font-family: "KaiTi"; letter-spacing: 4px; }

.entity-group { margin-bottom: 20px; }
.entity-title { font-size: 16px; color: #5e482d; margin-bottom: 10px; border-bottom: 1px dashed #e6dcc8; padding-bottom: 5px; }
.tags-box { display: flex; flex-wrap: wrap; gap: 10px; }
.entity-tag { font-size: 14px; }
.no-data { color: #999; font-size: 14px; font-style: italic; }

.fade-in { animation: fadeIn 0.5s; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>