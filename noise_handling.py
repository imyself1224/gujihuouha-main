"""
噪声点处理模块
负责处理 DBSCAN 聚类中的噪声点（孤立点）
使用多种策略：最近邻、时间相似性、单独聚类等
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors


def assign_noise_by_nearest_neighbor(df, features_scaled, eps):
    """
    使用最近邻方法将噪声点分配到最近的聚类
    
    Args:
        df: 包含聚类结果的数据框
        features_scaled: 标准化后的特征数组
        eps: DBSCAN 的 eps 参数，用于距离阈值
        
    Returns:
        pandas DataFrame: 处理后的数据框
    """
    df_copy = df.copy()
    noise_events = df_copy[df_copy['cluster'] == -1].copy()
    
    if len(noise_events) == 0:
        return df_copy
    
    # 获取有效的聚类样本
    valid_mask = df_copy['cluster'] != -1
    valid_features = features_scaled[valid_mask]
    valid_clusters = df_copy.loc[valid_mask, 'cluster'].values
    
    if len(valid_features) == 0:
        return df_copy
    
    # 找到每个噪声点的最近邻
    nbrs = NearestNeighbors(n_neighbors=1).fit(valid_features)
    noise_features = features_scaled[~valid_mask]
    distances, indices = nbrs.kneighbors(noise_features)
    
    # 分配距离足够近的噪声点
    for i, (idx, dist) in enumerate(zip(indices.flatten(), distances.flatten())):
        noise_idx = noise_events.index[i]
        nearest_cluster = valid_clusters[idx]
        
        if dist < eps * 1.5:
            df_copy.loc[noise_idx, 'cluster'] = nearest_cluster
            df_copy.loc[noise_idx, 'assigned_method'] = 'nearest_neighbor'
        else:
            df_copy.loc[noise_idx, 'assigned_method'] = 'remain_noise'
    
    print(f"通过最近邻方法处理了 {(distances.flatten() < eps * 1.5).sum()} 个噪声点")
    return df_copy


def assign_noise_by_time_similarity(df, time_threshold=5):
    """
    使用时间相似性方法将剩余的噪声点分配到时间最接近的聚类
    
    Args:
        df: 包含聚类结果的数据框
        time_threshold: 时间差阈值（年数）
        
    Returns:
        pandas DataFrame: 处理后的数据框
    """
    df_copy = df.copy()
    remaining_noise = df_copy[df_copy['cluster'] == -1].copy()
    
    if len(remaining_noise) == 0:
        return df_copy
    
    assigned_count = 0
    
    for noise_idx in remaining_noise.index:
        noise_event = df_copy.loc[noise_idx]
        min_time_diff = float('inf')
        best_cluster = -1
        
        # 找到时间最接近的聚类
        for cluster_id in set(df_copy['cluster']):
            if cluster_id == -1:
                continue
            cluster_events = df_copy[df_copy['cluster'] == cluster_id]
            time_diff = abs(cluster_events['year'].mean() - noise_event['year'])
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                best_cluster = cluster_id
        
        # 如果时间差在阈值内，分配到该聚类
        if min_time_diff < time_threshold:
            df_copy.loc[noise_idx, 'cluster'] = best_cluster
            df_copy.loc[noise_idx, 'assigned_method'] = 'time_similarity'
            assigned_count += 1
    
    print(f"通过时间相似性方法处理了 {assigned_count} 个噪声点")
    return df_copy


def create_isolated_clusters_for_remaining_noise(df):
    """
    为无法分配的噪声点创建单独的聚类
    
    Args:
        df: 包含聚类结果的数据框
        
    Returns:
        pandas DataFrame: 处理后的数据框
    """
    df_copy = df.copy()
    final_noise = df_copy[df_copy['cluster'] == -1].copy()
    
    if len(final_noise) == 0:
        return df_copy
    
    next_cluster_id = df_copy[df_copy['cluster'] != -1]['cluster'].max() + 1
    
    for noise_idx in final_noise.index:
        df_copy.loc[noise_idx, 'cluster'] = next_cluster_id
        df_copy.loc[noise_idx, 'assigned_method'] = 'isolated_cluster'
        next_cluster_id += 1
    
    print(f"为 {len(final_noise)} 个孤立点创建了单独的聚类")
    return df_copy


def handle_all_noise(df, features_scaled, eps, time_threshold=5):
    """
    执行完整的噪声处理流程
    
    Args:
        df: 包含聚类结果的数据框
        features_scaled: 标准化后的特征数组
        eps: DBSCAN 的 eps 参数
        time_threshold: 时间相似性阈值
        
    Returns:
        pandas DataFrame: 完全处理后的数据框
    """
    print("开始处理噪声点...")
    
    # 第一步：最近邻
    df = assign_noise_by_nearest_neighbor(df, features_scaled, eps)
    
    # 第二步：时间相似性
    df = assign_noise_by_time_similarity(df, time_threshold)
    
    # 第三步：创建孤立聚类
    df = create_isolated_clusters_for_remaining_noise(df)
    
    print("噪声点处理完成")
    return df


def initialize_assigned_method_column(df):
    """
    初始化 assigned_method 列
    
    Args:
        df: 数据框
        
    Returns:
        pandas DataFrame: 初始化后的数据框
    """
    df_copy = df.copy()
    df_copy['assigned_method'] = 'original'
    return df_copy
