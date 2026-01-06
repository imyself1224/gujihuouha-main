"""
层次聚类模块
负责对 DBSCAN 聚类结果进行进一步的层次聚类分析
将每个主聚类分解为多个子聚类
"""

import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
import numpy as np
import os


def perform_hierarchical_clustering_on_cluster(cluster_features, cluster_data, n_subclusters=3):
    """
    对单个聚类进行层次聚类分解
    
    Args:
        cluster_features: 该聚类的特征矩阵（标准化后的）
        cluster_data: 该聚类对应的数据框
        n_subclusters: 要分解的子聚类数量（最多）
        
    Returns:
        pandas DataFrame: 添加了 sub_cluster 列的数据框
    """
    if len(cluster_features) < 2:
        cluster_data_copy = cluster_data.copy()
        cluster_data_copy['sub_cluster'] = 1
        return cluster_data_copy
    
    # 计算链接矩阵
    linkage_matrix = linkage(cluster_features, method='ward')
    
    # 切割层次聚类树，生成子类
    actual_subclusters = min(n_subclusters, len(cluster_features))
    sub_clusters = fcluster(linkage_matrix, actual_subclusters, criterion='maxclust')
    
    cluster_data_copy = cluster_data.copy()
    cluster_data_copy['sub_cluster'] = sub_clusters
    
    return cluster_data_copy


def analyze_hierarchical_results(df, features_scaled, main_clusters):
    """
    对每个主聚类进行层次聚类分析，并生成分析结果
    
    Args:
        df: 包含主聚类结果的数据框
        features_scaled: 标准化后的特征数组
        main_clusters: 主聚类标签数组
        
    Returns:
        list: 层次聚类分析结果列表
    """
    hierarchical_results = []
    
    for cluster_id in sorted(set(main_clusters)):
        # 获取该聚类的数据
        cluster_mask = df['cluster'] == cluster_id
        cluster_features = features_scaled[cluster_mask]
        cluster_data = df[cluster_mask].copy()
        
        if len(cluster_features) < 2:
            continue
        
        # 进行层次聚类
        cluster_data = perform_hierarchical_clustering_on_cluster(
            cluster_features, 
            cluster_data, 
            n_subclusters=3
        )
        
        # 分析每个子聚类
        for sub_id in sorted(set(cluster_data['sub_cluster'])):
            sub_events = cluster_data[cluster_data['sub_cluster'] == sub_id]
            
            # 计算子聚类的时间和空间特征
            year_range = f"{int(sub_events['year'].min())} ~ {int(sub_events['year'].max())}"
            locations = ', '.join(sub_events['location_ancient'].unique())
            event_descriptions = '; '.join(
                sub_events['description'].astype(str).str[:20] + '...'
            )
            
            hierarchical_results.append({
                'main_cluster': cluster_id + 1,
                'sub_cluster': sub_id,
                'event_count': len(sub_events),
                'year_range': year_range,
                'locations': locations,
                'events': event_descriptions
            })
    
    return hierarchical_results


def save_hierarchical_results(hierarchical_results, output_path='./results/hierarchical_clustering.csv'):
    """
    将层次聚类结果保存为 CSV 文件
    
    Args:
        hierarchical_results: 层次聚类分析结果列表
        output_path: 输出文件路径（默认保存到 results 文件夹）
        
    Returns:
        pandas DataFrame: 保存的结果数据框
    """
    if not hierarchical_results:
        print("没有层次聚类结果可保存")
        return None
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    hierarchical_df = pd.DataFrame(hierarchical_results)
    hierarchical_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"层次聚类结果已保存到: {output_path}")
    
    return hierarchical_df


def print_hierarchical_summary(hierarchical_results):
    """
    打印层次聚类结果的摘要
    
    Args:
        hierarchical_results: 层次聚类分析结果列表
    """
    if not hierarchical_results:
        print("没有层次聚类结果")
        return
    
    print("\n========== 层次聚类分析摘要 ==========")
    
    current_main_cluster = None
    for result in hierarchical_results:
        if result['main_cluster'] != current_main_cluster:
            current_main_cluster = result['main_cluster']
            print(f"\n【第 {current_main_cluster} 个主聚类】")
        
        print(f"  └─ 子聚类 {result['sub_cluster']}: "
              f"{result['event_count']} 个事件, "
              f"时间: {result['year_range']}, "
              f"地点: {result['locations']}")
    
    print("\n====================================\n")
