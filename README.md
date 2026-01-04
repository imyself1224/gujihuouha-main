# 古籍事件关系识别 Flask API 服务

基于古文BERT的古籍事件关系识别系统。支持事件关系类型识别（因果、并列、顺承），通过Flask提供RESTful API接口。

## 📂 项目结构

```
.
├── app.py                      # Flask应用主文件 [核心]
├── config.py                   # 配置文件
├── models.py                   # 神经网络模型定义
├── data.py                     # 数据加载与预处理
├── inference.py                # 推理函数
├── utils.py                    # 工具函数
├── test_api.py                 # API测试脚本
├── GuWen-Bert/                 # [核心] 古文BERT预训练模型
├── model_best/                 # [核心] 训练好的模型权重
│   └── rbert_model.pth
├── filtered_deduplicated_data.json  # 训练数据
└── requirements.txt            # 依赖列表
```

## 🛠️ 环境配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备模型文件

确保以下文件存在：
- `GuWen-Bert/` 目录（包含 config.json, pytorch_model.bin 等）
- `model_best/rbert_model.pth` 训练好的模型权重

## 🚀 快速开始

### 方式一：启动 Web API 服务

# 古籍人物画像分析系统（简易使用说明）

## 1. 环境准备

- Python >= 3.8
- PyTorch >= 1.9.0（建议CUDA加速）

安装依赖：
```bash
pip install -r requirements.txt
```

## 2. GuWen-Bert模型文件

**本项目不包含GuWen-Bert模型文件夹，请从HuggingFace下载：**

https://huggingface.co/ethanyt/guwenbert-base

下载后需包含以下文件：
- config.json
- vocab.txt
- flax_model.msgpack
- pytorch_model.bin
- gitattributes
- README.md

下载后将整个GuWen-Bert文件夹放在项目根目录。

## 3. model_best文件

**model_best文件未上传，如需获取请邮件联系：1315721905@qq.com**

## 4. 快速使用

### 方式一：命令行测试
```bash
python test.py
```

### 方式二：启动Web API服务
```bash
python main.py
```
默认端口5002。

### 方式三：API调用示例

#### 健康检查
```bash
curl http://localhost:5002/health
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

#### Python调用示例
```python
import requests
response = requests.post(
        "http://localhost:5002/analyze",
        json={
                "text": "{刘邦|PER}为{沛令|OFI}。{项羽|PER}与{刘邦|PER}争天下。",
                "person_aliases": {"高祖,季,刘季": "刘邦"}
        }
)
print(response.json())
```

#### Spring Boot调用示例
```java
RestTemplate restTemplate = new RestTemplate();
Map<String, Object> payload = new HashMap<>();
payload.put("text", "{刘邦|PER}为{沛令|OFI}。{项羽|PER}与{刘邦|PER}争天下。");
payload.put("person_aliases", Collections.singletonMap("高祖,季,刘季", "刘邦"));
String response = restTemplate.postForObject("http://localhost:5002/analyze", payload, String.class);
System.out.println(response);
```

### 方式四：API测试脚本
```bash
python test_api.py
```

## 5. 文件分析接口

```bash
curl -X POST http://localhost:5002/analyze/file \
    -H "Content-Type: application/json" \
    -d '{
        "file_path": "HanGaozuBenji_simple.txt",
        "person_aliases": {
            "高祖,季,刘季": "刘邦"
        }
    }'
```

## 6. 文本标注格式

文本需使用 `{实体文本|实体类型}` 标注。

实体类型：
- PER：人物
- LOC：地点
- TIME：时间
- OFI：官职

示例：
```
{刘邦|PER}为{沛|LOC}人，{秦二世二年|TIME}率众起义。后被拜为{沛令|OFI}。
```

## 7. 常见问题

- GuWen-Bert模型未下载或文件缺失会导致启动失败，请确保模型文件齐全。
- model_best未上传，如需请邮件联系。

---
如有问题请提交Issue或邮件联系。
| 因果 | 一个事件是另一个事件的原因或结果 | "因为下雨，所以取消"（下雨→取消） |
| 并列 | 两个事件平行发生 | "既进攻，又防守"（进攻≈防守） |
| 顺承 | 两个事件按时间顺序发生 | "先吃饭，再睡觉"（吃饭→睡觉） |

## 📈 模型性能

测试集表现：
- **Accuracy**: 80%
- **Micro F1**: 0.8000
- **Precision**: 0.8000
- **Recall**: 0.8000

## 🔧 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| `✗ 无法连接到服务` | Flask 未启动 | 运行 `python app.py` 启动服务 |
| `模型加载失败` | 模型文件缺失 | 检查 `model_best/rbert_model.pth` 是否存在 |
| `预测结果异常` | 触发词不在文本中 | 确保 `head_trigger` 和 `tail_trigger` 都在文本中 |
| `GPU 内存不足` | 模型过大 | 减小 `config.py` 中的 `BATCH_SIZE` |
| `端口 5004 被占用` | 端口冲突 | 修改 `config.py` 中的 `FLASK_PORT` |

**常见错误排查：**

1. **关于 `head_trigger` 和 `tail_trigger`：**
   - 必须是文本中真实存在的字或词
   - 对古文敏感，需要正确的繁体字
   - 示例：`"令"` 而不是 `"令与"`

2. **关于 GPU/CUDA：**
   - 如果 GPU 不可用，会自动切换到 CPU（较慢）
   - 可在 `config.py` 设置 `USE_CUDA = False` 强制使用 CPU

3. **关于预测准确性：**
   - 使用的是古文文本，模型基于古籍训练
   - 不同的触发词组合会影响预测结果
   - 置信度反映了模型的预测信心度

## 📦 生产环境部署

使用 Gunicorn：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5004 app:app
```

使用 Docker：

```dockerfile
FROM python:3.8
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5004
CMD ["python", "app.py"]
```

## 📝 关键文件说明

| 文件 | 功能 | 状态 |
|------|------|------|
| `app.py` | Flask主应用，定义所有API路由 | ✓ 已验证 |
| `config.py` | 所有可配置的常量 | ✓ 完成 |
| `models.py` | 7种神经网络模型架构 | ✓ 完成 |
| `data.py` | 数据加载、分词、预处理 | ✓ 完成 |
| `inference.py` | 推理函数 | ✓ 完成 |
| `utils.py` | 模型加载、初始化工具 | ✓ 完成 |
| `test_api.py` | 快速API测试脚本 | ✓ 已验证 |
| `GuWen-Bert/` | 古文BERT预训练模型 | ✓ 已加载 |
| `model_best/rbert_model.pth` | 训练好的模型权重 | ✓ 已加载 |

## ✨ 主要特性

✅ **完全可用** - 所有API接口已验证  
✅ **GPU加速** - 支持CUDA加速，自动切换到CPU  
✅ **批量预测** - 支持一次处理多个样本  
✅ **多模型支持** - 可切换7种模型架构  
✅ **完整的错误处理** - 详细的错误提示  
✅ **简洁的API设计** - RESTful风格  
✅ **快速测试脚本** - 一键验证系统  
✅ **生产环境就绪** - 支持 Gunicorn 和 Docker  

---

**项目状态**: ✅ **完整可用**  
**最后更新**: 2026-01-04  
**测试验证**: ✓ 通过 (2026-01-04)
