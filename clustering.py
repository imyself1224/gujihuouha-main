"""
聚类模块
负责使用 DBSCAN 算法对事件进行时空聚类
"""

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import pandas as pd


def normalize_time_features(years):
    """
    归一化时间特征到 [0, 1] 范围
    
    Args:
        years: numpy 数组，包含年份数据
        
    Returns:
        numpy 数组: 归一化后的时间特征
    """
    time_normalized = (years - years.min()) / (years.max() - years.min())
    return time_normalized


def prepare_features(df):
    """
    准备聚类特征：将地理位置和时间信息组合
    
    Args:
        df: 包含 latitude, longitude, year 的数据框
        
    Returns:
        tuple: (features, scaler) - 原始特征和缩放器对象
    """
    years = df['year'].values
    time_normalized = normalize_time_features(years)
    
    features = np.column_stack([
        df['latitude'].values,
        df['longitude'].values,
        time_normalized
    ])
    
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    return features_scaled, scaler, features


def find_best_dbscan_params(features_scaled, test_params=None):
    """
    通过网格搜索找到最佳的 DBSCAN 参数
    
    Args:
        features_scaled: 标准化后的特征数组
        test_params: 要测试的参数列表，格式为 [(eps, min_samples), ...]
                    如果为 None，使用默认参数
        
    Returns:
        tuple: (eps, min_samples) - 最佳参数
    """
    if test_params is None:
        test_params = [
            (0.3, 2), (0.5, 2), (0.7, 2), (1.0, 2),
            (0.5, 3), (0.5, 4)
        ]
    
    best_params = None
    best_score = float('inf')
    
    for eps, min_samples in test_params:
        dbscan_test = DBSCAN(eps=eps, min_samples=min_samples)
        clusters_test = dbscan_test.fit_predict(features_scaled)
        
        # 计算指标
        n_clusters_test = len(set(clusters_test)) - (1 if -1 in clusters_test else 0)
        n_noise_test = list(clusters_test).count(-1)
        noise_ratio = n_noise_test / len(clusters_test)
        
        # 评分函数：噪声比例权重高，聚类数偏离5时加分
        score = noise_ratio + 0.1 * abs(n_clusters_test - 5)
        
        if score < best_score:
            best_score = score
            best_params = (eps, min_samples)
    
    if best_params is not None:
        print(f"最佳参数: eps={best_params[0]}, min_samples={best_params[1]}, 评分={best_score:.4f}")
    return best_params


def perform_dbscan(features_scaled, eps=0.5, min_samples=2):
    """
    执行 DBSCAN 聚类
    
    Args:
        features_scaled: 标准化后的特征数组
        eps: DBSCAN 的 eps 参数
        min_samples: DBSCAN 的 min_samples 参数
        
    Returns:
        numpy 数组: 每个样本的聚类标签
    """
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    clusters = dbscan.fit_predict(features_scaled)
    
    n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
    n_noise = list(clusters).count(-1)
    
    print(f"聚类完成: {n_clusters} 个聚类, {n_noise} 个噪声点")
    
    return clusters


def add_clusters_to_dataframe(df, clusters):
    """
    将聚类结果添加到数据框
    
    Args:
        df: 原始数据框
        clusters: 聚类标签数组
        
    Returns:
        pandas DataFrame: 添加了聚类列的数据框
    """
    df_copy = df.copy()
    df_copy['cluster'] = clusters
    return df_copy
