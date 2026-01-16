# 古籍话题 Flask API - 图数据库查询服务

本项目是一个基于 Flask 框架的 Neo4j 图数据库查询服务，用于快速检索和分析古代文献中的人物、地点、事件及其相互关系。通过 RESTful API 提供灵活的查询能力，支持单点查询、关系查询、路径分析等功能。

本项目提供了完整的后端 API 服务 (`app.py`) 和配置文件，可供前端应用进行图数据查询。

## 📚 项目简介

  * **核心功能**: 图数据库查询、关系分析、路径追踪
  * **后端技术**: Flask + Neo4j Driver + CORS
  * **数据支持**: 
      * **人物节点**: 古籍中的各类人物（皇帝、官员、平民等）
      * **地点节点**: 古代地名、地理位置
      * **关系类型**: 亲属关系、官职、地理位置、事件参与等
  * **应用场景**: 古籍数字化、知识图谱展示、历史人物关系分析

## 📂 目录结构

项目目录结构如下所示：

```text
.
├── app.py                      # Flask 服务启动脚本（主要应用）
├── README.md                   # 项目文档
├── config.py                   # 配置文件
├── requirements.txt            # 项目依赖库
├── newmain.py                  # 数据导入脚本（导入关系数据到 Neo4j）
├── try.py                      # 旧版导入脚本
├── RE-Hangaozubenji.json       # 关系数据文件（JSON 格式）
├── 汉高祖本纪场景.json          # 场景/事件数据文件
├── EE-Hangaozubenji.txt        # 事件数据文件（文本格式）
├── re.csv                      # 关系数据文件（CSV 格式）
├── reconvert.py                # 数据格式转换脚本
└── text.txt                    # 原始文本数据
```

## 🛠️ 环境与数据库准备

### 1. 安装依赖

请确保 Python 版本 >= 3.7。

```bash
pip install -r requirements.txt
```

*主要依赖: `flask`, `flask-cors`, `neo4j`*

### 2. Neo4j 数据库配置

确保 Neo4j 数据库已安装并正在运行。

  * **数据库地址**: `neo4j://127.0.0.1:7687`
  * **用户名**: `neo4j`
  * **密码**: `12345678`

如需修改连接参数，编辑 `app.py` 文件中的以下部分：

```python
NEO4J_URI = "neo4j://127.0.0.1:7687"  # 数据库地址
NEO4J_USER = "neo4j"                  # 用户名
NEO4J_PASSWORD = "12345678"           # 密码
```

### 3. 数据导入

在启动服务之前，需要将关系数据导入到 Neo4j 数据库：

```bash
python newmain.py
```

该脚本会读取 `re.csv` 文件，创建节点和关系，导入到 Neo4j 数据库。

## 🚀 运行与使用

### 启动服务

```bash
python app.py
```

*服务默认监听地址 `0.0.0.0:5007`*。

控制台输出示例：
```
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5007
```

服务启动成功后，即可通过 HTTP 请求调用 API。

## 📡 API 接口文档

## 📡 API 接口文档

### 1. 健康检查
检查数据库连接状态

**请求:**
```
GET /api/health
```

**响应:**
```json
{
  "status": "success",
  "message": "Neo4j 连接正常"
}
```

---

### 2. 查询节点详情
获取特定节点的完整信息

**请求:**
```
GET /api/node/<节点名称>
```

例如：`GET /api/node/高祖`

**响应:**
```json
{
  "status": "success",
  "data": {
    "name": "高祖",
    "labels": ["Person"],
    "properties": {
      "属性1": "值1",
      "属性2": "值2"
    }
  }
}
```

---

### 3. 查询人物及其关系（查节点）
根据人物名称查询其信息及所有关联的边（关系）

**请求:**
```
GET /api/search/person?name=高祖
```

**请求方式二 (POST):**
```
POST /api/search/person
Content-Type: application/json

{
  "name": "高祖"
}
```

**响应:**
```json
{
  "status": "success",
  "data": {
    "node": {
      "name": "高祖",
      "labels": ["Person"],
      "properties": {}
    },
    "edges": [
      {
        "source": "高祖",
        "target": "吕后",
        "relation_type": "夫妻",
        "direction": "outgoing",
        "target_labels": ["Person"],
        "properties": {}
      },
      {
        "source": "太公",
        "target": "高祖",
        "relation_type": "父子",
        "direction": "incoming",
        "target_labels": ["Person"],
        "properties": {}
      }
    ],
    "edge_count": 2
  }
}
```

---

### 4. 查询两个节点之间的边（查关系）
获取两个节点之间的所有关系（边）信息

**请求:**
```
GET /api/edge/relations?source=高祖&target=吕后
```

**请求方式二 (POST):**
```
POST /api/edge/relations
Content-Type: application/json

{
  "source": "高祖",
  "target": "吕后"
}
```

**响应:**
```json
{
  "status": "success",
  "data": {
    "source": "高祖",
    "target": "吕后",
    "edges": [
      {
        "source": "高祖",
        "target": "吕后",
        "relation_type": "夫妻",
        "properties": {
          "年份": "2000 BC",
          "备注": "汉初皇后"
        }
      }
    ],
    "edge_count": 1
  }
}
```

---

### 5. 查询特定类型的所有边
查询数据库中所有特定类型的关系

**请求:**
```
GET /api/edge/by-type/夫妻?limit=50
```

**响应:**
```json
{
  "status": "success",
  "data": {
    "relation_type": "夫妻",
    "edges": [
      {
        "source": "高祖",
        "target": "吕后",
        "relation_type": "夫妻",
        "properties": {}
      }
    ],
    "total_count": 1
  }
}
```

---

### 6. 查询邻接节点（一度关系）
获取某个节点的直接邻接节点及连接关系

**请求:**
```
GET /api/graph/neighbors?name=高祖&limit=20
```

**请求方式二 (POST):**
```
POST /api/graph/neighbors
Content-Type: application/json

{
  "name": "高祖",
  "limit": 20
}
```

**响应:**
```json
{
  "status": "success",
  "data": {
    "nodes": [
      {
        "id": "高祖",
        "name": "高祖",
        "labels": ["Person"],
        "properties": {},
        "is_center": true
      },
      {
        "id": "吕后",
        "name": "吕后",
        "labels": ["Person"],
        "properties": {}
      }
    ],
    "edges": [
      {
        "source": "高祖",
        "target": "吕后",
        "relation_type": "夫妻",
        "properties": {}
      }
    ],
    "node_count": 2,
    "edge_count": 1
  }
}
```

---

### 7. 查询子图（查多度关系）
以指定节点为中心，查询多度关系的子图

**请求:**
```
GET /api/graph/subgraph?center=高祖&depth=2&limit=50
```

**请求方式二 (POST):**
```
POST /api/graph/subgraph
Content-Type: application/json

{
  "center": "高祖",
  "depth": 2,
  "limit": 50
}
```

**参数说明:**
- `center`: 中心节点名称（必需）
- `depth`: 查询深度，范围 1-5（默认 2）
  - depth=1: 查询直接邻接节点
  - depth=2: 查询邻接节点的邻接节点
  - depth=3: 三度关系
  - 以此类推...
- `limit`: 返回节点数量限制（默认 50）

**响应:**
```json
{
  "status": "success",
  "data": {
    "center": "高祖",
    "depth": 2,
    "nodes": [
      {
        "id": "高祖",
        "name": "高祖",
        "labels": ["Person"],
        "properties": {},
        "is_center": true
      },
      {
        "id": "吕后",
        "name": "吕后",
        "labels": ["Person"],
        "properties": {}
      },
      {
        "id": "孝惠帝",
        "name": "孝惠帝",
        "labels": ["Person"],
        "properties": {}
      }
    ],
    "edges": [
      {
        "source": "高祖",
        "target": "吕后",
        "relation_type": "夫妻",
        "properties": {}
      },
      {
        "source": "吕后",
        "target": "孝惠帝",
        "relation_type": "母子",
        "properties": {}
      }
    ],
    "node_count": 3,
    "edge_count": 2
  }
}
```

---

### 8. 查询两节点间的最短路径
找到两个节点之间的最短连接路径

**请求:**
```
GET /api/graph/path?source=高祖&target=孝惠帝&max_length=5
```

**请求方式二 (POST):**
```
POST /api/graph/path
Content-Type: application/json

{
  "source": "高祖",
  "target": "孝惠帝",
  "max_length": 5
}
```

**参数说明:**
- `source`: 源节点名称（必需）
- `target`: 目标节点名称（必需）
- `max_length`: 最大路径长度（默认 5）

**响应:**
```json
{
  "status": "success",
  "data": {
    "source": "高祖",
    "target": "孝惠帝",
    "path_length": 2,
    "nodes": [
      {
        "id": "高祖",
        "name": "高祖",
        "labels": ["Person"],
        "properties": {}
      },
      {
        "id": "吕后",
        "name": "吕后",
        "labels": ["Person"],
        "properties": {}
      },
      {
        "id": "孝惠帝",
        "name": "孝惠帝",
        "labels": ["Person"],
        "properties": {}
      }
    ],
    "edges": [
      {
        "source": "高祖",
        "target": "吕后",
        "relation_type": "夫妻",
        "properties": {}
      },
      {
        "source": "吕后",
        "target": "孝惠帝",
        "relation_type": "母子",
        "properties": {}
      }
    ],
    "node_count": 3,
    "edge_count": 2
  }
}
```

---

### 9. 查询地点信息
根据地点名称查询其信息及关联关系

**请求:**
```
GET /api/search/location?name=咸阳
```

**请求方式二 (POST):**
```
POST /api/search/location
Content-Type: application/json

{
  "name": "咸阳"
}
```

**响应:**
```json
{
  "status": "success",
  "data": {
    "name": "咸阳",
    "labels": ["Location"],
    "relations": [
      {
        "target": "高祖",
        "relation_type": "去往",
        "target_labels": ["Person"]
      }
    ]
  }
}
```

---

### 10. 全局搜索
按关键词搜索所有匹配的节点

**请求:**
```
GET /api/search/all?keyword=高
```

**请求方式二 (POST):**
```
POST /api/search/all
Content-Type: application/json

{
  "keyword": "高"
}
```

**响应:**
```json
{
  "status": "success",
  "data": [
    {
      "name": "高祖",
      "labels": ["Person"]
    }
  ],
  "total": 1
}
```

---

### 11. 获取图数据库统计信息
获取数据库中节点和关系的统计信息

**请求:**
```
GET /api/graph/stats
```

**响应:**
```json
{
  "status": "success",
  "data": {
    "nodes_by_label": {
      "Person": 25,
      "Location": 15,
      "Other": 10
    },
    "relations_by_type": {
      "父子": 5,
      "夫妻": 3,
      "去往": 8
    }
  }
}
```

---

## 💻 前端集成示例

### 使用 JavaScript 调用 API

```javascript
// 健康检查
async function checkHealth() {
  const response = await fetch('http://localhost:5007/api/health');
  const data = await response.json();
  console.log(data);
}

// 查询人物信息
async function searchPerson(name) {
  const response = await fetch(`http://localhost:5007/api/search/person?name=${name}`);
  const data = await response.json();
  console.log(data);
}

// 查询两个人物之间的关系
async function searchRelations(source, target) {
  const response = await fetch('http://localhost:5007/api/search/relations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      source: source,
      target: target
    })
  });
  const data = await response.json();
  console.log(data);
}

// 获取邻接节点（用于可视化）
async function getNeighbors(name) {
  const response = await fetch(`http://localhost:5007/api/graph/neighbors?name=${name}&limit=20`);
  const data = await response.json();
  console.log(data);
}

// 全局搜索
async function globalSearch(keyword) {
  const response = await fetch(`http://localhost:5007/api/search/all?keyword=${keyword}`);
  const data = await response.json();
  console.log(data);
}
```

### 使用 Vue.js 的完整示例

```vue
<template>
  <div class="search-container">
    <input v-model="searchName" placeholder="搜索人物或地点" />
    <button @click="search">搜索</button>
    
    <div v-if="searchResult" class="result">
      <h3>{{ searchResult.name }}</h3>
      <h4>关联关系：</h4>
      <ul>
        <li v-for="rel in searchResult.relations" :key="rel.target">
          <strong>{{ rel.target }}</strong> ({{ rel.relation_type }})
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchName: '',
      searchResult: null
    }
  },
  methods: {
    async search() {
      try {
        const response = await fetch(`http://localhost:5007/api/search/person?name=${this.searchName}`);
        const data = await response.json();
        if (data.status === 'success') {
          this.searchResult = data.data;
        } else {
          console.error('查询失败:', data.message);
        }
      } catch (error) {
        console.error('请求出错:', error);
      }
    }
  }
}
</script>
```

### 使用 Axios 的示例

```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5007/api';

// 查询人物
async function fetchPerson(name) {
  try {
    const response = await axios.get(`${API_BASE_URL}/search/person`, {
      params: { name }
    });
    return response.data;
  } catch (error) {
    console.error('查询失败:', error);
  }
}

// 查询关系
async function fetchRelations(source, target) {
  try {
    const response = await axios.post(`${API_BASE_URL}/search/relations`, {
      source,
      target
    });
    return response.data;
  } catch (error) {
    console.error('查询失败:', error);
  }
}

// 获取统计信息
async function fetchStats() {
  try {
    const response = await axios.get(`${API_BASE_URL}/graph/stats`);
    return response.data;
  } catch (error) {
    console.error('获取统计信息失败:', error);
  }
}
```

---

## ⚠️ 常见问题

1. **无法连接到 Neo4j 数据库**
   
   确保满足以下条件：
   - Neo4j 数据库已启动并运行
   - 数据库 URI 正确: `neo4j://127.0.0.1:7687`
   - 用户名和密码正确: `neo4j` / `12345678`
   - 防火墙允许 7687 端口访问

2. **查询返回空结果**
   
   可能的原因：
   - 数据未导入到数据库（请先运行 `python newmain.py`）
   - 查询的节点名称拼写错误或大小写不匹配
   - 节点标签与查询接口不符（如查询 Person 但节点为 Other）

3. **前端跨域请求失败**
   
   Flask 已配置 CORS 支持，应该允许来自任何域的请求。如仍有问题，检查：
   - Flask 应用是否正常启动
   - 前端请求 URL 是否正确（http://localhost:5007）

4. **性能问题**
   
   - 对于大型数据集，建议在 Neo4j 中为常用属性建立索引
   - 使用 `limit` 参数限制返回结果数量
   - 考虑添加查询缓存机制

5. **修改 API 响应格式**
   
   编辑 `app.py` 文件中的相应路由函数，返回不同的 JSON 结构。

---

## 📝 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置 Neo4j 连接**
   - 修改 `app.py` 中的数据库连接参数（如需）

3. **导入数据**
   ```bash
   python newmain.py
   ```

4. **启动服务**
   ```bash
   python app.py
   ```

5. **测试 API**
   ```bash
   curl http://localhost:5007/api/health
   ```

---

## 📖 更多信息

- **Neo4j 官方文档**: https://neo4j.com/docs/
- **Flask 官方文档**: https://flask.palletsprojects.com/
- **Python Neo4j Driver**: https://neo4j.com/docs/api/python-driver/current/
