# 汉高祖本纪事件抽取接口

基于 Flask 的古文事件抽取 REST API 服务。该服务接收来自前端的古文文本查询，在数据集中检索匹配的文本并返回对应的事件标注训练数据。

## 功能概述

- **事件抽取查询** - 输入古文文本，获取完整的事件标注（事件类型、触发词、论元角色）
- **多数据集支持** - 支持查询多个古文数据集（汉高祖本纪、古文EE等）
- **前后端分离** - 完全符合 REST API 设计，支持任何前端框架
- **CORS 支持** - 已配置跨域资源共享，支持 Spring Boot + Vue 等跨域调用
- **数据缓存** - 首次加载数据后自动缓存，提高查询效率
- **完整错误处理** - 统一的错误响应格式，便于前端处理

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务

**Windows（推荐）:**
```bash
run.bat
```

**Linux/macOS:**
```bash
bash run.sh
```

**直接运行:**
```bash
python app.py
```

服务默认运行在 **`http://localhost:5003`**

## API 端点说明

### 1. 查询古文文本（核心接口）

**POST** `/api/query-by-text`

根据输入的古文文本在数据集中查询，返回对应的事件标注数据。

| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | string | 要查询的古文文本 |
| `dataset` | string | 数据集名称，可选（默认：Hangaozubenji） |

**请求示例:**
```bash
curl -X POST http://localhost:5003/api/query-by-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。",
    "dataset": "Hangaozubenji"
  }'
```

**成功响应 (200):**
```json
{
    "status": "success",
    "found": true,
    "text": "其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。",
    "event_list": [
        {
            "event_type": "地理/雷雨風",
            "trigger": "雷电晦冥",
            "arguments": [
                {"role": "地点", "argument": "大泽"},
                {"role": "时间", "argument": "是时"}
            ]
        }
    ],
    "message": "找到匹配的训练数据"
}
```

**未找到响应 (404):**
```json
{
    "status": "error",
    "message": "数据集中未找到该文本"
}
```

### 2. 获取训练数据（分页）

**POST** `/api/training-data`

分页获取数据集中的训练数据。

**参数:**
- `dataset` (string) - 数据集名称
- `limit` (integer) - 每页数据数（可选，默认：10）
- `offset` (integer) - 分页偏移量（可选，默认：0）

**请求示例:**
```json
{
    "dataset": "Hangaozubenji",
    "limit": 5,
    "offset": 0
}
```

### 3. 数据集信息

**GET** `/api/datasets`

获取所有可用的数据集列表。

**响应示例:**
```json
{
    "status": "success",
    "datasets": [
        "Hangaozubenji",
        "GuwenEE_new",
        "EE-Hangaozubenji",
        ...
    ],
    "total": 10
}
```

### 4. 统计信息

**GET** `/api/training-stats/{dataset_name}`

获取指定数据集的统计信息。

**响应示例:**
```json
{
    "status": "success",
    "dataset": "Hangaozubenji",
    "total_items": 196,
    "total_events": 196,
    "event_types": {
        "地理/雷雨風": 45,
        "人物/死亡": 38,
        ...
    }
}
```

### 5. 健康检查

**GET** `/api/health`

检查服务状态。

**响应:**
```json
{
    "status": "ok",
    "message": "服务正常运行"
}
```

## 核心接口

### 按文本查询训练数据

**POST** `/api/query-by-text`

前端传来古文文本，返回对应的事件标注训练数据。

**请求示例:**
```json
{
    "text": "其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。",
    "dataset": "Hangaozubenji"
}
```

**成功响应:**
```json
{
    "status": "success",
    "found": true,
    "text": "...",
    "event_list": [
        {
            "event_type": "地理/雷雨風",
            "trigger": "雷电晦冥",
            "arguments": [...]
        }
    ],
    "message": "找到匹配的训练数据"
}
```

**未找到响应 (404):**
```json
{
    "status": "error",
    "message": "数据集中未找到该文本"
}
```

## 其他接口

- **GET** `/api/health` - 健康检查
- **GET** `/api/datasets` - 获取所有可用数据集
- **POST** `/api/training-data` - 获取分页训练数据
- **GET** `/api/training-stats/{dataset_name}` - 获取统计信息

详细文档见 [QUICKSTART.md](QUICKSTART.md)

## 项目结构

```
gujihuouha-exe-flask/
├── app.py                    # 主应用程序（268行）
│                             # - Flask 应用初始化
│                             # - DatasetManager 类（数据加载、查询、缓存）
│                             # - 5 个 API 端点的实现
│                             # - CORS 跨域配置
├── config.py                 # 配置管理模块
│                             # - 开发环境/生产环境配置
│                             # - 数据集路径配置
├── test_api.py              # API 测试工具
│                             # - 测试所有 5 个端点
│                             # - 验证返回数据的完整性
├── requirements.txt         # Python 依赖清单
│                             # Flask==2.3.0
│                             # Flask-CORS==4.0.0
│                             # Werkzeug==2.3.0
├── run.bat                  # Windows 启动脚本
├── run.sh                   # Linux/macOS 启动脚本
├── README.md                # 项目说明（本文件）
├── QUICKSTART.md            # 详细使用指南
├── USAGE.md                 # API 用法示例和数据结构说明
└── datasets/                # 数据集目录（10 个数据集）
    ├── Hangaozubenji.json          # 汉高祖本纪（196 条）
    ├── GuwenEE_new.json            # 古文事件抽取
    ├── EE-Hangaozubenji.json       # 事件抽取标注版本
    ├── event_sentences_by_type.json
    ├── duee_dev.json
    ├── duee_dev_1.json
    ├── duee_train.json
    ├── duee_test1.json
    ├── duee.json
    └── Hangaozubenji_index.json
```

## 应用特性

- ✅ **模块化设计** - `DatasetManager` 类独立负责数据管理，职责清晰
- ✅ **CORS 跨域支持** - 配置完整，支持 Spring Boot + Vue 等前后端分离架构
- ✅ **数据缓存机制** - 首次加载后自动缓存，大幅提升查询效率
- ✅ **完整的错误处理** - 统一的错误响应格式，便于前端处理异常
- ✅ **内置测试工具** - `test_api.py` 脚本包含所有接口测试
- ✅ **详细的文档** - README、QUICKSTART、USAGE 三份文档覆盖各个层面
- ✅ **生产级配置** - 支持开发/生产环境配置切换

## 代码调用示例

### JavaScript/Fetch（前端示例）

```javascript
// 查询古文文本的训练数据
const text = "其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。";

fetch('http://localhost:5003/api/query-by-text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text: text,
        dataset: 'Hangaozubenji'
    })
})
    .then(res => res.json())
    .then(data => {
        if (data.found) {
            console.log('事件标注:', data.event_list);
            // 遍历事件
            data.event_list.forEach(event => {
                console.log(`事件类型: ${event.event_type}`);
                console.log(`触发词: ${event.trigger}`);
                console.log(`论元:`, event.arguments);
            });
        } else {
            console.log('未找到该文本');
        }
    })
    .catch(err => console.error('错误:', err));
```

### Python（后端示例）

```python
import requests

# 查询古文文本
text = "其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。"

response = requests.post('http://localhost:5003/api/query-by-text', json={
    'text': text,
    'dataset': 'Hangaozubenji'
})

data = response.json()

if data['found']:
    print(f"找到 {len(data['event_list'])} 个事件")
    for event in data['event_list']:
        print(f"  事件类型: {event['event_type']}")
        print(f"  触发词: {event['trigger']}")
        for arg in event['arguments']:
            print(f"    {arg['role']}: {arg['argument']}")
else:
    print("未找到该文本")
```

### cURL（命令行示例）

```bash
curl -X POST http://localhost:5003/api/query-by-text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。",
    "dataset": "Hangaozubenji"
  }' \
  | python -m json.tool
```

## 测试和验证

### 运行测试脚本

验证所有 API 端点都正常工作：

```bash
python test_api.py
```

**测试覆盖范围：**
- ✅ 健康检查 (`/api/health`)
- ✅ 数据集列表 (`/api/datasets`)
- ✅ 文本查询 (`/api/query-by-text`) - 包含完整的事件标注数据
- ✅ 分页数据 (`/api/training-data`)
- ✅ 统计信息 (`/api/training-stats/{dataset_name}`)

**预期输出：**
```
测试健康检查... ✓
测试数据集列表... ✓
测试文本查询... ✓
  - 文本: 其先刘媪尝息大泽之陂，梦与神遇...
  - 事件数: 1
  - 事件类型: 地理/雷雨風
  - 触发词: 雷电晦冥
测试分页数据... ✓
测试统计信息... ✓

所有测试通过！
```

## 常见问题

### Q1: 如何自定义查询的数据集？
**A:** 在请求时指定 `dataset` 参数。例如：
```json
{
    "text": "文本内容",
    "dataset": "GuwenEE_new"
}
```
可用的数据集列表可通过 `GET /api/datasets` 获取。

### Q2: 查询时说"未找到"，是什么原因？
**A:** 最常见的原因是查询文本与数据集中的文本不完全相同。接口使用精确匹配，需要：
- 查询文本必须与数据集中的文本**完全一致**
- 包括标点符号、空格等
- 建议使用分页接口先浏览数据集中的实际文本

### Q3: 首次访问很慢，之后就很快，为什么？
**A:** 应用实现了数据缓存机制。首次访问某个数据集时需要从磁盘加载 JSON 文件，之后该数据集会被缓存在内存中，查询速度会大幅提升。

### Q4: 可以添加新的数据集吗？
**A:** 可以。在 `datasets/` 目录下放入新的 JSON 文件，确保格式与现有数据集一致（包含 `text` 和 `event_list` 字段），然后重启服务即可。

### Q5: 支持跨域调用吗？
**A:** 支持。已配置 CORS，允许来自任何域名的请求。支持 Spring Boot、Vue、React 等任何前端框架。

## 部署说明

### 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py

# 3. 测试
python test_api.py

# 4. 访问
# 浏览器打开: http://localhost:5003/api/health
```

### 生产环境部署

推荐使用 Gunicorn 等 WSGI 服务器：

```bash
# 安装 gunicorn
pip install gunicorn

# 启动应用
gunicorn -w 4 -b 0.0.0.0:5003 app:app
```

## 数据说明

### 汉高祖本纪数据集

- **数据量:** 196 条文本记录
- **事件数:** 196 个事件标注
- **主要事件类型:** 人物死亡、地理天象、战争等
- **每条数据结构:**
  ```json
  {
    "text": "古文文本内容",
    "event_list": [
      {
        "event_type": "事件分类",
        "trigger": "触发词",
        "arguments": [
          {
            "role": "论元角色名",
            "argument": "论元值"
          }
        ]
      }
    ]
  }
  ```

## 关键技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Flask | 2.3.0 | Web 框架 |
| Flask-CORS | 4.0.0 | 跨域资源共享 |
| Python | 3.x | 编程语言 |
| JSON | - | 数据格式 |

## 联系和帮助

- **详细用法:** 见 [USAGE.md](USAGE.md)
- **快速开始指南:** 见 [QUICKSTART.md](QUICKSTART.md)
- **问题排查:** 检查 `test_api.py` 的测试输出

## 许可证

本项目用于学术和教育用途。
