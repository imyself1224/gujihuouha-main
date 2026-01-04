"""
古籍事件关系识别 - 配置文件
包含所有超参数和配置常量
"""

# ============== 模型配置 ==============
# BERT模型路径
BERT_MODEL_PATH = './GuWen-Bert'

# 数据路径
DATA_PATH = './filtered_deduplicated_data.json'
MODEL_SAVE_PATH = './model_best/rbert_model.pth'

# ============== 分词配置 ==============
MAX_LENGTH = 256  # 最大序列长度
PADDING = 'max_length'
TRUNCATION = True

# ============== 训练配置 ==============
LEARNING_RATE = 1e-5
NUM_EPOCHS = 13
BATCH_SIZE = 16
TRAIN_RATIO = 0.7  # 训练集比例

# ============== 模型结构配置 ==============
HIDDEN_SIZE = 768  # BERT隐藏层维度
DROPOUT_RATE = 0.3
LSTM_HIDDEN_SIZE = 256
LSTM_LAYERS = 2
GRU_HIDDEN_SIZE = 256
GRU_LAYERS = 1
CNN_NUM_FILTERS = 256
CNN_KERNEL_SIZES = (2, 3, 4)
GCN_LAYERS = 2

# ============== 设备配置 ==============
USE_CUDA = True

# ============== 特殊标记 ==============
SPECIAL_TOKENS = {
    'additional_special_tokens': ['<e1>', '</e1>', '<e2>', '</e2>']
}

# ============== 模型选择 ==============
# 可选的模型类型: 'RBERT', 'BiLSTM', 'CNN_ATT', 'BiGRU_ATT', 'BiLSTM_ATT', 'EventGraph', 'EM'
MODEL_TYPE = 'EM'  # 使用 GuwenBERT_EM 模型

# ============== Flask 配置 ==============
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5004
FLASK_DEBUG = False

# ============== 是否使用 GPU ==============
# USE_CUDA 已在上面定义，这里只是提醒
