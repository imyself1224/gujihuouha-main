# 古代事件时空聚类分析系统 - Flask API

一个基于Flask的RESTful服务，用于对古代历史事件进行时空聚类分析。用户上传地名数据和事件数据，系统自动执行空间-时间维度的聚类分析，将相关事件聚类在一起。

## 主要功能

- **事件聚类**：基于地理位置和时间信息，使用DBSCAN算法自动发现事件簇
- **噪声处理**：智能识别和处理孤立事件
- **参数自优化**：自动搜索最佳聚类参数
- **RESTful API**：简单的HTTP接口，易于集成

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务
```bash
python app.py
```

服务将在 `http://localhost:5005` 启动

## 使用指南

### 数据格式

#### 地名数据 (location.csv)
CSV格式，包含古代地名和现代坐标信息

```csv
ancient_name,modern_name,latitude,longitude
长安,西安,34.5,108.9
洛阳,洛阳,34.6,112.4
南京,南京,32.1,118.8
```

#### 事件数据 (events.json)
JSON数组格式，包含历史事件信息

```json
[
    {
        "id": "1",
        "year": 220,
        "location": "长安",
        "description": "某历史事件描述"
    },
    {
        "id": "2", 
        "year": 221,
        "location": "洛阳",
        "description": "另一个历史事件"
    }
]
```

## API 端点

### POST /api/cluster/file
执行聚类分析（推荐方式）

**请求（multipart/form-data）：**
```
Files:
- location_file: location.csv
- events_file: events.json
```

**响应示例：**
```json
{
    "status": "success",
    "message": "聚类分析完成",
    "data": {
        "clusters": [
            {
                "cluster_id": 0,
                "size": 3,
                "events": [
                    {
                        "id": "1",
                        "year": 220,
                        "location": "长安",
                        "description": "某历史事件描述",
                        "latitude": 34.5,
                        "longitude": 108.9,
                        "assigned_method": "original"
                    },
                    {
                        "id": "2",
                        "year": 221,
                        "location": "洛阳",
                        "description": "另一个历史事件",
                        "latitude": 34.6,
                        "longitude": 112.4,
                        "assigned_method": "original"
                    }
                ]
            },
            {
                "cluster_id": 1,
                "size": 2,
                "events": [
                    {
                        "id": "3",
                        "year": 222,
                        "location": "南京",
                        "description": "第三个事件",
                        "latitude": 32.1,
                        "longitude": 118.8,
                        "assigned_method": "original"
                    }
                ]
            },
            {
                "cluster_id": -1,
                "size": 1,
                "events": [
                    {
                        "id": "4",
                        "year": 250,
                        "location": "西安",
                        "description": "孤立的噪声点事件",
                        "latitude": 34.5,
                        "longitude": 108.9,
                        "assigned_method": "noise"
                    }
                ]
            }
        ],
        "summary": {
            "total_events": 6,
            "num_clusters": 2,
            "num_noise": 1,
            "best_params": {
                "eps": 0.5,
                "min_samples": 2
            }
        }
    }
}
```

**返回字段说明：**
- `clusters`: 聚类结果数组
  - `cluster_id`: 聚类ID（-1 表示噪声点）
  - `size`: 该聚类包含的事件数
  - `events`: 聚类中的事件列表
    - `id`: 事件ID
    - `year`: 事件年份
    - `location`: 事件地点（古代名称）
    - `description`: 事件描述
    - `latitude`: 地理位置纬度
    - `longitude`: 地理位置经度
    - `assigned_method`: 事件分配方式（original=原始，noise=噪声处理）
- `summary`: 聚类分析摘要
  - `total_events`: 总事件数
  - `num_clusters`: 聚类数量
  - `num_noise`: 噪声点数量
  - `best_params`: 使用的DBSCAN最佳参数

### GET /api/info
获取API文档和信息

### GET /health
健康检查

## 结果文件说明

每次执行聚类分析后，系统会自动将结果保存到 `results/` 文件夹，包含以下文件：

1. **clustering_results_[时间戳].csv** - 完整的聚类结果
   - 包含所有事件的详细信息和聚类分配
   - 字段：id, year, location, description, latitude, longitude, cluster, assigned_method 等

2. **hierarchical_results_[时间戳].csv** - 层次聚类分析结果
   - 对每个主聚类进行进一步的子聚类分解
   - 字段：main_cluster, sub_cluster, event_count, year_range, locations, events

3. **clustering_summary_[时间戳].json** - 分析摘要和参数
   - 包含聚类分析的摘要信息
   - 包含使用的DBSCAN参数等元数据

**示例文件列表：**
```
results/
├── clustering_results_20260105_171801.csv
├── hierarchical_results_20260105_171801.csv
└── clustering_summary_20260105_171801.json
```

## Java 调用示例

### 方式一：使用 Apache HttpClient (推荐)

```java
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.mime.MultipartEntityBuilder;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.entity.ContentType;
import java.io.File;

public class ClusteringClient {
    
    public static void performClustering(String locationFile, String eventsFile) 
            throws Exception {
        
        try (CloseableHttpClient httpClient = HttpClients.createDefault()) {
            HttpPost uploadFile = new HttpPost("http://localhost:5005/api/cluster/file");
            
            MultipartEntityBuilder builder = MultipartEntityBuilder.create();
            builder.addBinaryBody("location_file", 
                                 new File(locationFile),
                                 ContentType.APPLICATION_OCTET_STREAM, 
                                 "location.csv");
            builder.addBinaryBody("events_file", 
                                 new File(eventsFile),
                                 ContentType.APPLICATION_OCTET_STREAM, 
                                 "events.json");
            
            uploadFile.setEntity(builder.build());
            
            var response = httpClient.execute(uploadFile);
            System.out.println("Response Code: " + response.getStatusLine().getStatusCode());
            System.out.println("Response: " + 
                             new String(response.getEntity().getContent().readAllBytes()));
        }
    }
    
    public static void main(String[] args) throws Exception {
        performClustering("location.csv", "events.json");
    }
}
```

### Maven 依赖

```xml
<dependency>
    <groupId>org.apache.httpcomponents</groupId>
    <artifactId>httpclient</artifactId>
    <version>4.5.14</version>
</dependency>
```

## 聚类结果格式

### JSON API 响应格式

聚类分析完成后，API返回以下结构的JSON数据：

```json
{
    "status": "success",
    "message": "聚类分析完成",
    "data": {
        "clusters": [
            {
                "cluster_id": 0,
                "size": 5,
                "events": [
                    {
                        "id": "1",
                        "year": 220,
                        "location": "长安",
                        "description": "某历史事件",
                        "latitude": 34.5,
                        "longitude": 108.9,
                        "assigned_method": "DBSCAN"
                    },
                    ...
                ]
            },
            {
                "cluster_id": 1,
                "size": 3,
                "events": [...]
            }
        ],
        "summary": {
            "total_events": 50,
            "num_clusters": 5,
            "num_noise": 2,
            "best_params": {
                "eps": 0.5,
                "min_samples": 2
            }
        }
    }
}
```

### CSV 导出格式

通过 `/api/cluster/download` 端点获取的CSV文件包含以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| id | string | 事件唯一标识符 |
| year | integer | 事件发生年份 |
| location | string | 古代地名 |
| description | string | 事件描述 |
| latitude | float | 地理位置纬度 |
| longitude | float | 地理位置经度 |
| cluster | integer | 聚类ID（-1表示噪声点） |
| assigned_method | string | 分配方法（DBSCAN/重新分配） |

**CSV示例：**
```csv
id,year,location,description,latitude,longitude,cluster,assigned_method
1,220,长安,某历史事件,34.5,108.9,0,DBSCAN
2,221,洛阳,另一个历史事件,34.6,112.4,0,DBSCAN
3,222,南京,相关历史事件,32.1,118.8,1,DBSCAN
4,450,长安,孤立事件,34.5,108.9,-1,未分配
5,451,长安,重新分配事件,34.5,108.9,0,重新分配
```

**前端展示建议：**
- 使用 `cluster` 列进行分组展示
- `cluster_id = -1` 表示噪声点，可单独显示
- `assigned_method` 显示事件的分配方式
- 使用 `latitude/longitude` 在地图上绘制聚类

## 工作原理

1. **特征提取**：将事件的地理位置（纬度、经度）和时间（年份）转换为特征向量
2. **标准化**：对特征进行标准化处理
3. **聚类分析**：使用DBSCAN算法，自动搜索最优参数
4. **噪声处理**：将孤立事件重新分配到最近的聚类
5. **结果输出**：返回聚类分组和统计信息

## 项目结构

```
gujihuouha-scenery-flask/
├── app.py                      # Flask应用主文件
├── clustering_service.py       # 聚类服务核心逻辑
├── data_loader.py              # 数据加载模块
├── location_matcher.py         # 地名匹配模块
├── clustering.py               # 聚类算法模块
├── noise_handling.py           # 噪声处理模块
├── hierarchical_clustering.py  # 层次聚类分析
├── requirements.txt            # 项目依赖
├── README.md                   # 本文档
└── datasets/                   # 数据文件夹
    ├── location.csv
    └── events.json
```

## 常见问题

**Q: 聚类需要多长时间？**  
A: 取决于数据量。通常数百个事件在秒级完成。

**Q: 如何处理编码问题？**  
A: 确保所有数据文件使用UTF-8编码。

---

版本：2.0 | 基于Flask和scikit-learn
