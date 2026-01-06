"""
古代事件时空聚类分析 - Flask 接口服务
提供RESTful API供用户上传数据集并执行聚类分析
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import json
import io
from werkzeug.utils import secure_filename
import os
import traceback

from clustering_service import ClusteringService
from data_loader import load_all_data_from_strings

app = Flask(__name__)
CORS(app)

# 配置
ALLOWED_EXTENSIONS = {'csv', 'json'}
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化聚类服务
clustering_service = ClusteringService()


def allowed_file(filename):
    """检查文件类型是否被允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'message': '古代事件时空聚类分析服务运行正常'
    }), 200


@app.route('/api/cluster', methods=['POST'])
def perform_clustering():
    """
    执行聚类分析
    
    接收参数：
    - location_csv: 地名数据 CSV 文件或 CSV 字符串
    - events_json: 事件数据 JSON 文件或 JSON 字符串
    
    返回：
    {
        'status': 'success' | 'error',
        'message': 状态消息,
        'data': {
            'clusters': 聚类结果,
            'summary': {
                'total_events': 总事件数,
                'num_clusters': 聚类数,
                'num_noise': 噪声点数,
                'best_params': 最佳参数
            }
        }
    }
    """
    try:
        # 获取上传的文件或字符串数据
        location_data = None
        events_data = None
        
        # 处理 location.csv
        if 'location_csv' in request.files:
            location_file = request.files['location_csv']
            if location_file and allowed_file(location_file.filename):
                location_data = location_file.read().decode('utf-8')
            else:
                return jsonify({
                    'status': 'error',
                    'message': '无效的 location.csv 文件格式'
                }), 400
        elif 'location_csv_string' in request.form:
            location_data = request.form['location_csv_string']
        else:
            return jsonify({
                'status': 'error',
                'message': '缺少地名数据 (location_csv 或 location_csv_string)'
            }), 400
        
        # 处理 events.json
        if 'events_json' in request.files:
            events_file = request.files['events_json']
            if events_file and allowed_file(events_file.filename):
                events_data = events_file.read().decode('utf-8')
            else:
                return jsonify({
                    'status': 'error',
                    'message': '无效的 events.json 文件格式'
                }), 400
        elif 'events_json_string' in request.form:
            events_data = request.form['events_json_string']
        else:
            return jsonify({
                'status': 'error',
                'message': '缺少事件数据 (events_json 或 events_json_string)'
            }), 400
        
        # 执行聚类分析
        result = clustering_service.perform_clustering(location_data, events_data)
        
        return jsonify({
            'status': 'success',
            'message': '聚类分析完成',
            'data': result
        }), 200
        
    except Exception as e:
        error_msg = f'{str(e)}\n{traceback.format_exc()}'
        print(f'错误: {error_msg}')
        return jsonify({
            'status': 'error',
            'message': str(e),
            'details': error_msg
        }), 500


@app.route('/api/cluster/file', methods=['POST'])
def perform_clustering_with_file():
    """
    通过文件上传执行聚类分析 (多部分表单数据)
    
    接收文件：
    - location_file: 地名 CSV 文件
    - events_file: 事件 JSON 文件
    
    返回：聚类结果的 JSON
    """
    try:
        # 验证文件是否存在
        if 'location_file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '缺少地名文件 (location_file)'
            }), 400
        
        if 'events_file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '缺少事件文件 (events_file)'
            }), 400
        
        location_file = request.files['location_file']
        events_file = request.files['events_file']
        
        # 验证文件名
        if location_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '地名文件未选择'
            }), 400
        
        if events_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '事件文件未选择'
            }), 400
        
        # 读取文件内容
        location_data = location_file.read().decode('utf-8')
        events_data = events_file.read().decode('utf-8')
        
        # 执行聚类分析
        result = clustering_service.perform_clustering(location_data, events_data)
        
        return jsonify({
            'status': 'success',
            'message': '聚类分析完成',
            'data': result
        }), 200
        
    except Exception as e:
        error_msg = f'{str(e)}\n{traceback.format_exc()}'
        print(f'错误: {error_msg}')
        return jsonify({
            'status': 'error',
            'message': str(e),
            'details': error_msg
        }), 500








@app.route('/api/info', methods=['GET'])
def get_api_info():
    """
    获取 API 信息和使用说明
    """
    return jsonify({
        'name': '古代事件时空聚类分析服务',
        'version': '2.2',
        'description': '提供RESTful接口用于上传数据集并执行时空聚类分析',
        'endpoints': {
            'POST /api/cluster': {
                'description': '执行聚类分析',
                'parameters': {
                    'location_csv': 'CSV 文件或字符串（包含古代地名、现代地名、纬度、经度）',
                    'events_json': 'JSON 文件或字符串（包含事件数据）'
                }
            },
            'POST /api/cluster/file': {
                'description': '通过文件上传执行聚类分析',
                'parameters': {
                    'location_file': 'CSV 文件',
                    'events_file': 'JSON 文件'
                }
            },
            'GET /api/info': {
                'description': '获取API信息'
            },
            'GET /health': {
                'description': '健康检查'
            }
        }
    }), 200


@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({
        'status': 'error',
        'message': '端点未找到',
        'path': request.path
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    return jsonify({
        'status': 'error',
        'message': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("古代事件时空聚类分析 - Flask 服务")
    print("=" * 60)
    print("\n启动服务中...")
    print("访问 http://localhost:5005/api/info 查看API文档")
    print("\n" + "=" * 60)
    
    # 开发环境设置
    app.run(debug=True, host='0.0.0.0', port=5005)
