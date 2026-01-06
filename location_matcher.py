"""
地名匹配模块
负责将事件中的古代地名与现代地名进行匹配，并提取地理坐标
"""

import pandas as pd
import numpy as np


def match_location(location_name, location_df):
    """
    将古代地名匹配到现代地名及其坐标
    
    Args:
        location_name: 古代地名字符串（可能包含多个地名，用、或,分隔）
        location_df: 包含地名映射的 DataFrame
        
    Returns:
        tuple: (ancient_name, modern_name, latitude, longitude)
               如果匹配失败返回 (None, None, None, None)
    """
    # 分解多个地名
    locations = [loc.strip() for loc in location_name.replace('、', ',').split(',')]
    matched_coords = []
    
    for loc in locations:
        # 精确匹配
        match = location_df[location_df['古代地名'] == loc]
        if not match.empty:
            matched_coords.append({
                'ancient': loc,
                'modern': match.iloc[0]['现代地名'],
                'lat': match.iloc[0]['纬度'],
                'lon': match.iloc[0]['经度']
            })
        else:
            # 模糊匹配：检查是否包含关键词
            for _, row in location_df.iterrows():
                if loc in row['古代地名'] or row['古代地名'] in loc:
                    matched_coords.append({
                        'ancient': loc,
                        'modern': row['现代地名'],
                        'lat': row['纬度'],
                        'lon': row['经度']
                    })
                    break
    
    # 如果有匹配结果，返回第一个匹配的地名
    if matched_coords:
        avg_lat = np.mean([m['lat'] for m in matched_coords])
        avg_lon = np.mean([m['lon'] for m in matched_coords])
        return matched_coords[0]['ancient'], matched_coords[0]['modern'], avg_lat, avg_lon
    else:
        return None, None, None, None


def enrich_events(events, location_df):
    """
    为事件添加地理信息（现代地名和坐标）
    
    Args:
        events: 事件列表
        location_df: 地名映射数据框
        
    Returns:
        pandas DataFrame: 包含地理信息的事件数据框
    """
    enriched_events = []
    
    for event in events:
        ancient, modern, lat, lon = match_location(event['location'], location_df)
        
        if lat is not None:
            enriched_events.append({
                'id': event['id'],
                'year': event['year'],
                'description': event['description'],
                'location_ancient': ancient,
                'location_modern': modern,
                'latitude': lat,
                'longitude': lon
            })
    
    df = pd.DataFrame(enriched_events)
    print(f"成功匹配 {len(df)} 个事件的地理信息")
    return df
