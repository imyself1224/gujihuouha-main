# -*- coding: utf-8 -*-
"""
共现矩阵分析模块
"""

import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class CooccurrenceAnalyzer:
    """
    共现矩阵分析器
    用于提取实体和计算实体间的共现关系
    """
    
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.text = ""
        self.entities = {
            'PER': [],
            'LOC': [],
            'TIME': [],
            'OFI': []
        }
        self.person_aliases = {}
        self.cooccurrence_matrices = {}

    def extract_entities(self, text):
        """
        从文本中提取标注的实体
        
        Args:
            text: 包含{实体|类型}标注的文本
        """
        self.text = text

        # 定义实体提取的正则表达式
        pattern = r'\{([^|]+)\|([^}]+)\}'
        matches = re.findall(pattern, text)

        # 初始化实体列表
        for key in self.entities:
            self.entities[key] = []

        # 提取所有实体
        for match in re.finditer(pattern, text):
            entity_text = match.group(1)
            entity_type = match.group(2)
            start_pos = match.start()
            end_pos = match.end()

            if entity_type in self.entities:
                self.entities[entity_type].append({
                    'text': entity_text,
                    'type': entity_type,
                    'start': start_pos,
                    'end': end_pos
                })

    def add_person_alias(self, aliases, canonical_name):
        """
        Add person alias mapping
        
        Args:
            aliases: List of aliases
            canonical_name: Canonical name
        """
        for alias in aliases:
            self.person_aliases[alias] = canonical_name

    def get_canonical_person_name(self, name):
        """
        获取人物的规范名称
        
        Args:
            name: 人物名称
            
        Returns:
            str: 规范名称
        """
        return self.person_aliases.get(name, name)

    def build_cooccurrence_matrix(self, entity_type1, entity_type2):
        """
        构建两种实体类型之间的共现矩阵
        
        Args:
            entity_type1: 第一个实体类型
            entity_type2: 第二个实体类型
            
        Returns:
            pd.DataFrame: 共现矩阵
        """
        entities1 = self.entities[entity_type1]
        entities2 = self.entities[entity_type2]

        # 获取实体名称列表
        if entity_type1 == 'PER':
            entities1_names = [self.get_canonical_person_name(e['text']) for e in entities1]
        else:
            entities1_names = [e['text'] for e in entities1]

        if entity_type2 == 'PER':
            entities2_names = [self.get_canonical_person_name(e['text']) for e in entities2]
        else:
            entities2_names = [e['text'] for e in entities2]

        # 去重并排序
        unique_entities1 = sorted(list(set(entities1_names)))
        unique_entities2 = sorted(list(set(entities2_names)))

        # 初始化矩阵
        matrix = np.zeros((len(unique_entities1), len(unique_entities2)))

        # 计算共现次数
        for i, entity1 in enumerate(entities1):
            for j, entity2 in enumerate(entities2):
                if abs(entity1['start'] - entity2['start']) <= self.window_size * 10:
                    name1 = self.get_canonical_person_name(entity1['text']) if entity_type1 == 'PER' else entity1['text']
                    name2 = self.get_canonical_person_name(entity2['text']) if entity_type2 == 'PER' else entity2['text']

                    idx1 = unique_entities1.index(name1)
                    idx2 = unique_entities2.index(name2)
                    matrix[idx1][idx2] += 1
        
        # 转换为 DataFrame
        df = pd.DataFrame(matrix,
                         index=unique_entities1,
                         columns=unique_entities2)

        return df

    def analyze_all_cooccurrences(self):
        """
        分析所有实体类型对之间的共现关系
        
        Returns:
            dict: 共现矩阵字典
        """
        self.cooccurrence_matrices['人物-官职'] = self.build_cooccurrence_matrix('PER', 'OFI')
        self.cooccurrence_matrices['人物-地点'] = self.build_cooccurrence_matrix('PER', 'LOC')
        self.cooccurrence_matrices['人物-时间'] = self.build_cooccurrence_matrix('PER', 'TIME')

        return self.cooccurrence_matrices

    def get_top_cooccurrences(self, matrix_name, top_n=10):
        """
        获取共现关系的前N个
        
        Args:
            matrix_name: 矩阵名称
            top_n: 返回数量
            
        Returns:
            list: 共现关系列表
        """
        if matrix_name not in self.cooccurrence_matrices:
            return []

        matrix = self.cooccurrence_matrices[matrix_name]

        results = []
        for i, row_name in enumerate(matrix.index):
            for j, col_name in enumerate(matrix.columns):
                count = matrix.iloc[i, j]
                if count > 0:
                    results.append({
                        'entity1': row_name,
                        'entity2': col_name,
                        'count': int(count),
                        'type': matrix_name
                    })

        results.sort(key=lambda x: x['count'], reverse=True)

        return results[:top_n]

    def get_person_top_cooccurrences(self, person_name, top_n=5):
        """
        获取指定人物的前N个共现实体
        
        Args:
            person_name: 人物名称
            top_n: 返回数量
            
        Returns:
            dict: 包含地点、官职、时间的共现实体
        """
        results = {
            '地点': [],
            '官职': [],
            '时间': []
        }

        matrix_mappings = {
            '人物-地点': '地点',
            '人物-官职': '官职',
            '人物-时间': '时间'
        }

        for matrix_name, category in matrix_mappings.items():
            if matrix_name not in self.cooccurrence_matrices:
                continue

            matrix = self.cooccurrence_matrices[matrix_name]

            if person_name not in matrix.index:
                continue

            person_row = matrix.loc[person_name]
            person_cooccurrences = []

            for entity, count in person_row.items():
                if count > 0:
                    person_cooccurrences.append({
                        'entity': entity,
                        'count': int(count)
                    })

            person_cooccurrences.sort(key=lambda x: x['count'], reverse=True)
            results[category] = person_cooccurrences[:top_n]

        return results

    def get_all_persons(self):
        """
        获取所有人物列表
        
        Returns:
            set: 所有人物
        """
        all_persons = set()
        for matrix_name in ['人物-地点', '人物-官职', '人物-时间']:
            if matrix_name in self.cooccurrence_matrices:
                all_persons.update(self.cooccurrence_matrices[matrix_name].index.tolist())

        return all_persons
