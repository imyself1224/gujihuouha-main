import json
import os
import re
import numpy as np
import pandas as pd
import networkx as nx
from flask import Flask, jsonify, send_from_directory, request
from collections import Counter
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


app = Flask(__name__)

# ================= 解决跨域问题 =================
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ================= 静态文件服务 =================
@app.route('/files/<path:filename>')
def serve_files(filename):
    """提供 output 目录下的静态文件访问"""
    return send_from_directory('output', filename)

# ================= 配置路径 =================
DATA_PATH_RELATION = "output/causal_relations.json"
DATA_PATH_EVENT = "output/historical_relations/EE-Hangaozubenji_updated.json"


# ================= 辅助函数 =================
def to_native(obj):
    """将Numpy类型转换为Python原生类型，防止JSON序列化报错"""
    if isinstance(obj, np.generic): return obj.item()
    if isinstance(obj, np.ndarray): return obj.tolist()
    return obj


# ================= 模型 1: 因果关系分析 =================
class CausalAnalyzer:
    def __init__(self, causal_data):
        self.df = pd.DataFrame([{
            'event1': i.get('事件1', i.get('event1')),
            'event2': i.get('事件2', i.get('event2')),
            'relation': i.get('关系类型', i.get('relation_type')),
            'connector': i.get('连接词', i.get('connector'))
        } for i in causal_data])
        self.graph = nx.DiGraph()
        for _, r in self.df.iterrows():
            self.graph.add_edge(r['event1'], r['event2'], relation=r['relation'], connector=r['connector'])

    def get_data(self):
        # 1. 网络图
        pos = nx.spring_layout(self.graph, k=0.8, seed=42)
        # 使用 nx.degree 函数获取并转换为 dict，避免 Pylance 将 self.graph.degree 属性误判为 int
        degree_dict = dict(nx.degree(self.graph))
        
        nodes = []
        for n in self.graph.nodes():
            degree_val = degree_dict.get(n, 0)
            if not isinstance(degree_val, int):
                degree_val = 0
            
            nodes.append({
                "name": n, 
                "x": pos[n][0] * 1000, 
                "y": pos[n][1] * 1000,
                "value": degree_val, 
                "symbolSize": min(15 + degree_val * 3, 60)
            })
            
        links = [{"source": u, "target": v, "label": {"show": True, "formatter": d['connector']}}
                 for u, v, d in self.graph.edges(data=True)]

        # 2. 因果链 (DFS)
        chains = []

        def dfs(u, path):
            if len(path) > 6: return
            path.append(u)
            if len(path) > 1: chains.append(path.copy())
            for v in self.graph.successors(u): dfs(v, path)
            path.pop()

        start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0][:15]
        for n in start_nodes: dfs(n, [])

        chains.sort(key=len, reverse=True)
        top_chains = []
        for i, c in enumerate(chains[:5]):
            top_chains.append([[step, i, evt] for step, evt in enumerate(c)])  # [x, y, name]

        # 3. 统计
        stats = {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "top_causes": sorted(dict(self.graph.out_degree()).items(), key=lambda x: x[1], reverse=True)[:5],
            "top_results": sorted(dict(self.graph.in_degree()).items(), key=lambda x: x[1], reverse=True)[:5]
        }
        return {"graph": {"nodes": nodes, "links": links}, "chains": top_chains, "report": stats}


# ================= 模型 2: 事件类型分析 =================
class TypeAnalyzer:
    def __init__(self, data):
        self.df = pd.DataFrame([{
            'event_type': e['event_type'],
            'args_len': len(e['arguments']),
            'trigger_len': len(str(e['trigger']))
        } for item in data for e in item['event_list']])

    def get_data(self):
        # 特征工程 & 聚类
        counts = self.df['event_type'].value_counts()
        types = list(counts.index)
        features = []
        for t in types:
            sub = self.df[self.df['event_type'] == t]
            features.append([len(sub), sub['args_len'].mean(), sub['trigger_len'].mean()])

        # PCA & KMeans
        # Explicitly convert to numpy array to fix Pylance argument type error
        features_arr = np.array(features)
        X = StandardScaler().fit_transform(features_arr)
        coords = PCA(n_components=2).fit_transform(X) if len(X) > 1 else np.zeros((len(X), 2))
        
        # 聚类健壮性检查
        n_clusters = min(5, len(X))
        if len(X) >= n_clusters and len(X) > 1:
            clusters = KMeans(n_clusters=n_clusters, random_state=42).fit_predict(X)
        else:
            clusters = np.zeros(len(X), dtype=int)

        scatter = [{"name": t, "value": [float(coords[i][0]), float(coords[i][1]), int(clusters[i])],
                    "category": int(clusters[i])} for i, t in enumerate(types)]

        # 计算轮廓系数健壮性
        n_labels = len(set(clusters))
        silhouette = 0
        if n_labels > 1 and len(X) > n_labels:
            try:
                silhouette = float(silhouette_score(X, clusters))
            except Exception as e:
                silhouette = 0

        stats = {
            "total_types": len(types),
            "silhouette": silhouette
        }
        
        # 4. 文件链接
        base_url = request.host_url.rstrip('/')
        files = {
            "image": f"{base_url}/files/image/event_clusters_output.png",
            "csv": f"{base_url}/files/csv/event_category_clusters.csv"
        }
        
        return {"scatter": scatter, "stats": stats, "files": files}


# ================= 模型 3: 地点空间分析 =================
class LocationAnalyzer:
    def __init__(self, data):
        self.locs = []
        for item in data:
            for e in item['event_list']:
                for arg in e['arguments']:
                    if arg['role'] in ['地点', '目的地', '出发地']:
                        self.locs.append({'loc': arg['argument'], 'role': arg['role'], 'type': e['event_type']})
        self.df = pd.DataFrame(self.locs)

    def get_data(self):
        if self.df.empty: return {}
        # 1. 频率排行 (Bar)
        top = self.df['loc'].value_counts().head(15)
        bar = {"categories": top.index.tolist(), "values": [int(x) for x in top.values]}

        # 2. 角色分布 (Pie)
        role_counts = self.df['role'].value_counts()
        pie = [{"name": k, "value": int(v)} for k, v in role_counts.items()]

        # 3. 聚类 (Scatter) - 简单特征：频率 + 角色多样性
        unique_locs = self.df['loc'].unique()
        features = []
        for l in unique_locs:
            sub = self.df[self.df['loc'] == l]
            features.append([len(sub), len(sub['role'].unique()), len(sub['type'].unique())])

        features_arr = np.array(features)
        X = StandardScaler().fit_transform(features_arr)
        coords = PCA(n_components=2).fit_transform(X) if len(X) > 1 else np.zeros((len(X), 2))
        clusters = KMeans(n_clusters=min(5, len(X)), random_state=42).fit_predict(X)

        scatter = [{"name": l, "value": [float(coords[i][0]), float(coords[i][1]), int(clusters[i])],
                    "category": int(clusters[i])} for i, l in enumerate(unique_locs)]

        # 4. 文件链接
        base_url = request.host_url.rstrip('/')
        files = {
            "images": [
                f"{base_url}/files/image/location_clusters_output.png",
                f"{base_url}/files/image/location_frequency.png",
                f"{base_url}/files/image/role_distribution.png"
            ],
            "csv": f"{base_url}/files/csv/location_clusters.csv"
        }

        return {"bar": bar, "pie": pie, "scatter": scatter, "files": files}


# ================= 模型 4: 时间演化分析 =================
class TimeAnalyzer:
    def __init__(self, data):
        self.events = []
        # 简化的时间解析逻辑 (复用你提供的正则思路)
        self.dynasty_map = {'秦': (-221, -207), '楚汉': (-206, -202), '西汉': (-202, 8)}

        for item in data:
            for e in item['event_list']:
                time_arg = next((a['argument'] for a in e['arguments'] if a['role'] == '时间'), None)
                if time_arg:
                    year = self._parse_year(time_arg)
                    dynasty = '未知'
                    for d, (s, e_year) in self.dynasty_map.items():
                        if s <= year <= e_year: dynasty = d; break

                    self.events.append({
                        'text': time_arg, 'year': year, 'type': e['event_type'], 'dynasty': dynasty
                    })

    def _parse_year(self, text):
        # 简单解析：提取汉字数字转年份，或者默认值
        cn_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5}
        # 模拟：如果有"二年" -> -205 (假设高祖二年)
        if '二年' in text: return -205
        if '元年' in text: return -206
        if '五年' in text: return -202
        return -210 + len(text)  # fallback mock

    def get_data(self):
        # 1. 时间线散点 (Timeline)
        types = list(set(e['type'] for e in self.events))
        type_map = {t: i for i, t in enumerate(types)}

        timeline = []
        for e in self.events:
            # value: [year, type_index, text, type_name]
            timeline.append([e['year'], type_map[e['type']], e['text'], e['type']])

        # 2. 窗口统计 (Bar)
        counts = Counter(e['dynasty'] for e in self.events)
        windows = [{"name": k, "value": v} for k, v in counts.items()]

        # 3. 文件链接
        base_url = request.host_url.rstrip('/')
        files = {
            "images": [
                f"{base_url}/files/image/time_clusters.png",
                f"{base_url}/files/image/historical_timeline.png",
                f"{base_url}/files/image/time_windows_dynasty.png",
                f"{base_url}/files/image/time_windows_seasonal.png",
                f"{base_url}/files/image/time_length_distribution.png"
            ],
            "csv": f"{base_url}/files/csv/enhanced_time_analysis_results.csv"
        }

        return {"timeline": timeline, "windows": windows, "types": types, "files": files}


# ================= Flask 接口定义 =================

@app.route('/analysis/causal/portrait', methods=['GET', 'POST'])
def causal_api():
    try:
        with open(DATA_PATH_RELATION, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"code": 200, "data": CausalAnalyzer(data).get_data()})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/analysis/event/type', methods=['GET', 'POST'])
def type_api():
    try:
        if not os.path.exists(DATA_PATH_EVENT):
            return jsonify({"code": 404, "msg": "数据文件不存在"})
            
        with open(DATA_PATH_EVENT, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = TypeAnalyzer(data).get_data()
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/analysis/event/location', methods=['GET', 'POST'])
def location_api():
    try:
        if not os.path.exists(DATA_PATH_EVENT):
            return jsonify({"code": 404, "msg": "数据文件不存在"})

        with open(DATA_PATH_EVENT, 'r', encoding='utf-8') as f:
            data = json.load(f)

        result = LocationAnalyzer(data).get_data()
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/analysis/event/time', methods=['GET', 'POST'])
def time_api():
    try:
        with open(DATA_PATH_EVENT, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"code": 200, "data": TimeAnalyzer(data).get_data()})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


if __name__ == '__main__':
    # 确保有 output 目录
    if not os.path.exists("output"): os.makedirs("output")
    app.run(port=5006, debug=True)