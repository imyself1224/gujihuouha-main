<template>
  <div class="sidebar">
    <div class="logo-area">
      <div class="logo-seal">古籍</div>
      <div class="logo-text">
        <div class="main-title">智·析</div>
        <div class="sub-title">知识图谱平台</div>
      </div>
    </div>

    <div class="menu-section">
      <div class="menu-group-title">数据层</div>
      <ul class="nav-menu">
        <li :class="{ active: activeView === 'process' }" @click="$emit('change-view', 'process')">
          <el-icon class="menu-icon"><EditPen /></el-icon> 文本清洗工作台
        </li>
        <li :class="{ active: activeView === 'library' }" @click="$emit('change-view', 'library')">
          <el-icon class="menu-icon"><Collection /></el-icon> 珍藏语料库
        </li>
      </ul>
    </div>

    <div class="menu-section analysis-section">
      <div class="menu-group-title">分析层</div>
      <ul class="nav-menu custom-scrollbar scrollable-list">
        <li :class="{ active: activeView === 'ner' }" @click="$emit('change-view', 'ner')">
          <el-icon class="menu-icon"><PriceTag /></el-icon> 命名实体识别
        </li>
        <li :class="{ active: activeView === 'relation' }" @click="$emit('change-view', 'relation')">
          <el-icon class="menu-icon"><Connection /></el-icon> 人物关系抽取
        </li>
        <li :class="{ active: activeView === 'event-extraction' }" @click="$emit('change-view', 'event-extraction')">
          <el-icon class="menu-icon"><Timer /></el-icon> 事件信息抽取
        </li>
        <li :class="{ active: activeView === 'event-relation' }" @click="$emit('change-view', 'event-relation')">
          <el-icon class="menu-icon"><Connection /></el-icon> 事件关系识别
        </li>
        <li :class="{ active: activeView === 'portrait' }" @click="$emit('change-view', 'portrait')">
          <el-icon class="menu-icon"><User /></el-icon> 人物画像生成
        </li>
        <li :class="{ active: activeView === 'event-analysis' }" @click="$emit('change-view', 'event-analysis')">
          <el-icon class="menu-icon"><Management /></el-icon> 事件时空聚类
        </li>
        <li :class="{ active: activeView === 'his-analysis' }" @click="$emit('change-view', 'his-analysis')">
          <el-icon class="menu-icon"><Histogram /></el-icon> 历史事件群像
        </li>
        <li :class="{ active: activeView === 'graph' }" @click="$emit('change-view', 'graph')">
          <el-icon class="menu-icon"><Share /></el-icon> 古籍故事表达
        </li>
      </ul>
    </div>

    <div class="menu-section">
      <div class="menu-group-title">典籍工具</div>
      <ul class="nav-menu">
        <li :class="{ active: activeView === 'dict' }" @click="$emit('change-view', 'dict')">
          <el-icon class="menu-icon"><Reading /></el-icon> 中华词典检索
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
// 1. 在这里补充引入 'Reading' 图标
import { EditPen, Collection, PriceTag, Connection, Timer, User, Reading, Management, Histogram, Share } from '@element-plus/icons-vue'

defineProps(['activeView'])
defineEmits(['change-view'])
</script>

<style scoped>
/* 保持原有的 sidebar 样式，新增一点样式 */
.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #2b303b 0%, #1a1d24 100%);
  color: #e0d6c3;
  display: flex; flex-direction: column; z-index: 10;
}
.logo-area {
  height: 100px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: rgba(0,0,0,0.1);
  border-bottom: 1px solid #3d4450;
  transition: all 0.4s ease;
  cursor: pointer;
}

.logo-area:hover {
  background: rgba(255, 255, 255, 0.05);
}

.logo-area:hover .logo-seal {
  transform: scale(1.1);
}

.logo-seal {
  width: 48px;
  height: 48px;
  background-color: #a83b3b;
  color: #fff;
  font-size: 24px;
  font-weight: bold;
  border: 2px solid #852b2b;
  margin-right: 15px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 4px;
  font-family: "KaiTi";
  transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.logo-text .main-title { font-size: 22px; color: #cdab84; letter-spacing: 2px; }
.logo-text .sub-title { font-size: 12px; color: #8a96a3; }

.nav-menu { list-style: none; padding: 0; margin: 0; }
.menu-section { margin-bottom: 30px; flex: 0 0 auto; }
/* 自动适应高度，保留滚动条以防屏幕过小 */
.scrollable-list { max-height: 55vh; overflow-y: auto; }
.menu-group-title { padding: 15px 20px 5px; font-size: 12px; color: #5c6b7f; letter-spacing: 1px; }

.nav-menu li {
  padding: 15px 30px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex;
  align-items: center;
  font-size: 15px;
  color: #909399;
}

.nav-menu li:hover {
  color: #e0d6c3;
  background: rgba(255,255,255,0.05);
}

.nav-menu li.active { color: #cdab84; background: linear-gradient(90deg, rgba(205,171,132,0.1) 0%, transparent 100%); border-right: 3px solid #cdab84; }
.menu-icon { margin-right: 10px; font-size: 16px; }
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #3d4450; }
</style>