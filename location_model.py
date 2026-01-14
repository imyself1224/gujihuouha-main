import os
# 设置环境变量以抑制警告
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"

import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use('Agg')  # 强制使用完全离线的绘图后端，防止弹窗导致的崩溃
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
from matplotlib.font_manager import FontProperties
import matplotlib

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class LocationClusterAnalyzer:
    def __init__(self, data):
        """
        地点维度聚类分析器
        """
        self.data = data
        self.location_data = self._extract_location_data()
        self.df = self._preprocess_data()
        self.cluster_results = None

    def _extract_location_data(self):
        """从数据中提取所有地点信息"""
        location_records = []

        for item in self.data:
            text = item['text']
            event_list = item['event_list']
            affiliated = item.get('affiliated', '-1')

            for event in event_list:
                for arg in event['arguments']:
                    if arg['role'] in ['地点', '目的地', '出发地', '投降地点', '埋葬地点']:
                        location_records.append({
                            'text': text,
                            'event_type': event['event_type'],
                            'trigger': event['trigger'],
                            'location': arg['argument'],
                            'role_type': arg['role'],
                            'affiliated': affiliated
                        })

        return location_records

    def _preprocess_data(self):
        """数据预处理"""
        return pd.DataFrame(self.location_data)

    def analyze_location_distribution(self):
        """分析地点分布特征"""
        # 地点出现频次统计
        location_counts = Counter(self.df['location'])

        # 地点类型分布
        role_counts = Counter(self.df['role_type'])

        # 事件类型与地点的关系
        event_location_pairs = self.df.groupby(['event_type', 'location']).size().reset_index(name='count')

        return {
            'location_frequency': location_counts,
            'role_distribution': role_counts,
            'event_location_relations': event_location_pairs
        }

    def extract_location_features(self):
        """提取地点特征"""
        # 获取所有地点
        locations = list(self.df['location'].unique())

        # 为每个地点创建特征向量
        location_features = {}

        for location in locations:
            # 获取该地点的所有记录
            location_data = self.df[self.df['location'] == location]

            # 1. 地点出现频次
            freq = len(location_data)

            # 2. 涉及的事件类型多样性
            event_types = set(location_data['event_type'])
            event_diversity = len(event_types)

            # 3. 地点角色类型多样性
            role_types = set(location_data['role_type'])
            role_diversity = len(role_types)

            # 4. 文本特征（地点相关的文本平均长度）
            text_lengths = [len(text) for text in location_data['text']]
            avg_text_length = np.mean(text_lengths)

            # 5. 时间维度（affiliated字段，表示历史阶段）
            time_periods = location_data['affiliated'].unique()
            time_diversity = len(time_periods)

            # 6. 触发词多样性
            triggers = set(location_data['trigger'])
            trigger_diversity = len(triggers)

            location_features[location] = {
                'frequency': freq,
                'event_diversity': event_diversity,
                'role_diversity': role_diversity,
                'avg_text_length': avg_text_length,
                'time_diversity': time_diversity,
                'trigger_diversity': trigger_diversity
            }

        return location_features

    def perform_clustering(self, n_clusters=5, method='hierarchical'):
        """执行地点聚类分析"""
        # 提取特征
        location_features = self.extract_location_features()
        locations = list(location_features.keys())

        # 创建特征矩阵
        feature_matrix = []
        for location in locations:
            features = location_features[location]
            feature_vector = [
                features['frequency'],
                features['event_diversity'],
                features['role_diversity'],
                features['avg_text_length'],
                features['time_diversity'],
                features['trigger_diversity']
            ]
            feature_matrix.append(feature_vector)

        feature_matrix = np.array(feature_matrix)

        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(feature_matrix)

        # 选择聚类方法
        if method == 'kmeans':
            clusterer = KMeans(n_clusters=n_clusters, random_state=42)
        elif method == 'hierarchical':
            clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        elif method == 'dbscan':
            clusterer = DBSCAN(eps=0.5, min_samples=2)
        else:
            clusterer = KMeans(n_clusters=n_clusters, random_state=42)

        # 执行聚类
        clusters = clusterer.fit_predict(features_scaled)

        # 统计聚类数量（排除噪声点-1）
        unique_labels = set(clusters)
        n_clusters_found = len(unique_labels) - (1 if -1 in unique_labels else 0)

        # 计算轮廓系数
        if n_clusters_found >= 2:
            silhouette_avg = silhouette_score(features_scaled, clusters)
        else:
            silhouette_avg = -1  # 无法计算单一簇的轮廓系数

        # 保存结果
        self.cluster_results = {
            'locations': locations,
            'clusters': clusters,
            'features': features_scaled,
            'feature_matrix': feature_matrix,
            'silhouette_score': silhouette_avg,
            'location_features': location_features
        }

        return self.cluster_results

    def visualize_clusters(self, output_file='output/image/location_clusters_output.png'):
        """可视化地点聚类结果"""
        if self.cluster_results is None:
            return

        try:
            # PCA降维可视化
            pca = PCA(n_components=2)
            features_2d = pca.fit_transform(self.cluster_results['features'])

            plt.figure(figsize=(18, 14))  # 进一步增大图形尺寸

            # 创建散点图
            scatter = plt.scatter(features_2d[:, 0], features_2d[:, 1],
                                  c=self.cluster_results['clusters'],
                                  cmap='viridis', s=100, alpha=0.7)

            # 添加所有地点标签
            for i, location in enumerate(self.cluster_results['locations']):
                plt.annotate(location, (features_2d[i, 0], features_2d[i, 1]),
                             xytext=(3, 3), textcoords='offset points',
                             fontsize=6, alpha=0.6)

            plt.colorbar(scatter, label='聚类编号')
            plt.title(f'历史事件地点聚类分析\n轮廓系数: {self.cluster_results["silhouette_score"]:.3f}')
            plt.xlabel('PCA主成分1')
            plt.ylabel('PCA主成分2')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 先保存，防止崩溃
            plt.savefig(output_file, dpi=300)
            
        except Exception as e:
            pass
    # def visualize_clusters(self):
    #     """可视化地点聚类结果"""
    #     if self.cluster_results is None:
    #         print("请先执行聚类分析")
    #         return
    #
    #     # PCA降维可视化
    #     pca = PCA(n_components=2)
    #     features_2d = pca.fit_transform(self.cluster_results['features'])
    #
    #     plt.figure(figsize=(14, 10))
    #
    #     # 创建散点图
    #     scatter = plt.scatter(features_2d[:, 0], features_2d[:, 1],
    #                           c=self.cluster_results['clusters'],
    #                           cmap='viridis', s=100, alpha=0.7)
    #
    #     # 添加地点标签（只显示重要的地点）
    #     location_features = self.cluster_results['location_features']
    #     for i, location in enumerate(self.cluster_results['locations']):
    #         freq = location_features[location]['frequency']
    #         # 只对高频地点添加标签，避免过于拥挤
    #         if freq > np.percentile([lf['frequency'] for lf in location_features.values()], 70):
    #             plt.annotate(location, (features_2d[i, 0], features_2d[i, 1]),
    #                          xytext=(5, 5), textcoords='offset points',
    #                          fontsize=8, alpha=0.8)
    #
    #     plt.colorbar(scatter, label='聚类编号')
    #     plt.title(f'历史事件地点聚类分析\n轮廓系数: {self.cluster_results["silhouette_score"]:.3f}')
    #     plt.xlabel('PCA主成分1')
    #     plt.ylabel('PCA主成分2')
    #     plt.grid(True, alpha=0.3)
    #     plt.tight_layout()
    #     plt.show()

    def analyze_cluster_characteristics(self):
        """分析每个聚类的特征"""
        if self.cluster_results is None:
            return
            
        cluster_results_data = self.cluster_results

        results = []
        unique_clusters = np.unique(cluster_results_data['clusters'])

        for cluster_id in unique_clusters:
            cluster_indices = np.where(cluster_results_data['clusters'] == cluster_id)[0]
            cluster_locations = [cluster_results_data['locations'][i] for i in cluster_indices]

            # 计算聚类中心特征
            cluster_features = cluster_results_data['feature_matrix'][cluster_indices]
            centroid = np.mean(cluster_features, axis=0)

            # 获取该聚类中的高频地点
            location_features = cluster_results_data['location_features']
            cluster_location_data = [(loc, location_features[loc]['frequency']) for loc in cluster_locations]
            cluster_location_data.sort(key=lambda x: x[1], reverse=True)
            top_locations = [loc for loc, freq in cluster_location_data[:5]]

            results.append({
                'cluster_id': cluster_id,
                'num_locations': len(cluster_locations),
                'top_locations': top_locations,
                'avg_frequency': centroid[0],
                'avg_event_diversity': centroid[1],
                'avg_role_diversity': centroid[2],
                'avg_text_length': centroid[3],
                'avg_time_diversity': centroid[4],
                'avg_trigger_diversity': centroid[5]
            })

        return pd.DataFrame(results)

    def generate_location_network(self):
        """生成地点共现网络（可选功能）"""
        # 分析地点在同一事件中的共现关系
        location_cooccurrence = {}

        for item in self.data:
            event_locations = set()
            for event in item['event_list']:
                for arg in event['arguments']:
                    if arg['role'] in ['地点', '目的地', '出发地']:
                        event_locations.add(arg['argument'])

            # 记录共现关系
            locations_list = list(event_locations)
            for i, loc1 in enumerate(locations_list):
                for loc2 in locations_list[i + 1:]:
                    pair = tuple(sorted([loc1, loc2]))
                    location_cooccurrence[pair] = location_cooccurrence.get(pair, 0) + 1

        return location_cooccurrence

    def generate_location_report(self):
        """生成地点分析报告"""
        # 地点分布分析
        distribution = self.analyze_location_distribution()

        if self.cluster_results is not None:
            cluster_df = self.analyze_cluster_characteristics()

    def plot_location_frequency(self):
        """绘制地点频率分布图"""
        distribution = self.analyze_location_distribution()
        top_locations = distribution['location_frequency'].most_common(15)

        plt.figure(figsize=(12, 8))
        locations, counts = zip(*top_locations)

        plt.barh(range(len(locations)), counts)
        plt.yticks(range(len(locations)), locations)
        plt.xlabel('出现频次')
        plt.title('高频地点TOP15')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('output/image/location_frequency.png')

    def plot_role_distribution(self):
        """绘制角色类型分布图"""
        distribution = self.analyze_location_distribution()

        plt.figure(figsize=(10, 6))
        roles, counts = zip(*distribution['role_distribution'].items())

        plt.pie(counts, labels=roles, autopct='%1.1f%%', startangle=90)
        plt.title('地点角色类型分布')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig('output/image/role_distribution.png')


# 主程序
def main():
    try:
        # 读取数据
        data_path = "output/historical_relations/EE-Hangaozubenji_updated.json"
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 创建地点分析器
        analyzer = LocationClusterAnalyzer(data)

        # 生成分析报告
        analyzer.generate_location_report()

        # 绘制基础统计图
        analyzer.plot_location_frequency()
        analyzer.plot_role_distribution()

        # 执行聚类分析
        cluster_results = analyzer.perform_clustering(n_clusters=5, method='hierarchical')

        # 可视化结果
        analyzer.visualize_clusters()

        # 详细聚类分析
        cluster_analysis = analyzer.analyze_cluster_characteristics()

        # 保存结果到文件
        if analyzer.cluster_results is not None:
            output_path = 'output/csv/location_clusters.csv'
            output_df = pd.DataFrame({
                'location': analyzer.cluster_results['locations'],
                'cluster_id': analyzer.cluster_results['clusters'],
                'frequency': [analyzer.cluster_results['location_features'][loc]['frequency']
                            for loc in analyzer.cluster_results['locations']]
            })
            output_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        # 生成地点共现网络
        cooccurrence_network = analyzer.generate_location_network()

        # 显示强共现关系
        strong_connections = {pair: count for pair, count in cooccurrence_network.items() if count > 1}

    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        pass
    except Exception as e:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()