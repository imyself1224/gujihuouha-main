"""
聚类服务模块
封装聚类分析逻辑，支持从字符串数据源处理
"""

import pandas as pd
import json
import io
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import os
from datetime import datetime

from data_loader import load_all_data_from_strings
from location_matcher import enrich_events
from clustering import (
    prepare_features,
    find_best_dbscan_params,
    perform_dbscan,
    add_clusters_to_dataframe
)
from noise_handling import handle_all_noise, initialize_assigned_method_column
from hierarchical_clustering import analyze_hierarchical_results


class ClusteringService:
    """聚类服务类，提供核心聚类功能"""
    
    def __init__(self):
        """初始化服务"""
        self.last_result = None
    
    def perform_clustering(self, location_csv_string, events_json_string):
        """
        执行完整的聚类分析流程
        
        Args:
            location_csv_string: 地名 CSV 数据字符串
            events_json_string: 事件 JSON 数据字符串
        
        Returns:
            dict: 包含聚类结果的字典
        """
        try:
            print("\n" + "=" * 60)
            print("开始聚类分析...")
            print("=" * 60)
            
            # ============ 第一步：数据加载 ============
            print("\n[第一步] 加载数据...")
            location_df, events = load_all_data_from_strings(location_csv_string, events_json_string)
            print(f"已加载 {len(location_df)} 条地名记录")
            print(f"已加载 {len(events)} 个事件")
            
            # ============ 第二步：地名匹配和事件丰富 ============
            print("\n[第二步] 进行地名匹配和地理信息丰富...")
            df = enrich_events(events, location_df)
            print(f"丰富后的数据框大小: {df.shape}")
            
            # ============ 第三步：准备聚类特征 ============
            print("\n[第三步] 准备聚类特征...")
            features_scaled, scaler, features = prepare_features(df)
            print(f"特征维度: {features_scaled.shape}")
            
            # ============ 第四步：寻找最佳参数 ============
            print("\n[第四步] 寻找最佳 DBSCAN 参数...")
            best_params = find_best_dbscan_params(features_scaled)
            if best_params is None:
                raise ValueError("Failed to find best DBSCAN parameters")
            eps, min_samples = best_params
            
            # ============ 第五步：执行 DBSCAN 聚类 ============
            print("\n[第五步] 执行 DBSCAN 聚类...")
            clusters = perform_dbscan(features_scaled, eps=eps, min_samples=min_samples)
            df = add_clusters_to_dataframe(df, clusters)
            df = initialize_assigned_method_column(df)
            
            # ============ 第六步：处理噪声点 ============
            print("\n[第六步] 处理噪声点...")
            df = handle_all_noise(df, features_scaled, eps, time_threshold=5)
            
            # ============ 第七步：层次聚类分析 ============
            print("\n[第七步] 执行层次聚类分析...")
            hierarchical_results = analyze_hierarchical_results(df, features_scaled, df['cluster'].values)
            
            # ============ 收集结果信息 ============
            n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
            n_noise = list(clusters).count(-1)
            
            # 保存完整结果供后续使用
            self.last_result = {
                'df': df,
                'hierarchical_results': hierarchical_results,
                'features_scaled': features_scaled,
                'best_params': best_params
            }
            
            print("\n" + "=" * 60)
            print("分析完成！")
            print("=" * 60)
            
            # 返回摘要数据
            return {
                'clusters': self._format_clusters(df),
                'summary': {
                    'total_events': len(df),
                    'num_clusters': n_clusters,
                    'num_noise': n_noise,
                    'best_params': {
                        'eps': float(eps),
                        'min_samples': int(min_samples)
                    }
                }
            }
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_full_dataframe(self, location_csv_string, events_json_string):
        """
        获取完整的结果数据框
        
        Args:
            location_csv_string: 地名 CSV 数据字符串
            events_json_string: 事件 JSON 数据字符串
        
        Returns:
            dict: 包含完整df的字典
        """
        if self.last_result is None:
            # 如果没有缓存结果，执行一次聚类
            self.perform_clustering(location_csv_string, events_json_string)
        
        return self.last_result
    
    def _format_clusters(self, df):
        """
        格式化聚类结果为字典列表
        
        Args:
            df: 包含聚类结果的数据框
        
        Returns:
            list: 聚类结果列表
        """
        clusters = []
        
        if df.shape[0] == 0:
            return clusters
        
        # 按聚类ID分组
        grouped = df.groupby('cluster')
        
        for cluster_id, group in grouped:
            cluster_data = {
                'cluster_id': int(cluster_id) if cluster_id != -1 else -1,
                'size': len(group),
                'events': []
            }
            
            # 收集聚类中的事件
            for idx, row in group.iterrows():
                event = {
                    'id': str(row.get('id', idx)),
                    'year': int(row.get('year', 0)),
                    'location': str(row.get('location', '')),
                    'location_ancient': str(row.get('location_ancient', '')),
                    'location_modern': str(row.get('location_modern', '')),
                    'description': str(row.get('description', '')),
                    'latitude': float(row.get('latitude', 0)) if pd.notna(row.get('latitude')) else None,
                    'longitude': float(row.get('longitude', 0)) if pd.notna(row.get('longitude')) else None,
                    'assigned_method': str(row.get('assigned_method', ''))
                }
                cluster_data['events'].append(event)
            
            clusters.append(cluster_data)
        
        return clusters
