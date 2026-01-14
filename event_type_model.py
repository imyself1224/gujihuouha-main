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

# 设置中文字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass


class HistoricalEventClusterAnalyzer:
    def __init__(self, data):
        """
        历史事件聚类分析器
        """
        self.data = data
        self.df = self._preprocess_data()
        self.event_categories = None
        self.cluster_results = None

    def _preprocess_data(self):
        """数据预处理"""
        records = []
        for item in self.data:
            text = item['text']
            event_list = item['event_list']
            affiliated = item.get('affiliated', '-1')

            for event in event_list:
                records.append({
                    'text': text,
                    'event_type': event['event_type'],
                    'trigger': event['trigger'],
                    'arguments': event['arguments'],
                    'affiliated': affiliated
                })

        return pd.DataFrame(records)

    def analyze_event_category_hierarchy(self):
        """分析事件类别层级结构"""
        # 提取一级和二级事件类别
        event_types = self.df['event_type'].tolist()

        # 分析类别结构（假设格式为"一级类别/二级类别"）
        primary_categories = []
        secondary_categories = []

        for event_type in event_types:
            if '/' in event_type:
                parts = event_type.split('/')
                primary_categories.append(parts[0])
                if len(parts) > 1:
                    secondary_categories.append(parts[1])
            else:
                primary_categories.append(event_type)
                secondary_categories.append('无二级分类')

        # 统计频次
        primary_counts = Counter(primary_categories)
        secondary_counts = Counter(secondary_categories)

        return {
            'primary_categories': primary_counts,
            'secondary_categories': secondary_counts,
            'all_categories': Counter(event_types)
        }

    def extract_category_features(self):
        """提取事件类别特征"""
        # 获取所有事件类别
        event_categories = list(self.df['event_type'].unique())

        # 为每个类别创建特征向量
        category_features = {}

        for category in event_categories:
            # 1. 类别出现频次
            freq = len(self.df[self.df['event_type'] == category])

            # 2. 参数类型多样性
            category_data = self.df[self.df['event_type'] == category]
            argument_types = set()
            for args in category_data['arguments']:
                for arg in args:
                    argument_types.add(arg['role'])
            argument_diversity = len(argument_types)

            # 3. 触发词特征
            triggers = category_data['trigger'].tolist()
            trigger_length = np.mean([len(str(trigger)) for trigger in triggers])

            # 4. 文本长度特征
            text_lengths = [len(text) for text in category_data['text']]
            avg_text_length = np.mean(text_lengths)

            category_features[category] = {
                'frequency': freq,
                'argument_diversity': argument_diversity,
                'avg_trigger_length': trigger_length,
                'avg_text_length': avg_text_length
            }

        return category_features

    def perform_clustering(self, n_clusters=5, method='kmeans'):
        """执行聚类分析"""
        # 提取特征
        category_features = self.extract_category_features()
        categories = list(category_features.keys())

        # 创建特征矩阵
        feature_matrix = []
        for category in categories:
            features = category_features[category]
            feature_vector = [
                features['frequency'],
                features['argument_diversity'],
                features['avg_trigger_length'],
                features['avg_text_length']
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

        # 【核心改进】计算轮廓系数前手动剔除噪声点 -1
        # 在某些系统下，DBSCAN的-1标签会导致 silhouette_score 内部发生硬崩溃
        silhouette_avg = 0
        if n_clusters_found >= 2:
            try:
                mask = (clusters != -1)
                if np.sum(mask) >= 2:
                    score_data = features_scaled[mask]
                    score_labels = clusters[mask]
                    silhouette_avg = float(silhouette_score(score_data, score_labels))
                else:
                    pass
            except Exception as e:
                pass
        else:
            pass

        # 保存结果
        self.cluster_results = {
            'categories': categories,
            'clusters': clusters,
            'features': features_scaled,
            'silhouette_score': silhouette_avg,
            'feature_matrix': feature_matrix
        }

        return self.cluster_results

    def visualize_clusters(self, output_file='output/image/event_clusters_output.png'):
        """可视化聚类结果"""
        if self.cluster_results is None:
            return

        try:
            # PCA降维可视化
            pca = PCA(n_components=2)
            features_2d = pca.fit_transform(self.cluster_results['features'])

            plt.figure(figsize=(12, 8))

            # 创建散点图
            scatter = plt.scatter(features_2d[:, 0], features_2d[:, 1],
                                  c=self.cluster_results['clusters'],
                                  cmap='viridis', s=100, alpha=0.7)

            # 添加类别标签
            for i, category in enumerate(self.cluster_results['categories']):
                plt.annotate(category, (features_2d[i, 0], features_2d[i, 1]),
                             xytext=(5, 5), textcoords='offset points',
                             fontsize=8, alpha=0.8)

            plt.colorbar(scatter, label='聚类编号')
            plt.title(f'历史事件类别聚类分析\n轮廓系数: {self.cluster_results["silhouette_score"]:.3f}')
            plt.xlabel('PCA主成分1')
            plt.ylabel('PCA主成分2')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # 先保存到文件，防止 show() 崩溃
            plt.savefig(output_file, dpi=300)
            
        except Exception as e:
            pass

    def analyze_cluster_characteristics(self):
        """分析每个聚类的特征"""
        if self.cluster_results is None:
            return
            
        cluster_results_data = self.cluster_results

        results = []
        unique_clusters = np.unique(cluster_results_data['clusters'])

        for cluster_id in unique_clusters:
            cluster_indices = np.where(cluster_results_data['clusters'] == cluster_id)[0]
            cluster_categories = [cluster_results_data['categories'][i] for i in cluster_indices]

            # 计算聚类中心特征
            cluster_features = cluster_results_data['feature_matrix'][cluster_indices]
            centroid = np.mean(cluster_features, axis=0)

            results.append({
                'cluster_id': cluster_id,
                'num_categories': len(cluster_categories),
                'categories': cluster_categories,
                'avg_frequency': centroid[0],
                'avg_argument_diversity': centroid[1],
                'avg_trigger_length': centroid[2],
                'avg_text_length': centroid[3]
            })

        return pd.DataFrame(results)

    def generate_category_report(self):
        """生成事件类别分析报告"""
        # 类别层级分析
        hierarchy = self.analyze_event_category_hierarchy()

        if self.cluster_results is not None:
            cluster_df = self.analyze_cluster_characteristics()


# 主程序
def main():
    try:
        # 读取数据
        data_path = "output/historical_relations/EE-Hangaozubenji_updated.json"
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 创建分析器
        analyzer = HistoricalEventClusterAnalyzer(data)

        # 生成分析报告
        analyzer.generate_category_report()

        # 执行聚类分析
        cluster_results = analyzer.perform_clustering(n_clusters=6, method='dbscan')

        # 可视化结果
        analyzer.visualize_clusters()

        # 详细聚类分析
        cluster_analysis = analyzer.analyze_cluster_characteristics()

        # 保存结果到文件
        if analyzer.cluster_results is not None:
            output_path = 'output/csv/event_category_clusters.csv'
            output_df = pd.DataFrame({
                'event_category': analyzer.cluster_results['categories'],
                'cluster_id': analyzer.cluster_results['clusters']
            })
            output_df.to_csv(output_path, index=False, encoding='utf-8-sig')

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