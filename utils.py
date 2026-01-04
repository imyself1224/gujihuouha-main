"""
古籍事件关系识别 - 工具模块
包含模型加载、初始化等工具函数
"""
import os
import torch
from transformers import AutoTokenizer, AutoModel

from config import BERT_MODEL_PATH, SPECIAL_TOKENS, MODEL_SAVE_PATH, USE_CUDA, MODEL_TYPE
from models import (
    RBERT, GuwenBERT_BiLSTM, GuwenBERT_CNN_ATT,
    GuwenBERT_BiGRU_ATT, GuwenBERT_BiLSTM_ATT,
    GuwenBERT_EventGraph, GuwenBERT_EM
)


def setup_environment():
    """设置环境变量和获取设备"""
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    device = torch.device('cuda' if USE_CUDA and torch.cuda.is_available() else 'cpu')
    return device


def load_tokenizer():
    """加载分词器"""
    tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_PATH)
    tokenizer.add_special_tokens(SPECIAL_TOKENS)
    return tokenizer


def load_bert_model():
    """加载 BERT 基础模型"""
    bert_model = AutoModel.from_pretrained(BERT_MODEL_PATH)
    tokenizer = load_tokenizer()
    bert_model.resize_token_embeddings(len(tokenizer))
    return bert_model


def create_model(bert_model, num_relations, model_type=MODEL_TYPE):
    """
    创建模型实例
    
    Args:
        bert_model: 预训练BERT模型
        num_relations: 关系类型数
        model_type: 模型类型
    
    Returns:
        创建的模型实例
    """
    model_configs = {
        'RBERT': RBERT,
        'BiLSTM': GuwenBERT_BiLSTM,
        'CNN_ATT': GuwenBERT_CNN_ATT,
        'BiGRU_ATT': GuwenBERT_BiGRU_ATT,
        'BiLSTM_ATT': GuwenBERT_BiLSTM_ATT,
        'EventGraph': GuwenBERT_EventGraph,
        'EM': GuwenBERT_EM
    }

    if model_type not in model_configs:
        raise ValueError(f"Unknown model type: {model_type}. Available: {list(model_configs.keys())}")

    ModelClass = model_configs[model_type]
    return ModelClass(bert_model, num_relations=num_relations)


def load_trained_model(bert_model, num_relations, model_path, device, model_type=MODEL_TYPE):
    """
    加载训练好的模型权重
    
    Args:
        bert_model: BERT基础模型
        num_relations: 关系类型数
        model_path: 模型权重路径
        device: torch.device
        model_type: 模型类型
    
    Returns:
        加载好的模型
    """
    model = create_model(bert_model, num_relations, model_type)
    
    # 加载预训练权重
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        print(f"Loaded model from {model_path}")
    else:
        print(f"Warning: Model file not found at {model_path}, using untrained model")
    
    model.to(device)
    model.eval()
    return model
