# -*- coding: utf-8 -*-
"""
BERT语义相似度分析模块
"""

import re
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import warnings

warnings.filterwarnings('ignore')


class ImprovedBertSimilarityAnalyzer:
    """
    改进版BERT语义相似度分析器
    使用预训练模型计算实体的语义相似度
    """
    
    def __init__(self, model_name='./GuWen-Bert', device='auto'):
        """
        初始化分析器
        
        Args:
            model_name: 本地模型路径或HuggingFace模型名称
            device: 设备选择('auto'/'cuda'/'cpu')
        """
        self.model_name = model_name

        # Device selection
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        print(f"Using device: {self.device}")

        # Load model and tokenizer
        print(f"Loading model: {model_name}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.model.eval()
            print("Model loaded successfully")
        except Exception as e:
            print(f"Model loading failed: {e}")
            raise

        self.text = ""
        self.clean_text = ""
        self.entities = {
            'PER': [],
            'LOC': [],
            'TIME': [],
            'OFI': []
        }
        self.person_aliases = {}
        self.entity_embeddings = {}
        self.similarity_matrices = {}
        self.context_window = 50

    def extract_entities(self, text):
        """
        从文本中提取标注的实体并构建清洁文本
        
        Args:
            text: 包含{实体|类型}标注的文本
        """
        self.text = text

        # 构建清洁文本和位置映射
        clean_text = ""
        position_mapping = {}

        i = 0
        clean_pos = 0
        while i < len(text):
            if text[i] == '{':
                end_pos = text.find('}', i)
                if end_pos != -1:
                    annotation = text[i+1:end_pos]
                    if '|' in annotation:
                        entity_text, entity_type = annotation.split('|', 1)

                        for j in range(i, end_pos + 1):
                            if j < i + 1 + len(entity_text):
                                position_mapping[j] = clean_pos + (j - i - 1)

                        clean_text += entity_text
                        clean_pos += len(entity_text)

                    i = end_pos + 1
                else:
                    clean_text += text[i]
                    position_mapping[i] = clean_pos
                    clean_pos += 1
                    i += 1
            else:
                clean_text += text[i]
                position_mapping[i] = clean_pos
                clean_pos += 1
                i += 1

        self.clean_text = clean_text

        # 提取实体信息
        pattern = r'\{([^|]+)\|([^}]+)\}'

        for key in self.entities:
            self.entities[key] = []

        clean_pos = 0
        for match in re.finditer(pattern, text):
            entity_text = match.group(1)
            entity_type = match.group(2)
            start_pos_original = match.start()
            end_pos_original = match.end()

            start_pos_clean = clean_pos
            end_pos_clean = clean_pos + len(entity_text)
            clean_pos = end_pos_clean

            if entity_type in self.entities:
                self.entities[entity_type].append({
                    'text': entity_text,
                    'type': entity_type,
                    'start_original': start_pos_original,
                    'end_original': end_pos_original,
                    'start_clean': start_pos_clean,
                    'end_clean': end_pos_clean
                })

    def get_entity_context(self, entity, context_window=None):
        """
        获取实体的上下文
        
        Args:
            entity: 实体信息字典
            context_window: 上下文窗口大小
            
        Returns:
            tuple: (前缀, 实体, 后缀, 完整上下文)
        """
        if context_window is None:
            context_window = self.context_window

        start_pos = entity['start_clean']
        end_pos = entity['end_clean']
        entity_text = entity['text']

        context_start = max(0, start_pos - context_window)
        context_end = min(len(self.clean_text), end_pos + context_window)
        prefix = self.clean_text[context_start:start_pos]
        suffix = self.clean_text[end_pos:context_end]
        full_context = self.clean_text[context_start:context_end]

        return prefix, entity_text, suffix, full_context

    def add_person_alias(self, aliases, canonical_name):
        """
        添加人物别名映射
        
        Args:
            aliases: 别名列表
            canonical_name: 规范名称
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

    def get_entity_embedding(self, entity_text, context="", strategy='context', max_length=256):
        """
        获取实体的嵌入向量
        
        Args:
            entity_text: 实体文本
            context: 上下文文本
            strategy: 嵌入策略('entity_only'/'context'/'masked_context'/'weighted')
            max_length: 最大长度
            
        Returns:
            torch.Tensor: 嵌入向量
        """
        if strategy == 'entity_only':
            input_text = entity_text
        elif strategy == 'context':
            input_text = f"{context}" if context else entity_text
        elif strategy == 'masked_context':
            if context and entity_text in context:
                input_text = context.replace(entity_text, f"[MASK]{entity_text}[MASK]", 1)
            else:
                input_text = f"[MASK]{entity_text}[MASK] {context}"
        else:
            input_text = context if context else entity_text

        inputs = self.tokenizer(
            input_text,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=max_length
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

            if strategy == 'weighted' and context:
                last_hidden_states = outputs.last_hidden_state.squeeze(0)

                tokens = self.tokenizer.tokenize(input_text)
                entity_tokens = self.tokenizer.tokenize(entity_text)

                entity_token_ids = []
                for i, token in enumerate(tokens):
                    if any(et in token for et in entity_tokens):
                        entity_token_ids.append(i + 1)

                if entity_token_ids:
                    entity_embeddings = last_hidden_states[entity_token_ids]
                    entity_vector = entity_embeddings.mean(dim=0)
                else:
                    entity_vector = last_hidden_states[0]
            else:
                entity_vector = outputs.last_hidden_state[:, 0, :].squeeze(0)

        return entity_vector.cpu()

    def build_entity_embeddings(self, context_window=None, embedding_strategy='context'):
        """
        构建所有实体的嵌入向量
        
        Args:
            context_window: 上下文窗口大小
            embedding_strategy: 嵌入策略
        """
        if context_window is not None:
            self.context_window = context_window

        for entity_type, entities in self.entities.items():

            if entity_type == 'PER':
                unique_entities = {}
                for entity in entities:
                    canonical_name = self.get_canonical_person_name(entity['text'])
                    if canonical_name not in unique_entities:
                        unique_entities[canonical_name] = entity
                entity_items = list(unique_entities.items())
            else:
                unique_entities = {}
                for entity in entities:
                    if entity['text'] not in unique_entities:
                        unique_entities[entity['text']] = entity
                entity_items = [(k, v) for k, v in unique_entities.items()]

            embeddings = {}
            for i, (entity_name, entity_info) in enumerate(entity_items):
                try:
                    _, _, _, full_context = self.get_entity_context(
                        entity_info, self.context_window
                    )

                    context_str = full_context if full_context.strip() else ""

                    embedding = self.get_entity_embedding(
                        entity_name,
                        context_str,
                        strategy=embedding_strategy
                    )
                    embeddings[entity_name] = embedding

                except Exception as e:
                    continue

            self.entity_embeddings[entity_type] = embeddings

    def calculate_similarity_matrix(self, entity_type1, entity_type2):
        """
        计算两种实体类型之间的相似度矩阵
        
        Args:
            entity_type1: 第一个实体类型
            entity_type2: 第二个实体类型
            
        Returns:
            pd.DataFrame: 相似度矩阵
        """
        try:
            embeddings1 = self.entity_embeddings.get(entity_type1, {})
            embeddings2 = self.entity_embeddings.get(entity_type2, {})

            if not embeddings1 or not embeddings2:
                return pd.DataFrame()

            # Filter out None values
            embeddings1 = {k: v for k, v in embeddings1.items() if v is not None}
            embeddings2 = {k: v for k, v in embeddings2.items() if v is not None}

            if not embeddings1 or not embeddings2:
                return pd.DataFrame()

            entities1 = sorted(embeddings1.keys())
            entities2 = sorted(embeddings2.keys())
            
            # Convert vectors to numpy arrays
            vecs1 = [embeddings1[e].cpu().numpy() if isinstance(embeddings1[e], torch.Tensor) else embeddings1[e] for e in entities1]
            vecs2 = [embeddings2[e].cpu().numpy() if isinstance(embeddings2[e], torch.Tensor) else embeddings2[e] for e in entities2]
            
            vectors1 = np.stack(vecs1)
            vectors2 = np.stack(vecs2)
            
            # Use PyTorch to calculate cosine similarity
            vectors1_tensor = torch.from_numpy(vectors1).float()
            vectors2_tensor = torch.from_numpy(vectors2).float()
            
            # Normalize vectors and calculate similarity matrix
            vectors1_normalized = F.normalize(vectors1_tensor, p=2, dim=1)
            vectors2_normalized = F.normalize(vectors2_tensor, p=2, dim=1)
            similarity_matrix = torch.matmul(vectors1_normalized, vectors2_normalized.t()).cpu().numpy()

            df = pd.DataFrame(
                similarity_matrix,
                index=entities1,
                columns=entities2
            )
            
            return df
        except Exception as e:
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

        similarity_matrix = cosine_similarity(vectors1, vectors2)

        df = pd.DataFrame(
            similarity_matrix,
            index=entities1,
            columns=entities2
        )

        return df

    def analyze_all_similarities(self, context_window=50, embedding_strategy='masked_context'):
        """
        Analyze semantic similarity between all entity type pairs
        
        Args:
            context_window: Context window size
            embedding_strategy: Embedding strategy
            
        Returns:
            dict: Dictionary of similarity matrices
        """
        try:
            self.build_entity_embeddings(context_window, embedding_strategy)

            try:
                self.similarity_matrices['PER-OFI'] = self.calculate_similarity_matrix('PER', 'OFI')
            except Exception as e:
                pass
            
            try:
                self.similarity_matrices['PER-LOC'] = self.calculate_similarity_matrix('PER', 'LOC')
            except Exception as e:
                pass
            
            try:
                self.similarity_matrices['PER-TIME'] = self.calculate_similarity_matrix('PER', 'TIME')
            except Exception as e:
                pass
            
            try:
                self.similarity_matrices['LOC-OFI'] = self.calculate_similarity_matrix('LOC', 'OFI')
            except Exception as e:
                pass

            return self.similarity_matrices
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise

    def get_top_similarities(self, matrix_name, top_n=10, threshold=0.3):
        """
        获取相似度矩阵中的前N个最相似的对
        
        Args:
            matrix_name: 矩阵名称
            top_n: 返回数量
            threshold: 相似度阈值
            
        Returns:
            list: 相似度对列表
        """
        if matrix_name not in self.similarity_matrices:
            return []

        matrix = self.similarity_matrices[matrix_name]

        if matrix.empty:
            return []

        results = []
        for i, row_name in enumerate(matrix.index):
            for j, col_name in enumerate(matrix.columns):
                similarity = matrix.iloc[i, j]
                if similarity >= threshold:
                    results.append({
                        'entity1': row_name,
                        'entity2': col_name,
                        'similarity': float(similarity),
                        'type': matrix_name
                    })

        results.sort(key=lambda x: x['similarity'], reverse=True)

        return results[:top_n]


