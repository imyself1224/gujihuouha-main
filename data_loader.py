"""
数据加载模块
负责从 CSV 和 JSON 字符串中加载数据
所有数据都通过 Flask 接口传入
"""

import pandas as pd
import json
import io


def load_location_data_from_string(location_csv_string):
    """
    从 CSV 字符串加载地名数据
    
    Args:
        location_csv_string: 地名 CSV 字符串
        
    Returns:
        pandas DataFrame: 包含古代地名、现代地名、纬度、经度的数据框
    """
    location_df = pd.read_csv(io.StringIO(location_csv_string))
    print(f"已加载 {len(location_df)} 条地名记录")
    return location_df


def load_events_data_from_string(events_json_string):
    """
    从 JSON 字符串加载事件数据
    
    Args:
        events_json_string: 事件 JSON 字符串
        
    Returns:
        list: 事件列表，每个事件包含 id, year, location, description 等信息
    """
    events = json.loads(events_json_string)
    print(f"已加载 {len(events)} 个事件")
    return events


def load_all_data_from_strings(location_csv_string, events_json_string):
    """
    一次性从字符串加载所有必需的数据
    
    Args:
        location_csv_string: 地名 CSV 字符串
        events_json_string: 事件 JSON 字符串
        
    Returns:
        tuple: (location_df, events)
    """
    location_df = load_location_data_from_string(location_csv_string)
    events = load_events_data_from_string(events_json_string)
    return location_df, events
