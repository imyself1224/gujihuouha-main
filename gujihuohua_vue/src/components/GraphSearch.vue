<template>
  <div class="graph-search-container">
    <div class="header">
      <h2 class="gufeng-title">古籍故事表达</h2>
      <div class="subtitle">全览与交互式分析</div>
    </div>

    <div class="content-wrapper">
      <el-row :gutter="20">
        <!-- Sidebar Controls -->
        <el-col :span="6">
          <div class="control-panel">
            <el-tabs v-model="activeTab" class="sidebar-tabs">
              <el-tab-pane label="节点列表" name="nodes">
                <div class="list-controls">
                   <el-input v-model="nodeFilter" placeholder="筛选节点..." :prefix-icon="Search" clearable />
                   <el-button type="primary" link @click="loadWholeGraph">Reset / 显示全部节点</el-button>
                </div>
                
                <el-scrollbar style="height: calc(100vh - 250px);">
                   <div v-if="filteredNodes.length === 0" class="empty-text">无数据</div>
                   
                   <div v-for="(nodes, label) in groupedNodes" :key="label" class="node-group-box">
                      <div class="group-header-card" @click="toggleGroup(label)">
                          <div class="header-left">
                             <el-icon class="arrow-icon" :class="{ 'is-active': expandedGroups[label] }"><ArrowRight /></el-icon>
                             <span class="badget" :style="{backgroundColor: getColor(label)}"></span>
                             <span class="group-title">{{ label }}</span>
                          </div>
                          <div class="header-right">
                             <el-button 
                                v-if="expandedGroups[label]" 
                                size="small" 
                                circle 
                                :icon="Aim" 
                                @click.stop="filterGraphByLabel(label)" 
                                title="在图谱中仅展示此类节点"
                                style="margin-right: 5px;"
                             />
                             <el-tag size="small" type="info" effect="plain" round>{{ nodes.length }} / {{ statsData.nodes_by_label[label] || '?' }}</el-tag>
                          </div>
                      </div>
                      
                      <div class="group-list-container" v-show="expandedGroups[label]">
                          <div 
                              v-for="node in (showAllState[label] ? nodes : nodes.slice(0, PREVIEW_LIMIT))" 
                              :key="node.id" 
                              class="node-item grouped-item" 
                              :class="{ active: selectedNode && selectedNode.id === node.id }"
                              @click="handleNodeClick(node)"
                              :title="getDisplayName(node)"
                          >
                              <span class="node-name">{{ getDisplayName(node) }}</span>
                          </div>
                          
                          <div v-if="nodes.length > PREVIEW_LIMIT" class="group-footer" @click.stop="toggleShowAll(label)">
                              <span>{{ showAllState[label] ? '收起' : `展示全部 (${nodes.length})` }}</span>
                              <el-icon class="footer-icon" :class="{ 'is-flipped': showAllState[label] }"><ArrowDown /></el-icon>
                          </div>
                      </div>
                   </div>
                </el-scrollbar>
              </el-tab-pane>

              <el-tab-pane label="关系列表" name="relations">
                 <div class="list-controls">
                   <el-input v-model="relationFilter" placeholder="筛选关系类型..." :prefix-icon="Search" clearable />
                   <el-button type="primary" link @click="loadAllRelationsGraph">Reset / 显示关系全图</el-button>
                </div>
                 <el-scrollbar style="height: calc(100vh - 250px);">
                    <div class="stats-list" style="padding:10px;">
                       <div v-if="!filteredRelationStats || Object.keys(filteredRelationStats).length === 0" class="empty-text">无数据</div>
                       
                       <div v-for="(count, type) in filteredRelationStats" :key="type" class="node-group-box">
                          <div class="group-header-card" @click="toggleRelationGroup(type)">
                              <div class="header-left">
                                 <el-icon class="arrow-icon" :class="{ 'is-active': expandedRelationGroups[type] }"><ArrowRight /></el-icon>
                                 <span class="badget" style="background-color: #f56c6c;"></span>
                                 <span class="group-title">{{ type }}</span>
                              </div>
                              <div class="header-right">
                                 <el-button 
                                    v-if="expandedRelationGroups[type]" 
                                    size="small" 
                                    circle 
                                    :icon="Aim" 
                                    @click.stop="filterGraphByRelation(type)" 
                                    title="在图谱中展示此类关系"
                                    style="margin-right: 5px;"
                                 />
                                 <el-tag size="small" type="info" effect="plain" round>{{ count }}</el-tag>
                              </div>
                          </div>
                          
                          <div class="group-list-container" v-show="expandedRelationGroups[type]">
                              <div v-if="!loadedRelations[type] && expandedRelationGroups[type]" style="padding:10px;text-align:center;color:#999;font-size:12px;">
                                  加载中...
                              </div>
                              <template v-else-if="loadedRelations[type]">
                                  <div 
                                      v-for="edge in (relationShowAllState[type] ? loadedRelations[type] : loadedRelations[type].slice(0, PREVIEW_LIMIT))" 
                                      :key="edge.id || `${edge.source}-${edge.relation_type}-${edge.target}`" 
                                      class="node-item grouped-item" 
                                      @click="handleEdgeClick(edge)"
                                      :title="`${edge.source} -> ${edge.target}`"
                                  >
                                      <span class="node-name" style="display:flex;align-items:center;">
                                        <span class="badget" :style="{backgroundColor: getEdgeNodeColor(edge.source_labels)}"></span>
                                        <span :title="edge.source">{{ edge.source }}</span>
                                        <span style="color:#999;font-size:10px;margin:0 8px;">-></span>
                                        <span class="badget" :style="{backgroundColor: getEdgeNodeColor(edge.target_labels)}"></span>
                                        <span :title="edge.target">{{ edge.target }}</span>
                                      </span>
                                  </div>
                                  
                                  <div v-if="loadedRelations[type].length > PREVIEW_LIMIT" class="group-footer" @click.stop="toggleRelationShowAll(type)">
                                      <span>{{ relationShowAllState[type] ? '收起' : `展示更多 (${loadedRelations[type].length})` }}</span>
                                      <el-icon class="footer-icon" :class="{ 'is-flipped': relationShowAllState[type] }"><ArrowDown /></el-icon>
                                  </div>
                              </template>
                          </div>
                       </div>
                    </div>
                 </el-scrollbar>
              </el-tab-pane>

              <el-tab-pane label="路径/高级" name="advanced">
                 <!-- Path Analysis -->
                 <div class="section-title">路径分析</div>
                 <div class="search-group">
                  <el-input v-model="pathSource" placeholder="起点" class="mb-2"></el-input>
                  <el-input v-model="pathTarget" placeholder="终点" class="mb-2"></el-input>
                  <el-button type="primary" class="w-100" @click="handleSearchPath" size="small">查询路径</el-button>
                 </div>
                 
                 <el-divider />
                 
                 <div class="section-title">子图挖掘</div>
                 <div class="search-group">
                   <el-input v-model="subgraphCenter" placeholder="中心节点" class="mb-2"></el-input>
                   <div class="flex-row">
                      <el-input-number v-model="subgraphDepth" :min="1" :max="3" size="small" style="width:100px"></el-input-number>
                      <el-button type="primary" size="small" @click="handleSearchSubgraph">挖掘</el-button>
                   </div>
                 </div>
              </el-tab-pane>

              <el-tab-pane label="统计" name="stats">
                  <div class="stats-list">
                     <div v-for="(count, label) in statsData.nodes_by_label" :key="label" class="stat-row">
                        <span class="badget" :style="{backgroundColor: getColor(label)}"></span>
                        <span>{{ label }}</span>
                        <span class="count">{{ count }}</span>
                     </div>
                  </div>
              </el-tab-pane>
            </el-tabs>

            <!-- Node Details Panel (Bottom relative) -->
            <div v-if="selectedNode" class="node-info-panel animated slideInUp">
               <div class="info-header">
                  <strong>{{ selectedNode.name }}</strong>
                  <el-button link size="small" type="danger" @click="selectedNode=null" :icon="Close" />
               </div>
               <div class="props-scroller">
                  <div v-for="(v, k) in selectedNode.properties" :key="k" class="prop-row">
                    <span class="key">{{ k }}:</span> <span class="val">{{ v }}</span>
                  </div>
               </div>
               <div class="actions">
                  <el-button size="small" type="primary" plain @click="expandNode(selectedNode, true)">扩展邻居</el-button>
               </div>
            </div>
          </div>
        </el-col>



        <!-- Main Graph Area -->
        <el-col :span="18">
           <div class="graph-canvas-wrapper" v-loading="loading">
              <div ref="chartDom" class="chart-container"></div>
              
              <div class="status-overlay">
                  当前展示: Nodes: {{ currentGraph.nodes.length }}, Edges: {{ currentGraph.edges.length }}
              </div>

              <div class="legend-overlay">
                 <div class="legend-item"><span class="dot" style="background:#5470c6"></span> Person</div>
                 <div class="legend-item"><span class="dot" style="background:#91cc75"></span> Location</div>
                 <div class="legend-item"><span class="dot" style="background:#fac858"></span> Event</div>
              </div>
           </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Close, ArrowRight, ArrowDown, Aim } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const activeTab = ref('nodes')
const loading = ref(false)
const API_BASE = 'http://localhost:8080/api'

// Data
const allNodes = ref([]) // For the list
const currentGraph = reactive({ nodes: [], edges: [] })
const selectedNode = ref(null)
const nodeFilter = ref('')

// Advanced Inputs
const pathSource = ref('')
const pathTarget = ref('')
const subgraphCenter = ref('')
const subgraphDepth = ref(1)
const statsData = reactive({ nodes_by_label: {}, relations_by_type: {} })

// Group Toggle State
const expandedGroups = reactive({
    'Person': true,
    'Location': true,
    'Event': false // Default collapsed as per user hint? Or just let user click.
})
const toggleGroup = (label) => {
    expandedGroups[label] = !expandedGroups[label]
}

// Show All State for long lists
const showAllState = reactive({})
const PREVIEW_LIMIT = 10

const toggleShowAll = async (label) => {
    // If we are expanding, check if we need to load more from Server
    if (!showAllState[label]) {
        const currentCount = groupedNodes.value[label] ? groupedNodes.value[label].length : 0
        const totalCount = statsData.nodes_by_label[label] || 0
        
        // If we have significantly fewer nodes than total, fetch them
        if (totalCount > currentCount && totalCount < 3000) { 
             loading.value = true
             try {
                const res = await fetch(`${API_BASE}/graph/nodes-by-label?label=${label}&limit=3000`)
                const data = await res.json()
                if (data.status === 'success') {
                    // Extract data (Handle both List and Map format)
                    let newNodes = []
                    let newEdges = []
                    
                    if (Array.isArray(data.data)) {
                        newNodes = data.data
                    } else if (data.data && data.data.nodes) {
                        newNodes = data.data.nodes
                        newEdges = data.data.relationships || []
                    }

                    // Merge new nodes into allNodes, avoiding duplicates
                    const existingIds = new Set(allNodes.value.map(n => String(n.id)))
                    let addedNodes = 0
                    
                    newNodes.forEach(n => {
                        const sid = String(n.id)
                        if (!existingIds.has(sid)) {
                             allNodes.value.push(n)
                             existingIds.add(sid)
                             addedNodes++
                        }
                    })

                    // Merge Edges
                    let currentEdges = [...(currentGraph.edges || [])]
                    const edgeSig = (e) => `${e.source}|${e.target}|${e.relation_type}`
                    const existingEdgeSigs = new Set(currentEdges.map(edgeSig))
                    let addedEdges = 0

                    newEdges.forEach(e => {
                        const sig = edgeSig(e)
                        if (!existingEdgeSigs.has(sig)) {
                            currentEdges.push(e)
                            existingEdgeSigs.add(sig)
                            addedEdges++
                        }
                    })

                    if (addedNodes > 0 || addedEdges > 0) {
                         ElMessage.success(`已加载 ${addedNodes} 个节点, ${addedEdges} 条关系`)
                         // Refresh Graph
                         renderGraph(allNodes.value, currentEdges)
                    } else {
                        ElMessage.info('没有更多新数据')
                    }
                }
             } catch(e) { console.error(e) } 
             finally { loading.value = false }
        }
    }
    showAllState[label] = !showAllState[label]
}

// Graph Filter by Group
const filterGraphByLabel = (label) => {
    // 1. Get all nodes of this label currently in list
    const targetNodes = groupedNodes.value[label] || []
    if (targetNodes.length === 0) return
    
    // 2. Render only these nodes
    // We also need edges between them? Or edges connected to them?
    // User probably wants to see relationships BETWEEN these people.
    // Our 'renderGraph' expects edges. 
    // We can filter currentGraph.edges where both source/target are in targetNodes list
    
    const targetNames = new Set(targetNodes.map(n => n.name))
    const relevantEdges = currentGraph.edges.filter(e => targetNames.has(e.source) && targetNames.has(e.target))
    
    renderGraph(targetNodes, relevantEdges)
    ElMessage.success(`已筛选展示 ${label} 类节点`)
}

const getDisplayName = (node) => {
    // Priority: name -> title -> description -> content
    if (node.name && node.name !== 'null') return node.name
    const p = node.properties || {}
    return p.title || p.description || p.content || p.value || '无标题节点'
}

// Filtered Nodes for Sidebar
const filteredNodes = computed(() => {
   if (!nodeFilter.value) return allNodes.value
   const k = nodeFilter.value.toLowerCase()
   return allNodes.value.filter(n => {
       const name = n.name || ''
       return name.toLowerCase().includes(k)
   })
})

const groupedNodes = computed(() => {
    const groups = {}
    const nodes = filteredNodes.value
    
    // Initialize specific order if desired - Updated to match Neo4j Desk
    const order = ['Person', 'Location', 'Event', 'Scene']
    order.forEach(k => groups[k] = [])
    groups['Other'] = []

    nodes.forEach(node => {
        let label = node.labels && node.labels.length > 0 ? node.labels[0] : 'Other'
        if (!groups[label]) groups[label] = [] // For unexpected labels
        groups[label].push(node)
    })

    // Clean up empty groups
    Object.keys(groups).forEach(k => {
        if (groups[k].length === 0) delete groups[k]
    })
    
    return groups
})

// ECharts
const chartDom = ref(null)
let myChart = null

const colorMap = {
  'Person': '#5470c6',
  'Location': '#91cc75',
  'Event': '#fac858',
  'Scene': '#9a60b4', // Added Scene color (Purple-ish or Beige from screenshot?)  Screenshot is brownish/beige. Let's use a distinct color.
  'Other': '#ee6666'
}
const getColor = (label) => colorMap[label] || '#73c0de'
const getEdgeNodeColor = (labels) => {
    if (!labels || labels.length === 0) return '#606266'
    return getColor(labels[0])
}

// Init Chart
const initChart = () => {
  if (myChart || !chartDom.value) return
  myChart = echarts.init(chartDom.value)
  myChart.on('click', (params) => {
    if (params.dataType === 'node') {
       selectedNode.value = params.data.rawData
       // Sync selection in list if possible
    }
  })
  window.addEventListener('resize', () => myChart.resize())
}

const renderGraph = (nodes, edges) => {
   if (!myChart) initChart()
   
   // Update current graph stats
   currentGraph.nodes = nodes
   currentGraph.edges = edges

   const echartsNodes = nodes.map(n => ({
      id: String(n.id), 
      name: n.name, 
      value: n.labels ? n.labels.join(', ') : '',
      symbolSize: n.is_center ? 45 : 30,
      itemStyle: {
         color: getColor(n.labels ? n.labels[0] : 'Other'),
         borderColor: (selectedNode.value && selectedNode.value.id === String(n.id)) ? '#fff' : 'transparent',
         borderWidth: 2
      },
      label: {
         show: n.is_center || nodes.length < 50, // Show labels if graph is small or for center
         position: 'bottom',
         formatter: '{b}' 
      },
      rawData: n
  }))

  const echartsLinks = edges.map(e => ({
      source: e.source, 
      target: e.target,
      value: e.relation_type,
      label: {
         show: nodes.length < 50,
         formatter: '{c}',
         fontSize: 10
      },
      lineStyle: {
        curveness: 0.2,
        opacity: 0.7
      }
  }))
  
  // Deduplicate nodes for ECharts
   const uniqueNodesMap = new Map()
   echartsNodes.forEach(n => uniqueNodesMap.set(n.name, n))
   const uniqueNodes = Array.from(uniqueNodesMap.values())

  const option = {
    tooltip: {},
    legend: { show: false },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: uniqueNodes,
        links: echartsLinks,
        roam: true,
        draggable: true,
        force: {
           repulsion: 300,
           edgeLength: [50, 200],
           gravity: 0.1
        },
        label: { show: true, position: 'right' },
        lineStyle: { color: 'source', curveness: 0.3 }
      }
    ]
  };
  myChart.setOption(option)
}

// Actions

// 1. Load Whole Graph (Initial)
const loadWholeGraph = async () => {
   loading.value = true
   try {
      // Limit 500 for performance
      const res = await fetch(`${API_BASE}/graph/whole?limit=500`) 
      const data = await res.json()
      if (data.status === 'success') {
          const g = data.data
          // Sort nodes for list: Person first
          const nodes = g.nodes || []
          allNodes.value = nodes.sort((a,b) => {
              const la = a.labels?.[0] || 'Z'
              const lb = b.labels?.[0] || 'Z'
              return la.localeCompare(lb)
          })
          
          renderGraph(nodes, g.edges || [])
      }
   } catch(e) { ElMessage.error('加载全图失败') }
   finally { loading.value = false }
}

// 2. Click Node in List -> Get Neighbors (Filter)
const handleNodeClick = async (node) => {
   selectedNode.value = node
   // When clicking from list, we replace the view to focus on this node
   await expandNode(node, false)
}

const expandNode = async (node, merge = false) => {
   loading.value = true
   try {
     // Increased limit to 200 to show more neighbors
     const res = await fetch(`${API_BASE}/graph/neighbors?name=${node.name}&limit=200`)
     const data = await res.json()
     if (data.status === 'success') {
         const g = data.data
         
         if (merge) {
             // Merge with current graph
             const existingNodesMap = new Map()
             currentGraph.nodes.forEach(n => existingNodesMap.set(String(n.id), n))
             
             // Track existing edges to avoid duplicates
             const existingEdgeKeys = new Set(currentGraph.edges.map(e => `${e.source}-${e.relation_type}-${e.target}`))
             const newEdges = [...currentGraph.edges]
             
             // Add New Nodes
             g.nodes.forEach(n => existingNodesMap.set(String(n.id), n))
             
             // Add New Edges
             let addedCount = 0
             g.edges.forEach(e => {
                 const key = `${e.source}-${e.relation_type}-${e.target}`
                 if (!existingEdgeKeys.has(key)) {
                     newEdges.push(e)
                     existingEdgeKeys.add(key)
                     addedCount++
                 }
             })
             
             if (addedCount > 0) {
                 ElMessage.success(`扩展了 ${addedCount} 条新关系`)
             } else {
                 ElMessage.info('未发现更多新关系')
             }
             
             renderGraph(Array.from(existingNodesMap.values()), newEdges)
         } else {
             // Replace mode
             renderGraph(g.nodes, g.edges)
         }
     }
   } finally { loading.value = false }
}

// 3. Path
const handleSearchPath = async () => {
   if (!pathSource.value || !pathTarget.value) return
   loading.value = true
   try {
     const res = await fetch(`${API_BASE}/graph/path?source=${pathSource.value}&target=${pathTarget.value}`)
     const data = await res.json()
     if (data.status === 'success') {
         renderGraph(data.data.nodes, data.data.edges)
     } else { ElMessage.warning('无路径') }
   } finally { loading.value = false }
}

// 4. Subgraph
const handleSearchSubgraph = async () => {
    if (!subgraphCenter.value) return
    loading.value = true
    try {
        const res = await fetch(`${API_BASE}/graph/subgraph`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ center: subgraphCenter.value, depth: subgraphDepth.value })
        })
        const data = await res.json()
        if (data.status === 'success') {
            renderGraph(data.data.nodes, data.data.edges)
        }
    } finally { loading.value = false }
}

const expandedRelationGroups = reactive({})
const loadedRelations = reactive({}) // type -> edge[]
const relationShowAllState = reactive({})
const relationFilter = ref('')

const filteredRelationStats = computed(() => {
    if (!relationFilter.value) return statsData.relations_by_type
    const result = {}
    if (statsData.relations_by_type) {
        for (const type in statsData.relations_by_type) {
            if (type.toLowerCase().includes(relationFilter.value.toLowerCase())) {
                result[type] = statsData.relations_by_type[type]
            }
        }
    }
    return result
})

const toggleRelationGroup = async (type) => {
    expandedRelationGroups[type] = !expandedRelationGroups[type]
    if (expandedRelationGroups[type] && !loadedRelations[type]) {
        // Load data on first expand
        await loadRelationsForList(type)
    }
}

const loadRelationsForList = async (type) => {
    try {
        // Fetch more edges for list view (e.g. 100)
        const res = await fetch(`${API_BASE}/edge/by-type/${type}?limit=100`)
        const data = await res.json()
        if (data.status === 'success') {
             loadedRelations[type] = data.data.edges || []
        } else {
             loadedRelations[type] = []
        }
    } catch(e) {
        ElMessage.error('加载关系列表失败')
        loadedRelations[type] = []
    }
}

const toggleRelationShowAll = (type) => {
    relationShowAllState[type] = !relationShowAllState[type]
}

const handleEdgeClick = (edge) => {
    // Render graph with just this edge and its nodes
    const nodes = [
        { id: edge.source, name: edge.source, labels: edge.source_labels || ['Unknown'], is_center: true },
        { id: edge.target, name: edge.target, labels: edge.target_labels || ['Unknown'], is_center: false }
    ]
    renderGraph(nodes, [edge])
    ElMessage.success(`Focused on: ${edge.source} - ${edge.target}`)
}

const filterGraphByRelation = async (type) => {
    loading.value = true
    try {
        const res = await fetch(`${API_BASE}/edge/by-type/${type}?limit=100`)
        const data = await res.json()
        if (data.status === 'success') {
             const edges = data.data.edges || []
             // Extract unique node names to construct graph nodes
             const nodeMap = new Map() 
             edges.forEach(e => {
                 if (!nodeMap.has(e.source)) nodeMap.set(e.source, e.source_labels || ['Unknown'])
                 if (!nodeMap.has(e.target)) nodeMap.set(e.target, e.target_labels || ['Unknown'])
             })
             
             const nodes = Array.from(nodeMap.entries()).map(([name, labels]) => ({
                 id: name,
                 name: name,
                 labels: labels,
                 is_center: false
             }))
             
             renderGraph(nodes, edges)
             ElMessage.success(`Showing relations: ${type}`)
        }
    } catch(e) {
        ElMessage.error('Failed to load relations')
    } finally {
        loading.value = false
    }
}

const loadAllRelationsGraph = async () => {
   loading.value = true
   try {
      // Limit 2000 to cover general cases
      const res = await fetch(`${API_BASE}/edge/all?limit=2000`) 
      const data = await res.json()
      if (data.status === 'success') {
          const edges = data.data.edges || []
          
          const nodeMap = new Map()
          edges.forEach(e => {
             if (!nodeMap.has(e.source)) nodeMap.set(e.source, e.source_labels || ['Unknown'])
             if (!nodeMap.has(e.target)) nodeMap.set(e.target, e.target_labels || ['Unknown'])
          })
          
          const nodes = Array.from(nodeMap.entries()).map(([name, labels]) => ({
             id: name,
             name: name,
             labels: labels,
             is_center: false
          }))
          
          renderGraph(nodes, edges)
          ElMessage.success('已显示所有关系')
      }
   } catch(e) { ElMessage.error('加载所有关系失败') }
   finally { loading.value = false }
}

const fetchStats = async () => {
    try {
        const res = await fetch(`${API_BASE}/graph/stats`)
        const data = await res.json()
        if (data.status === 'success') {
            statsData.nodes_by_label = data.data.nodes_by_label
            statsData.relations_by_type = data.data.relations_by_type
        }
    } catch(e){
        console.error("Failed to fetch stats", e)
    }
}

onMounted(() => {
   fetchStats()
   loadWholeGraph()
   nextTick(() => initChart())
})
</script>

<style scoped>
.graph-search-container {
  padding: 20px;
  height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}
.header { margin-bottom: 20px; flex-shrink: 0; }
.content-wrapper { flex: 1; overflow: hidden; }
.el-row, .el-col { height: 100%; }

/* Sidebar */
.control-panel {
  background: white;
  height: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
  padding: 15px;
  display: flex;
  flex-direction: column;
  position: relative;
}
.sidebar-tabs { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.list-controls { padding-bottom: 10px; border-bottom: 1px solid #eee; margin-bottom: 10px; }

.node-item {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}
.node-item:hover { background: #f5f7fa; }
.node-item.active { background: #e6f7ff; color: #409EFF; }
.grouped-item { padding: 8px 10px 8px 30px; border-bottom: 1px solid #f9f9f9; cursor: pointer; transition: all 0.2s; }

/* Grouping Box Style */
.node-group-box { margin-bottom: 15px; border: 1px solid #ebeef5; border-radius: 4px; overflow: hidden; }
.group-header-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 15px;
    background: #f5f7fa;
    cursor: pointer;
    transition: background 0.3s;
    user-select: none;
}
.group-header-card:hover { background: #e6effb; }
.header-left { display: flex; align-items: center; }
.header-right { display: flex; align-items: center; }
.group-title { font-weight: bold; color: #606266; margin-right: 10px; }
.arrow-icon { margin-right: 8px; font-size: 12px; transition: transform 0.3s; color: #909399; }
.arrow-icon.is-active { transform: rotate(90deg); }
.group-list-container { background: #fff; }

.group-footer {
    text-align: center;
    padding: 8px;
    font-size: 12px;
    color: #409EFF;
    cursor: pointer;
    border-top: 1px dashed #eee;
    background: #fdfdfd;
    transition: background 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
}
.group-footer:hover { background: #f0f7ff; }
.footer-icon { transition: transform 0.3s; }
.footer-icon.is-flipped { transform: rotate(180deg); }

.badget { width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; flex-shrink: 0; }
.node-name { 
    flex: 1; 
    font-size: 13px; 
    color: #333; 
    overflow: hidden; 
    text-overflow: ellipsis; 
    white-space: nowrap; 
    display: block; 
}
.node-tag { margin-left: 5px; font-size: 10px; transform: scale(0.9); }
.empty-text { text-align: center; color: #999; margin-top: 20px; }

/* Node Info Panel */
.node-info-panel {
  position: absolute;
  /* 抬高底部，防止被屏幕边缘遮挡 */
  bottom: 20px;
  left: 10px;
  right: 10px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px; /* 增加圆角使其因悬浮而更美观 */
  padding: 15px;
  box-shadow: 0 -4px 16px rgba(0,0,0,0.1);
  z-index: 2000;
  display: flex;
  flex-direction: column;
    max-height: 35%;
}
.info-header { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 16px; }
.props-scroller { overflow-y: auto; flex: 1; margin-bottom: 10px; }
.prop-row { font-size: 12px; margin-bottom: 4px; display: flex; }
.key { color: #666; width: 70px; font-weight: bold; }
.val { color: #333; flex: 1; word-break: break-all; }
.actions { text-align: center; }

/* Advanced Tab */
.section-title { font-weight: bold; margin: 10px 0; color: #555; font-size: 14px; }
.search-group { margin-bottom: 15px; }
.mb-2 { margin-bottom: 8px; }
.flex-row { display: flex; gap: 8px; }
.w-100 { width: 100%; }

/* Graph Area */
.graph-canvas-wrapper {
  background: white;
  height: 100%;
  border-radius: 8px;
  position: relative;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
  overflow: hidden;
}
.chart-container { width: 100%; height: 100%; }
.legend-overlay {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(255,255,255,0.9);
  padding: 8px 12px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  pointer-events: none;
}
.legend-item { display: flex; align-items: center; font-size: 12px; margin-bottom: 4px; }
.status-overlay {
   position: absolute;
   bottom: 15px;
   left: 15px;
   background: rgba(255,255,255,0.8);
   padding: 5px 10px;
   font-size: 12px;
   color: #666;
   border-radius: 4px;
}
.dot { width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }

.gufeng-title { font-size: 24px; color: #5a4a42; }

.stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.2s;
}
.stat-row:hover {
  background-color: #f5f7fa;
}
</style>
