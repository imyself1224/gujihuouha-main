# -*- coding: utf-8 -*-
"""
数据加载模块
"""

def load_text_file(file_path):
    """
    加载文本文件
    
    Args:
        file_path: 文本文件路径
        
    Returns:
        str: 文件内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text
