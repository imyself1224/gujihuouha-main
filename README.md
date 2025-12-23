# 古籍人物画像分析系统 (GUJIHUOUHA-POF)

这是一个针对古代汉语（文言文）设计的人物画像与特征分析系统。该系统基于 **GuWen-Bert** 预训练模型，创新性地融合了**共现矩阵分析**和**BERT语义相似度**两种方法，通过双重特征融合来深度挖掘古籍中人物的形象特征与社会关系。

## 项目简介

**GUJIHUOUHA-POF（古籍人物画像分析平台）** 旨在解决古文语境下的人物画像构建与特征分析问题。该系统通过智能文本分析引擎，为研究人员和开发者提供强大的古籍人物形象挖掘能力。

## 项目结构

```
gujihuouha-pof-flask/
├── main.py                        # Flask 应用启动脚本
├── app.py                         # Flask Web 服务接口
├── test.py                        # 非Flask测试脚本
├── test_api.py                    # API 接口测试脚本
├── cooccurrence.py                # [核心] 共现矩阵分析模块
├── similarity.py                  # [核心] BERT语义相似度分析模块
├── data_loader.py                 # 数据加载模块
├── utils.py                       # 工具函数
├── HanGaozuBenji_simple.txt       # 示例数据文件（《汉高祖本纪》）
└── README.md                      # 项目说明文档
```

> **注意**: GuWen-Bert 模型文件夹不包含在此仓库中，需要手动下载

## 环境与配置

### 系统要求

- **Python**: >= 3.8
- **PyTorch**: >= 1.9.0（推荐使用 CUDA 版本以获得最佳性能）
- **GPU**: NVIDIA GPU with CUDA support（推荐）/ CPU（可选，但速度较慢）

### 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

```

### 模型文件准备

#### 1. GuWen-Bert 模型下载

**重要**: GuWen-Bert 预训练模型需要从 HuggingFace 单独下载。

**下载方式**:

```bash
# 使用 git-lfs 克隆模型仓库
git clone https://huggingface.co/ethanyt/guwenbert-base GuWen-Bert

# 或手动下载模型文件
```

**HuggingFace 模型链接**: https://huggingface.co/ethanyt/guwenbert-base/tree/main

**下载完成后**，将模型文件放在项目目录中，结构如下：

```
gujihuouha-pof-flask/
├── GuWen-Bert/
│   ├── config.json              # 模型配置文件
│   ├── vocab.txt                # 词汇表
│   ├── flax_model.msgpack       # 模型权重 (Flax格式)
│   ├── pytorch_model.bin        # PyTorch模型权重
│   ├── gitattributes            # Git LFS 属性文件
│   └── README.md                # 模型说明
├── main.py                      # Flask 应用启动脚本
├── app.py                       # Flask Web 服务接口
├── test.py                      # 非Flask测试脚本
├── test_api.py                  # API 接口测试脚本
├── cooccurrence.py              # 共现矩阵分析模块
├── similarity.py                # BERT语义相似度分析模块
├── data_loader.py               # 数据加载模块
├── utils.py                     # 工具函数
├── HanGaozuBenji_simple.txt     # 示例数据文件
├── requirements.txt             # 项目依赖
├── README.md                    # 项目说明文档
└── __pycache__/                 # Python缓存目录
```

包含 **6个主要核心文件**:
1. `main.py` - Flask 应用启动脚本
2. `app.py` - Flask Web 服务接口
3. `cooccurrence.py` - 共现矩阵分析模块
4. `similarity.py` - BERT语义相似度分析模块
5. `data_loader.py` - 数据加载模块
6. `utils.py` - 工具函数

#### 2. 示例数据

项目已包含 `HanGaozuBenji_simple.txt` 作为示例数据。如需使用其他古籍文本，请按以下格式准备：

```
{刘邦|PER}为{沛|LOC}人。{项羽|PER}与{刘邦|PER}争天下。{刘邦|PER}为{沛令|OFI}。
```

## 快速开始

### 方式一：命令行测试

使用 `test.py` 脚本直接测试，无需启动服务：

```bash
python test.py
```

### 方式二：启动 Web API 服务

使用 `main.py` 启动 Flask 服务：

```bash
python main.py
```

输出：
```
============================================================
Character Portrait Analysis Model Service Started
Listening on port: 5002
============================================================
```

### 方式三：API 调用示例

#### 健康检查

```bash
curl http://localhost:5002/health
```

响应：
```json
{
  "status": "ok",
  "message": "Service is running normally"
}
```

#### 分析文本内容

```bash
curl -X POST http://localhost:5002/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "{刘邦|PER}为{沛|LOC}人。{项羽|PER}与{刘邦|PER}争天下。",
    "person_aliases": {
      "高祖,季,刘季": "刘邦"
    }
  }'
```


#### Python 调用示例

```python
import requests

response = requests.post(
    "http://localhost:5002/analyze",
    json={
        "text": "{刘邦|PER}为{沛令|OFI}。{项羽|PER}与{刘邦|PER}争天下。",
        "person_aliases": {"高祖,季,刘季": "刘邦"}
    }
)
result = response.json()
print(result)
```

#### Spring Boot 调用示例

```java
RestTemplate restTemplate = new RestTemplate();
Map<String, Object> payload = new HashMap<>();
payload.put("text", "{刘邦|PER}为{沛令|OFI}。{项羽|PER}与{刘邦|PER}争天下。");
payload.put("person_aliases", Collections.singletonMap("高祖,季,刘季", "刘邦"));
String response = restTemplate.postForObject("http://localhost:5002/analyze", payload, String.class);
System.out.println(response);
```

### 方式四：运行 API 测试脚本

```bash
python test_api.py
```

**参数说明**
- `text` (必需): 待分析的文本内容，使用 `{实体|类型}` 格式标注
  - 实体类型: PER (人物), LOC (地点), TIME (时间), OFI (官职)
- `person_aliases` (可选): 人物别名映射
  - 格式: `{"别名1,别名2,别名3": "规范名"}`

**响应**
```json
{
  "success": true,
  "message": "分析成功",
  "data": {
    "cooccurrence": {
      "matrix_types": ["人物-官职", "人物-地点", "人物-时间"],
      "top_results": [
        {
          "entity1": "刘邦",
          "entity2": "沛令",
          "count": 52
        }
      ]
    },
    "similarity": {
      "matrix_types": ["人物-官职", "人物-地点", "人物-时间", "地点-官职"],
      "top_results": [
        {
          "entity1": "刘邦",
          "entity2": "汉王",
          "similarity": 0.9234
        }
      ]
    }
  }
}
```

### 4. 分析文件内容

**请求**
```
POST /analyze/file
Content-Type: application/json

{
  "file_path": "HanGaozuBenji_simple.txt",
  "person_aliases": {
    "高祖,季,刘季": "刘邦"
  }
}
```

**参数说明**
- `file_path` (必需): 待分析文件的路径
- `person_aliases` (可选): 人物别名映射

**响应** 格式同 `/analyze` 端点

### 启动服务

#### 方式一：直接运行主程序（推荐）
```bash
python main.py
```

#### 方式二：使用 Flask CLI
```bash
flask --app app run --host 0.0.0.0 --port 5002
```

#### 方式三：使用 Gunicorn（生产环境推荐）
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5002 app:app
```

## 核心模块详解

### 1. 共现矩阵分析 (`cooccurrence.py`)

**原理**: 统计实体对在固定窗口内共同出现的次数，反映实体间的关联强度。

**主要方法**:
- `extract_entities()` - 从标注文本中提取实体
- `add_person_alias()` - 添加人物别名映射
- `analyze_all_cooccurrences()` - 计算所有类型的共现矩阵
- `get_top_cooccurrences()` - 获取前 N 个共现对

### 2. BERT 语义相似度分析 (`similarity.py`)

**原理**: 使用 GuWen-Bert 预训练模型提取实体的语义向量，计算向量间的余弦相似度。

**主要方法**:
- `extract_entities()` - 从标注文本中提取实体
- `get_entity_embedding()` - 计算实体的嵌入向量
- `build_entity_embeddings()` - 批量构建所有实体的嵌入
- `analyze_all_similarities()` - 计算所有类型的相似度矩阵
- `get_top_similarities()` - 获取前 N 个相似对

**支持的嵌入策略**:
- `entity_only` - 仅使用实体文本（最快）
- `context` - 使用完整上下文
- `masked_context` - 用掩码标记实体的上下文
- `weighted` - 加权融合实体与上下文特征

### 3. 数据加载 (`data_loader.py`)

```python
from data_loader import load_text_file
text = load_text_file("HanGaozuBenji_simple.txt")
```

### 4. Flask 应用 (`app.py`)

**关键端点**:
- `POST /analyze` - 分析文本内容
- `POST /analyze/file` - 分析文件内容
- `GET /health` - 健康检查
- `GET /` - 首页信息

## 性能指标

| 操作 | 耗时 (秒) | 备注 |
|-----|---------|------|
| 模型首次加载 | ~30 | 第一次运行会加载 GuWen-Bert |
| 共现矩阵分析 (19K字符) | ~1 | 高效，主要是正则匹配 |
| 实体嵌入计算 (209个实体) | ~15 | 包含 BERT forward pass |
| 相似度矩阵计算 (20996) | ~2 | 使用 GPU 加速 |
| **总计** | **~48** | **全流程** |

*注: 性能数据基于 RTX 3090 GPU + PyTorch + CUDA 11.8*

## 高级配置

### 自定义嵌入策略

在 `app.py` 中修改:
```python
sim_matrices = analyzer.analyze_all_similarities(
    context_window=60,
    embedding_strategy='entity_only'  # 修改此处
)
```

### 修改窗口大小

```python
coanalyzer = CooccurrenceAnalyzer(window_size=20)
analyzer.analyze_all_similarities(context_window=60)
```

### 自定义人物别名

```python
payload = {
    "text": "...",
    "person_aliases": {
        "别名1,别名2,别名3": "规范名",
        "高祖,季": "刘邦"
    }
}
```

## 故障排除

### 1. 模型加载失败

**错误信息**:
```
模型加载失败: [Errno 2] No such file or directory: './GuWen-Bert'
```

**解决方案**:
- 检查 `GuWen-Bert/` 文件夹是否存在
- 确保文件夹中包含 `config.json` 和 `pytorch_model.bin` 等必要文件
- 从 HuggingFace 重新下载模型: https://huggingface.co/ethanyt/guwenbert-base

### 2. 端口已被占用

```bash
# 查找占用 5002 端口的进程
netstat -ano | findstr :5002

# 杀死进程 (Windows)
taskkill /PID <PID> /F

# 或修改端口
python -c "from app import app; app.run(port=5003)"
```

### 3. 出现乱码 (Windows)

```powershell
chcp 65001
python main.py
```

### 4. CUDA 内存不足

```python
analyzer = ImprovedBertSimilarityAnalyzer(
    model_name='./GuWen-Bert',
    device='cpu'  # 强制使用 CPU
)
```

### 5. API 响应超时

```python
response = requests.post(url, json=payload, timeout=300)  # 5分钟超时
```

## 文本标注格式

### 标准格式

```
{实体文本|实体类型}
```

### 示例

```
{刘邦|PER}为{沛|LOC}人，{秦二世二年|TIME}率众起义。后被拜为{沛令|OFI}。

{曹操|PER}与{刘备|PER}在{赤壁|LOC}大战，时值{建安十三年|TIME}。
曹操为{丞相|OFI}，{刘备|PER}为{左将军|OFI}。
```

### 实体类型说明

| 类型 | 说明 | 例子 |
|-----|------|------|
| `PER` | 人物名字 | 刘邦、项羽、曹操 |
| `LOC` | 地理位置 | 沛、咸阳、赤壁 |
| `TIME` | 时间信息 | 汉元年、秦二世三年 |
| `OFI` | 官职身份 | 沛令、汉王、丞相 |

## 项目重构历史

### v2.0.0 (2025年12月14日)

**新增功能**:
- 清理调试打印 - 移除了多余的中文调试打印语句
- 完整的中文文档 - 提供全面的中文项目文档
- 简化的输出信息 - 优化了控制台输出，更适合生产环境
- 优化的 API 响应 - 更好的 JSON 响应结构

**改进**:
- 从核心模块中删除了所有调试打印语句
- 提高了代码的可读性
- 优化了终端输出以适应生产环境
- 统一了 API 响应的格式

### 项目结构整理

✅ 文件移动 - 已将所有模块文件移动到主目录
✅ 清理已删除 - 已删除旧目录结构
✅ 代码修复和验证 - 已更新所有导入语句
✅ 文档更新 - 已更新项目文档以反映新的项目结构

所有文件均无语法错误，项目可以正常运行。

## 贡献与反馈

如有问题或建议，欢迎提交 Issue 或 Pull Request。

## 许可证

本项目采用 MIT 许可证。

## 参考资源

- [GuWen-Bert HuggingFace](https://huggingface.co/ethanyt/guwenbert-base)
- [PyTorch 官方文档](https://pytorch.org/docs/)
- [Flask 官方文档](https://flask.palletsprojects.com/)
- [Transformers 库文档](https://huggingface.co/docs/transformers/)

---

**最后更新**: 2025 年 12 月 23 日
