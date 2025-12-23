"""
工具函数模块
"""

import numpy as np
import re
from scipy.stats import rankdata


def rank_fusion(scores1, scores2, method='rrf', k=120):
    """
    使用排名融合方法合并两个评分
    
    Args:
        scores1: 第一个评分字典
        scores2: 第二个评分字典
        method: 融合方法('avg'或'rrf')
        k: RRF中的平滑参数
        
    Returns:
        dict: 融合后的评分字典
    """
    keys = list(scores1.keys())
    vals1 = np.array([scores1[k] for k in keys])
    vals2 = np.array([scores2[k] for k in keys])

    # 计算排名
    rank1 = rankdata(-vals1, method='average')
    rank2 = rankdata(-vals2, method='average')

    # 选择融合方法
    if method == 'avg':
        fused_rank = (rank1 + rank2) / 2
        fused_score = -fused_rank
    elif method == 'rrf':
        # Reciprocal Rank Fusion
        fused_score = 1 / (k + rank1) + 1 / (k + rank2)
    else:
        raise ValueError(f"未支持的融合方法: {method}")

    # 按融合评分排序
    order = np.argsort(-fused_score)
    fused_result = {keys[i]: fused_score[i] for i in order}
    
    return fused_result


def format_text_with_entities(text, entities):
    """
    将SpringBoot传入的数据格式转换为模型需要的格式
    
    SpringBoot格式:
    {
        "text": "掾、主吏萧何、曹参乃曰...",
        "entities": {
            "OFI": ["主吏"],
            "PER": ["掾", "萧何", "曹参"]
        }
    }
    
    转换为模型格式:
    {高祖|PER}，{沛|LOC}{丰邑|LOC}...
    
    Args:
        text (str): 原始文本
        entities (dict): 实体字典，格式为 {'PER': [...], 'LOC': [...], 'OFI': [...]}
        
    Returns:
        str: 标注后的文本
    """
    if not entities or not isinstance(entities, dict):
        return text
    
    # 构建实体映射表，记录每个实体的类型
    entity_type_map = {}
    for entity_type, entity_list in entities.items():
        for entity_name in entity_list:
            if entity_name not in entity_type_map:
                entity_type_map[entity_name] = entity_type
    
    if not entity_type_map:
        return text
    
    # 按实体名称长度从长到短排序，避免短实体覆盖长实体
    sorted_entities = sorted(entity_type_map.keys(), key=len, reverse=True)
    
    # 直接进行字符串替换（适合中文，不使用\b边界符）
    result = text
    for entity_name in sorted_entities:
        entity_type = entity_type_map[entity_name]
        replacement = f'{{{entity_name}|{entity_type}}}'
        # 使用简单的字符串替换，适合中文文本
        result = result.replace(entity_name, replacement)
    
    return result
