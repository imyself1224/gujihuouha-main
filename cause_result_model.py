import os
# 设置环境变量以抑制警告
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"

import json
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib.font_manager as fm
from matplotlib import rcParams

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class CausalRelationAnalyzer:
    def __init__(self, causal_data, event_data=None):
        """
        因果关系分析器

        Args:
            causal_data: 因果关系数据
            event_data: 事件数据（可选）
        """
        self.causal_data = causal_data
        self.event_data = event_data
        self.causal_graph = None
        self.relation_features = None
        self.cluster_results = None

    def _preprocess_causal_data(self):
        """预处理因果关系数据"""
        df = pd.DataFrame(self.causal_data)

        # 提取关键信息
        processed_data = []
        for item in self.causal_data:
            processed_data.append({
                'id': item['id'],
                'time': item['时间'],
                'event1': item['事件1'],
                'event2': item['事件2'],
                'relation_type': item['关系类型'],
                'connector': item['连接词'],
                'full_text': item['完整文本'],
                'source': item['来源']
            })

        return pd.DataFrame(processed_data)

    def build_causal_network(self):
        """构建因果关系网络"""
        self.df = self._preprocess_causal_data()
        self.causal_graph = nx.DiGraph()

        # 添加节点和边
        for _, row in self.df.iterrows():
            # 事件1作为源节点
            self.causal_graph.add_node(row['event1'], type='event')
            # 事件2作为目标节点
            self.causal_graph.add_node(row['event2'], type='event')
            # 添加因果关系边
            self.causal_graph.add_edge(
                row['event1'],
                row['event2'],
                relation_type=row['relation_type'],
                connector=row['connector'],
                time=row['time'],
                source=row['source']
            )

        return self.causal_graph

    def extract_relation_features(self):
        """提取关系特征"""
        relation_features = {}

        for _, row in self.df.iterrows():
            relation_id = f"{row['event1']}->{row['event2']}"

            # 1. 连接词类型特征（编码为数值）
            connector_mapping = {'故': 0, '是以': 1, '于是': 2, '因': 3, '遂': 4}
            connector_type = connector_mapping.get(row['connector'], 5)

            # 2. 事件文本特征
            event1_length = len(row['event1'])
            event2_length = len(row['event2'])
            text_similarity = self._calculate_text_similarity(row['event1'], row['event2'])

            # 3. 时间特征
            time_complexity = self._parse_time_complexity(row['time'])

            # 4. 事件复杂度特征
            event1_complexity = len(row['event1'].split())
            event2_complexity = len(row['event2'].split())

            relation_features[relation_id] = {
                'connector_type': connector_type,
                'event1_length': event1_length,
                'event2_length': event2_length,
                'text_similarity': text_similarity,
                'time_complexity': time_complexity,
                'event1_complexity': event1_complexity,
                'event2_complexity': event2_complexity,
                'relation_type': row['relation_type'],
                'original_connector': row['connector']
            }

        self.relation_features = relation_features
        return relation_features

    def _calculate_text_similarity(self, text1, text2):
        """计算文本相似度"""
        # 简单的文本相似度计算
        words1 = set(text1)
        words2 = set(text2)
        if len(words1.union(words2)) == 0:
            return 0
        return len(words1.intersection(words2)) / len(words1.union(words2))

    def _parse_time_complexity(self, time_str):
        """解析时间复杂性"""
        if not time_str or pd.isna(time_str):
            return 0

        # 简单的时间复杂性度量
        time_indicators = ['春', '夏', '秋', '冬', '年', '月', '日']
        complexity = sum(1 for indicator in time_indicators if indicator in time_str)
        return complexity

    def analyze_causal_patterns(self):
        """分析因果关系模式"""
        if self.causal_graph is None:
            self.build_causal_network()

        if self.causal_graph is None:
            return {}

        analysis_results = {}

        # 1. 节点度分析
        in_degrees = dict(self.causal_graph.in_degree())
        out_degrees = dict(self.causal_graph.out_degree())

        # 2. 关键事件识别（高入度或高出度）
        key_events = {
            'high_in_degree': sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10],
            'high_out_degree': sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        }

        # 3. 连接词分析
        connector_counts = Counter(self.df['connector'])

        # 4. 因果关系链分析
        causal_chains = self._find_causal_chains()

        analysis_results.update({
            'node_count': self.causal_graph.number_of_nodes(),
            'edge_count': self.causal_graph.number_of_edges(),
            'key_events': key_events,
            'connector_distribution': connector_counts,
            'causal_chains': causal_chains,
            'network_density': nx.density(self.causal_graph),
            'is_connected': nx.is_weakly_connected(self.causal_graph)
        })

        return analysis_results

    def _find_causal_chains(self, max_chain_length=5):
        """发现因果关系链"""
        if self.causal_graph is None:
            return []

        chains = []

        # 找到起始节点（入度为0的节点）
        start_nodes = [node for node in self.causal_graph.nodes()
                       if self.causal_graph.in_degree(node) == 0]

        for start_node in start_nodes[:10]:  # 限制数量避免组合爆炸
            self._dfs_find_chains(start_node, [], chains, max_chain_length)

        return chains

    def _dfs_find_chains(self, current_node, current_chain, all_chains, max_length):
        """深度优先搜索寻找因果链"""
        if len(current_chain) >= max_length:
            return

        current_chain.append(current_node)

        if len(current_chain) > 1:  # 至少两个事件才能形成链
            all_chains.append(current_chain.copy())

        if self.causal_graph is None:
            return

        # 继续搜索后续事件
        for neighbor in self.causal_graph.successors(current_node):
            self._dfs_find_chains(neighbor, current_chain, all_chains, max_length)

        current_chain.pop()

    def perform_causal_clustering(self, n_clusters=3, method='kmeans'):
        """执行因果关系聚类

        Args:
            n_clusters: 聚类数量
            method: 聚类方法 ('kmeans', 'hierarchical', 'dbscan')
        """
        if self.relation_features is None:
            self.extract_relation_features()
        
        if self.relation_features is None:
            return {}

        # 准备特征矩阵
        features = []
        relation_ids = []
        original_data = []

        for rel_id, features_dict in self.relation_features.items():
            feature_vector = [
                features_dict['connector_type'],
                features_dict['event1_length'],
                features_dict['event2_length'],
                features_dict['text_similarity'],
                features_dict['time_complexity'],
                features_dict['event1_complexity'],
                features_dict['event2_complexity']
            ]
            features.append(feature_vector)
            relation_ids.append(rel_id)
            original_data.append(features_dict)

        features = np.array(features)

        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # 选择聚类方法
        if method == 'kmeans':
            clusterer = KMeans(n_clusters=n_clusters, random_state=42)
        elif method == 'hierarchical':
            clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        elif method == 'dbscan':
            clusterer = DBSCAN(eps=0.8, min_samples=2)
        else:
            clusterer = KMeans(n_clusters=n_clusters, random_state=42)

        # 执行聚类
        clusters = clusterer.fit_predict(features_scaled)

        # 计算轮廓系数（对于DBSCAN需要特殊处理）
        if method == 'dbscan':
            unique_clusters = set(clusters)
            if len(unique_clusters) > 1 and -1 not in unique_clusters:
                silhouette_avg = silhouette_score(features_scaled, clusters)
            else:
                silhouette_avg = -1  # 无法计算
        else:
            silhouette_avg = silhouette_score(features_scaled, clusters)

        # 保存结果
        self.cluster_results = {
            'relation_ids': relation_ids,
            'clusters': clusters,
            'features': features_scaled,
            'original_data': original_data,
            'silhouette_score': silhouette_avg,
            'method': method,
            'n_clusters': len(set(clusters)) - (1 if -1 in clusters else 0)
        }

        return self.cluster_results

    def analyze_cluster_characteristics(self):
        """分析每个聚类的特征"""
        if self.cluster_results is None:
            return None

        results = []
        unique_clusters = np.unique(self.cluster_results['clusters'])

        for cluster_id in unique_clusters:
            if cluster_id == -1:  # 噪声点
                continue

            cluster_indices = np.where(self.cluster_results['clusters'] == cluster_id)[0]
            cluster_relations = [self.cluster_results['relation_ids'][i] for i in cluster_indices]

            # 计算聚类中心特征
            cluster_features = self.cluster_results['features'][cluster_indices]
            centroid = np.mean(cluster_features, axis=0)

            # 分析连接词分布
            connectors = []
            for idx in cluster_indices:
                connectors.append(self.cluster_results['original_data'][idx]['original_connector'])
            connector_dist = Counter(connectors)

            results.append({
                'cluster_id': cluster_id,
                'num_relations': len(cluster_relations),
                'relations_sample': cluster_relations[:3],  # 样本关系
                'avg_connector_type': centroid[0],
                'avg_event1_length': centroid[1],
                'avg_event2_length': centroid[2],
                'avg_text_similarity': centroid[3],
                'avg_time_complexity': centroid[4],
                'connector_distribution': dict(connector_dist.most_common(3))
            })

        return pd.DataFrame(results)

    def visualize_clusters(self, figsize=(12, 8), output_file='output/image/causal_clusters.png'):
        """可视化聚类结果"""
        if self.cluster_results is None:
            return

        # PCA降维可视化
        pca = PCA(n_components=2)
        features_2d = pca.fit_transform(self.cluster_results['features'])

        plt.figure(figsize=figsize)

        # 创建散点图
        scatter = plt.scatter(features_2d[:, 0], features_2d[:, 1],
                              c=self.cluster_results['clusters'],
                              cmap='viridis', s=100, alpha=0.7)

        # 添加关系标签（选择性显示）
        for i, relation_id in enumerate(self.cluster_results['relation_ids']):
            if i % 5 == 0:  # 每5个显示一个标签，避免过于拥挤
                plt.annotate(relation_id, (features_2d[i, 0], features_2d[i, 1]),
                             xytext=(5, 5), textcoords='offset points',
                             fontsize=6, alpha=0.6)

        plt.colorbar(scatter, label='聚类编号')
        plt.title(
            f'因果关系聚类分析 - {self.cluster_results["method"]}\n轮廓系数: {self.cluster_results["silhouette_score"]:.3f}')
        plt.xlabel('PCA主成分1')
        plt.ylabel('PCA主成分2')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)

    def visualize_causal_network(self, figsize=(15, 12), output_file='output/image/causal_network.png'):
        """可视化因果关系网络"""
        if self.causal_graph is None:
            self.build_causal_network()

        if self.causal_graph is None:
            return

        plt.figure(figsize=figsize)

        # 使用spring布局
        pos = nx.spring_layout(self.causal_graph, k=1, iterations=50)

        # 绘制节点
        node_sizes = [200 + 50 * self.causal_graph.out_degree(node)
                      for node in self.causal_graph.nodes()]

        nx.draw_networkx_nodes(self.causal_graph, pos,
                               node_size=node_sizes,
                               node_color='lightblue',
                               alpha=0.7)

        # 绘制边
        nx.draw_networkx_edges(self.causal_graph, pos,
                               edge_color='gray',
                               arrows=True,
                               arrowsize=20,
                               alpha=0.6)

        # 绘制标签
        nx.draw_networkx_labels(self.causal_graph, pos,
                                font_size=8,
                                font_family='SimHei')

        plt.title('历史事件因果关系网络', fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)

    def visualize_causal_chains(self, chains, figsize=(12, 8), output_file='output/image/causal_chains.png'):
        """可视化因果关系链"""
        if not chains:
            return

        plt.figure(figsize=figsize)

        # 选择前几个链进行可视化
        display_chains = chains[:5]

        for i, chain in enumerate(display_chains):
            chain_length = len(chain)
            y_pos = [i] * chain_length
            x_pos = list(range(chain_length))

            plt.plot(x_pos, y_pos, 'o-', linewidth=2, markersize=8,
                     label=f'链 {i + 1} (长度: {chain_length})')

            # 添加事件标签
            for j, event in enumerate(chain):
                plt.annotate(event, (x_pos[j], y_pos[j]),
                             xytext=(5, 5), textcoords='offset points',
                             fontsize=8, alpha=0.8)

        plt.xlabel('因果顺序')
        plt.ylabel('因果链')
        plt.title('因果关系链可视化')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)

    def compare_clustering_methods(self, n_clusters=3):
        """比较不同聚类方法的性能"""
        methods = ['kmeans', 'hierarchical', 'dbscan']
        results = []

        for method in methods:
            try:
                cluster_result = self.perform_causal_clustering(
                    n_clusters=n_clusters, method=method
                )

                results.append({
                    'method': method,
                    'silhouette_score': cluster_result['silhouette_score'],
                    'n_clusters_found': cluster_result['n_clusters'],
                    'n_relations': len(cluster_result['relation_ids'])
                })

            except Exception as e:
                pass

        return pd.DataFrame(results)

    def generate_causal_report(self):
        """生成因果关系分析报告"""
        if self.causal_graph is None:
            self.build_causal_network()

        patterns = self.analyze_causal_patterns()

        return patterns


# 主程序
def main():
    try:
        # 读取因果关系数据
        with open("output/causal_relations.json", "r", encoding="utf-8") as f:
            causal_data = json.load(f)

        # 读取事件数据（可选）
        event_data = None
        try:
            with open("EE-Hangaozubenji_updated.json", "r", encoding="utf-8") as f:
                event_data = json.load(f)
        except FileNotFoundError:
            pass

        # 创建分析器
        analyzer = CausalRelationAnalyzer(causal_data, event_data)

        # 生成分析报告
        report = analyzer.generate_causal_report()

        # 构建和可视化网络
        analyzer.build_causal_network()
        analyzer.visualize_causal_network()

        # 分析因果关系模式
        patterns = analyzer.analyze_causal_patterns()

        # 可视化因果关系链
        if patterns['causal_chains']:
            analyzer.visualize_causal_chains(patterns['causal_chains'])

        # 比较不同聚类方法
        comparison_results = analyzer.compare_clustering_methods(n_clusters=4)

        # 使用最佳方法进行详细聚类分析
        best_method = str(comparison_results.loc[comparison_results['silhouette_score'].idxmax(), 'method'])

        cluster_results = analyzer.perform_causal_clustering(method=best_method, n_clusters=4)
        cluster_analysis = analyzer.analyze_cluster_characteristics()

        # 保存分析结果
        output_data = {
            'network_analysis': patterns,
            'clustering_comparison': comparison_results.to_dict('records'),
            'best_clustering_analysis': cluster_analysis.to_dict('records') if cluster_analysis is not None else []
        }

        with open('output/causal_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    except Exception:
        pass


if __name__ == "__main__":
    main()