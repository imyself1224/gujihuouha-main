"""
古籍事件关系识别 - 数据处理模块
包含数据加载、预处理和数据加载器
"""
import torch
import spacy
import json
from torch.utils.data import TensorDataset, DataLoader


# 加载中文模型
nlp = spacy.load("zh_core_web_sm")


def prepare_data(data, tokenizer, relation_to_id):
    """
    准备训练数据：标记实体、分词、提取标签
    
    Args:
        data: list, 原始数据列表
        tokenizer: 分词器
        relation_to_id: 关系类型到ID的映射
    
    Returns:
        list, 处理后的数据列表
    """
    processed_data = []

    for item in data:
        text = item['text']
        events = item['events']
        relations = item.get('relations', [])

        # 创建事件ID到触发词的映射
        event_id_to_trigger = {event['id']: event['trigger'] for event in events}

        for relation in relations:
            head_event_id = relation['head']
            tail_event_id = relation['tail']
            relation_type = relation['relation_type']

            head_trigger = event_id_to_trigger.get(head_event_id)
            tail_trigger = event_id_to_trigger.get(tail_event_id)

            if head_trigger and tail_trigger:
                # 添加实体标记
                text_with_entities = text

                # 标记头实体
                if head_trigger in text:
                    text_with_entities = text_with_entities.replace(
                        head_trigger, f"<e1>{head_trigger}</e1>", 1
                    )

                # 标记尾实体
                if tail_trigger in text_with_entities:
                    # 找到第一个未标记的尾实体出现位置
                    parts = text_with_entities.split(tail_trigger, 1)
                    if len(parts) == 2:
                        text_with_entities = f"{parts[0]}<e2>{tail_trigger}</e2>{parts[1]}"

                # 分词
                inputs = tokenizer(
                    text_with_entities,
                    padding='max_length',
                    truncation=True,
                    max_length=256,
                    return_tensors='pt'
                )

                # 获取实体位置
                input_ids = inputs['input_ids'][0].tolist()

                try:
                    e1_start = input_ids.index(tokenizer.convert_tokens_to_ids('<e1>')) + 1
                    e1_end = input_ids.index(tokenizer.convert_tokens_to_ids('</e1>'))
                    e2_start = input_ids.index(tokenizer.convert_tokens_to_ids('<e2>')) + 1
                    e2_end = input_ids.index(tokenizer.convert_tokens_to_ids('</e2>'))

                    processed_data.append({
                        'input_ids': inputs['input_ids'].squeeze(0),
                        'attention_mask': inputs['attention_mask'].squeeze(0),
                        'e1_start': e1_start,
                        'e1_end': e1_end,
                        'e2_start': e2_start,
                        'e2_end': e2_end,
                        'label': relation_to_id[relation_type],
                        'original_text': text,
                        'head_trigger': head_trigger,
                        'tail_trigger': tail_trigger,
                        'relation_type': relation_type
                    })

                except ValueError:
                    # 如果找不到实体标记，跳过这个样本
                    continue

    return processed_data


def build_dependency_adj(text, event_spans):
    """
    使用依存句法生成事件邻接矩阵
    
    Args:
        text: str, 原始句子
        event_spans: list of tuples [(start, end), ...] 每个事件触发词token索引范围
    
    Returns:
        torch.Tensor, 邻接矩阵 [num_events, num_events]
    """
    doc = nlp(text)
    num_events = len(event_spans)
    adj = torch.eye(num_events, dtype=torch.float32)

    # 计算事件中心 token 的索引
    event_centers = [int((start + end) / 2) for start, end in event_spans]

    # 将 token 索引映射到事件节点
    token_to_event = {idx: i for i, idx in enumerate(event_centers)}

    # 遍历依存句法关系，若 head 和子节点都对应事件，则连边
    for token in doc:
        if token.i in token_to_event and token.head.i in token_to_event:
            i = token_to_event[token.i]
            j = token_to_event[token.head.i]
            adj[i, j] = 1.0
            adj[j, i] = 1.0  # 无向图

    # 归一化
    row_sum = adj.sum(dim=1, keepdim=True)
    adj = adj / (row_sum + 1e-6)
    return adj


def create_data_loader(data, batch_size=8):
    """
    创建数据加载器
    
    Args:
        data: list, 处理后的数据列表
        batch_size: int, 批次大小
    
    Returns:
        DataLoader, PyTorch数据加载器
    """
    input_ids = torch.stack([item['input_ids'] for item in data])
    attention_mask = torch.stack([item['attention_mask'] for item in data])
    labels = torch.tensor([item['label'] for item in data])

    e1_span_list = []
    e2_span_list = []
    adj_list = []

    for item in data:
        # 构建事件span
        e1_span = torch.tensor([item['e1_start'], item['e1_end']])
        e2_span = torch.tensor([item['e2_start'], item['e2_end']])
        e1_span_list.append(e1_span)
        e2_span_list.append(e2_span)
        
        # 使用 spaCy 构建邻接矩阵
        adj = build_dependency_adj(item['original_text'], [(item['e1_start'], item['e1_end']),
                                                  (item['e2_start'], item['e2_end'])])
        adj_list.append(adj)

    e1_span_tensor = torch.stack(e1_span_list)
    e2_span_tensor = torch.stack(e2_span_list)
    adj_tensor = torch.stack(adj_list)

    e1_start = torch.tensor([item['e1_start'] for item in data])
    e1_end = torch.tensor([item['e1_end'] for item in data])
    e2_start = torch.tensor([item['e2_start'] for item in data])
    e2_end = torch.tensor([item['e2_end'] for item in data])

    dataset = TensorDataset(input_ids, attention_mask, e1_start, e1_end, e2_start, e2_end, adj_tensor, labels)
    return DataLoader(dataset, batch_size=batch_size, shuffle=True)


def load_json_data(file_path):
    """
    加载JSON数据文件
    
    Args:
        file_path: str, 数据文件路径
    
    Returns:
        list, 数据列表
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_relation_types(data):
    """
    从数据中提取所有关系类型
    
    Args:
        data: list, 原始数据列表
    
    Returns:
        dict, relation_to_id 映射
        dict, id_to_relation 映射
    """
    relation_types = set()
    for item in data:
        for relation in item.get('relations', []):
            relation_types.add(relation['relation_type'])

    relation_types = sorted(list(relation_types))
    relation_to_id = {rel: idx for idx, rel in enumerate(relation_types)}
    id_to_relation = {idx: rel for idx, rel in enumerate(relation_types)}

    return relation_to_id, id_to_relation, relation_types
