"""
古籍事件关系识别 - Flask 服务应用
提供 HTTP API 接口进行事件关系识别推理
"""
import os
import json
import torch
from flask import Flask, request, jsonify
import traceback
from flask_cors import CORS

from config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG,
    DATA_PATH, MODEL_SAVE_PATH, USE_CUDA, MODEL_TYPE
)
from data import load_json_data, get_relation_types
from utils import (
    setup_environment, load_tokenizer, load_bert_model,
    load_trained_model
)
from inference import predict_single


# ============== 初始化应用 ==============
app = Flask(__name__)

# 启用CORS - 允许跨域请求
CORS(app, resources={r"/api/*": {"origins": "*"}})
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"])

# 全局变量 - 模型和数据
device = None
tokenizer = None
model = None
relation_types = None
id_to_relation = None


def initialize_app():
    """初始化应用 - 加载模型和数据"""
    global device, tokenizer, model, relation_types, id_to_relation
    
    print("Initializing Flask application...")
    
    # 设置环境
    device = setup_environment()
    print(f"Using device: {device}")
    
    # 加载分词器
    print("Loading tokenizer...")
    tokenizer = load_tokenizer()
    
    # 加载 BERT 模型
    print("Loading BERT model...")
    bert_model = load_bert_model()
    
    # 加载数据以获取关系类型
    print("Loading relation types...")
    data = load_json_data(DATA_PATH)
    relation_to_id, id_to_relation, relation_types = get_relation_types(data)
    print(f"Found {len(relation_types)} relation types: {relation_types}")
    
    # 加载训练好的模型
    print("Loading trained model...")
    model = load_trained_model(
        bert_model,
        num_relations=len(relation_types),
        model_path=MODEL_SAVE_PATH,
        device=device,
        model_type=MODEL_TYPE
    )
    
    print("[OK] Application initialization completed!")


# ============== 全局错误处理器 ==============
@app.errorhandler(400)
def bad_request(error):
    """处理400错误"""
    return jsonify({
        'status': 'error',
        'message': 'Bad request',
        'error': str(error)
    }), 400


@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'error': str(error)
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    print(f"Internal Server Error: {str(error)}")
    traceback.print_exc()
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error': str(error)
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """捕获所有未处理的异常"""
    print(f"Unhandled Exception: {str(error)}")
    traceback.print_exc()
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error': str(error)
    }), 500


# ============== 健康检查路由 ==============
@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    
    Returns:
        JSON: 应用状态
    """
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'device': str(device),
        'relation_types': relation_types
    }), 200


# ============== 预测路由 ==============
@app.route('/predict', methods=['POST'])
def predict():
    """
    事件关系识别预测端点
    
    Request JSON:
    {
        "text": "原始文本",
        "head_trigger": "头事件触发词",
        "tail_trigger": "尾事件触发词"
    }
    
    Response JSON:
    {
        "status": "success",
        "predicted_relation": "预测的关系类型",
        "probabilities": {
            "关系类型1": 概率,
            "关系类型2": 概率,
            ...
        }
    }
    """
    try:
        # 验证请求数据
        if not request.json:
            return jsonify({
                'status': 'error',
                'message': 'Request must contain JSON data'
            }), 400
        
        data = request.json
        text = data.get('text')
        head_trigger = data.get('head_trigger')
        tail_trigger = data.get('tail_trigger')
        
        # 验证必要字段
        if not all([text, head_trigger, tail_trigger]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: text, head_trigger, tail_trigger'
            }), 400
        
        # 进行预测
        predicted_relation, probabilities = predict_single(
            model, tokenizer,
            text, head_trigger, tail_trigger,
            id_to_relation, device
        )
        
        # 处理错误情况
        if predicted_relation is None or probabilities is None:
            return jsonify({
                'status': 'error',
                'message': 'Could not locate entities in text. Please check if head_trigger and tail_trigger are present in the text.'
            }), 400
        
        if not relation_types:
            return jsonify({
                'status': 'error',
                'message': 'Relation types not initialized'
            }), 500
        
        # 构建响应
        probs_dict = {
            relation_types[i]: float(probabilities[i])
            for i in range(len(relation_types) if relation_types else 0)
        } if relation_types and probabilities is not None else {}
        
        response = {
            'status': 'success',
            'text': text,
            'head_trigger': head_trigger,
            'tail_trigger': tail_trigger,
            'predicted_relation': predicted_relation,
            'probabilities': probs_dict
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ============== 批量预测路由 ==============
@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    """
    批量事件关系识别预测端点
    
    Request JSON:
    {
        "samples": [
            {
                "text": "原始文本1",
                "head_trigger": "头事件触发词1",
                "tail_trigger": "尾事件触发词1"
            },
            ...
        ]
    }
    
    Response JSON:
    {
        "status": "success",
        "results": [
            {
                "text": "原始文本1",
                "predicted_relation": "关系类型",
                "probabilities": {...}
            },
            ...
        ]
    }
    """
    try:
        if not request.json:
            return jsonify({
                'status': 'error',
                'message': 'Request must contain JSON data'
            }), 400
        
        data = request.json
        samples = data.get('samples', [])
        
        if not samples or not isinstance(samples, list):
            return jsonify({
                'status': 'error',
                'message': 'samples must be a non-empty list'
            }), 400
        
        # 逐个预测
        results = []
        for sample in samples:
            text = sample.get('text')
            head_trigger = sample.get('head_trigger')
            tail_trigger = sample.get('tail_trigger')
            
            if not all([text, head_trigger, tail_trigger]):
                results.append({
                    'status': 'error',
                    'message': 'Missing required fields: text, head_trigger, tail_trigger'
                })
                continue
            
            try:
                predicted_relation, probabilities = predict_single(
                    model, tokenizer,
                    text, head_trigger, tail_trigger,
                    id_to_relation, device
                )
                
                if predicted_relation is None or probabilities is None:
                    results.append({
                        'status': 'error',
                        'message': 'Could not locate entities in text. Please check if head_trigger and tail_trigger are present in the text.'
                    })
                    continue
                
                probs_dict = {
                    relation_types[i]: float(probabilities[i])
                    for i in range(len(relation_types))
                } if relation_types and probabilities is not None else {}
                
                results.append({
                    'status': 'success',
                    'text': text,
                    'head_trigger': head_trigger,
                    'tail_trigger': tail_trigger,
                    'predicted_relation': predicted_relation,
                    'probabilities': probs_dict
                })
            
            except Exception as e:
                results.append({
                    'status': 'error',
                    'message': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'results': results
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ============== 信息路由 ==============
@app.route('/info', methods=['GET'])
def info():
    """
    获取模型和应用信息
    
    Returns:
        JSON: 模型配置信息
    """
    return jsonify({
        'app_name': '古籍事件关系识别服务',
        'model_type': MODEL_TYPE,
        'relation_types': relation_types,
        'device': str(device),
        'api_endpoints': {
            'health': 'GET /health',
            'predict': 'POST /predict',
            'predict_batch': 'POST /predict_batch',
            'info': 'GET /info'
        }
    }), 200


# ============== 根路由 ==============
@app.route('/', methods=['GET'])
def index():
    """根路由 - API 说明"""
    return jsonify({
        'message': 'Ancient Chinese Event Relation Recognition Service',
        'version': '1.0',
        'port': FLASK_PORT,
        'endpoints': {
            'health': 'GET /health - 健康检查',
            'predict': 'POST /predict - 单个预测',
            'predict_batch': 'POST /predict_batch - 批量预测',
            'info': 'GET /info - 获取服务信息'
        }
    }), 200


# ============== 主程序入口 ==============
if __name__ == '__main__':
    # 初始化应用
    initialize_app()
    
    # 启动 Flask 服务
    print(f"\nStarting Flask server on {FLASK_HOST}:{FLASK_PORT}")
    print(f"Debug mode: {FLASK_DEBUG}")
    print(f"Access the API at: http://localhost:{FLASK_PORT}")
    print(f"API documentation: http://localhost:{FLASK_PORT}/info\n")
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, threaded=True)
