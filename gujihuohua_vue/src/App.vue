<template>
  <div class="app-root">
    <transition name="fade">
      <WelcomePage v-if="showWelcome" @enter="enterSystem" />
    </transition>

    <div class="app-container" v-if="!showWelcome">
      <SideMenu :active-view="activeView" @change-view="handleViewChange" />

      <div class="main-content">
        <keep-alive>
          <TextProcess
              v-if="activeView === 'process'"
              @save-record="handleSaveRecord"
          />
          <TextLibrary
              v-else-if="activeView === 'library'"
              ref="libraryRef"
          />
          <NerAnalysis v-else-if="activeView === 'ner'" />
          <RelationAnalysis v-else-if="activeView === 'relation'" />
          <EventExtractionAnalysis v-else-if="activeView === 'event-extraction'" />
          <EventRelationAnalysis v-else-if="activeView === 'event-relation'" />
          <PortraitAnalysis v-else-if="activeView === 'portrait'" />
          <EventAnalysis v-else-if="activeView === 'event-analysis'" />
          <HisAnalysis v-else-if="activeView === 'his-analysis'" />
          <XinhuaDict v-else-if="activeView === 'dict'" />
        </keep-alive>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import WelcomePage from './components/WelcomePage.vue'
import SideMenu from './components/SideMenu.vue'
import TextProcess from './components/TextProcess.vue'
import TextLibrary from './components/TextLibrary.vue'
import NerAnalysis from './components/NerAnalysis.vue'
import RelationAnalysis from './components/RelAnalysis.vue'
import EventExtractionAnalysis from './components/ExeAnalysis.vue'
import EventRelationAnalysis from './components/EriAnalysis.vue'
import PortraitAnalysis from './components/PofAnalysis.vue'
import EventAnalysis from './components/EventAnalysis.vue'
import HisAnalysis from './components/HisAnalysis.vue'
import XinhuaDict from './components/XinhuaDict.vue'

const showWelcome = ref(true)
const activeView = ref('process')
const libraryRef = ref(null)

const enterSystem = () => {
  showWelcome.value = false
}

const handleViewChange = (view) => {
  activeView.value = view
  // 如果切换到语料库，自动刷新列表
  if (view === 'library') {
    nextTick(() => {
      libraryRef.value?.fetchList()
    })
  }
}

const handleSaveRecord = () => {
  activeView.value = 'library'
  nextTick(() => {
    libraryRef.value?.fetchList()
  })
}
</script>

<style>
/* 全局样式设定 */
:root {
  --el-font-size-base: 16px !important;
  --el-text-line-height: 1.7 !important;
}

body, html {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  font-family: "KaiTi", "STKaiti", "BiauKai", "Microsoft YaHei", serif;
  font-size: 16px;
  background-color: #fcf9f2;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.gufeng-title { font-size: 28px !important; }
.el-table { font-size: 16px !important; }
.nav-menu li { font-size: 16px !important; }

/* 鼠标悬停动态效果 */
.hover-move {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.hover-move:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

/* 直接对常用组件应用效果 */
.el-button:hover,
.el-card:hover,
.list-item:hover,
.data-card:hover,
.panel-box:hover,
.upload-box:hover,
.entry-section:hover,
.word-header-box:hover,
.riddle-box:hover,
.answer-box:hover,
.stat-card:hover,
.sent-row:hover,
.text-line:hover,
.paper-bg:hover,
.viz-section > div:hover,
.chart-box:hover,
.event-card:hover,
.task-card:hover,
.el-tabs--border-card:hover,
.result-card:hover,
.prob-card:hover,
.desc-card:hover,
.cluster-card:hover,
.input-panel:hover,
.result-panel:hover,
.history-item:hover,
.el-tag:hover {
  transform: translateY(-5px) scale(1.01);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15) !important;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 10;
}

.el-button,
.el-card,
.list-item,
.data-card,
.panel-box,
.upload-box,
.entry-section,
.word-header-box,
.riddle-box,
.answer-box,
.stat-card,
.sent-row,
.text-line,
.paper-bg,
.viz-section > div,
.chart-box,
.event-card,
.task-card,
.el-tabs--border-card,
.result-card,
.prob-card,
.desc-card,
.cluster-card,
.input-panel,
.result-panel,
.history-item,
.el-tag {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
</style>

<style scoped>
.app-root { height: 100%; width: 100%; }
.app-container { display: flex; height: 100vh; width: 100vw; background-image: url("data:image/svg+xml,%3Csvg width='64' height='64' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M8 16c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm0-2c3.314 0 6-2.686 6-6s-2.686-6-6-6-6 2.686-6 6 2.686 6 6 6zm33.414-6l5.95-5.95L45.95.636 38.536 8.05 39.95 9.464l7.464-7.464zM12 12h4v4h-4v-4zm32 32h4v4h-4v-4zm-16-16h4v4h-4v-4zm-16 16h4v4h-4v-4zm32-32h4v4h-4v-4z' fill='%23d6d3c9' fill-opacity='0.4' fill-rule='evenodd'/%3E%3C/svg%3E"); }
.main-content { flex: 1; padding: 20px 30px; overflow: hidden; position: relative; }
.fade-leave-active { transition: opacity 0.8s; }
.fade-leave-to { opacity: 0; }
</style>