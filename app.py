"""
Flask 应用 - 汉高祖本纪事件抽取接口
核心功能：接收古文文本，返回对应的训练数据（事件标注）
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from typing import Dict, List, Any, Optional

from config import get_config

# ==================== 初始化 ====================

app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# 启用 CORS，允许来自前端的跨域请求
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})


# ==================== 数据管理模块 ====================

class DatasetManager:
    """数据集管理类 - 负责数据集的加载和查询"""
    
    def __init__(self, datasets_dir: str):
        self.datasets_dir = datasets_dir
        self.cache = {}
    
    def load_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """加载数据集（使用缓存）"""
        if dataset_name in self.cache:
            return self.cache[dataset_name]
        
        file_path = os.path.join(self.datasets_dir, f'{dataset_name}.json')
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cache[dataset_name] = data
                return data
        except Exception as e:
            print(f"Error loading dataset {dataset_name}: {str(e)}")
            return []
    
    def get_available_datasets(self) -> List[str]:
        """获取所有可用数据集"""
        try:
            datasets = [f.replace('.json', '') for f in os.listdir(self.datasets_dir) 
                       if f.endswith('.json')]
            return sorted(datasets)
        except Exception:
            return []
    
    def find_by_text(self, text: str, dataset_name: str) -> Optional[Dict[str, Any]]:
        """按文本查找数据项"""
        data = self.load_dataset(dataset_name)
        for item in data:
            if item.get('text') == text:
                return item
        return None
    
    def get_stats(self, dataset_name: str) -> Dict[str, Any]:
        """获取数据集统计信息"""
        data = self.load_dataset(dataset_name)
        
        if not data:
            return {}
        
        event_types = {}
        total_events = 0
        
        for item in data:
            for event in item.get('event_list', []):
                event_type = event.get('event_type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1
                total_events += 1
        
        return {
            'total_items': len(data),
            'total_events': total_events,
            'event_types': event_types,
            'avg_events_per_item': round(total_events / len(data), 2) if data else 0
        }


# 初始化数据管理器
dataset_manager = DatasetManager(
    os.path.join(os.path.dirname(__file__), 'datasets')
)


# ==================== 响应工具 ====================

def error_response(message: str, status_code: int = 500):
    """返回错误响应"""
    return jsonify({'status': 'error', 'message': message}), status_code


def success_response(data: Dict[str, Any], status_code: int = 200):
    """返回成功响应"""
    return jsonify({'status': 'success', **data}), status_code


# ==================== API 端点 ====================

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return success_response({'message': '服务正常运行'})


@app.route('/api/datasets', methods=['GET'])
def list_datasets():
    """获取所有可用数据集"""
    datasets = dataset_manager.get_available_datasets()
    return success_response({
        'datasets': datasets,
        'total': len(datasets)
    })


@app.route('/api/query-by-text', methods=['POST'])
def query_by_text():
    """
    核心接口：按文本查询训练数据
    
    前端传来古文文本，返回对应的事件标注训练数据
    
    请求示例:
    {
        "text": "其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。",
        "dataset": "Hangaozubenji"  // 可选，默认 Hangaozubenji
    }
    """
    try:
        request_data = request.get_json() or {}
        text = request_data.get('text', '').strip()
        dataset_name = request_data.get('dataset', 'Hangaozubenji')
        
        if not text:
            return error_response('文本不能为空', 400)
        
        result_item = dataset_manager.find_by_text(text, dataset_name)
        
        if result_item:
            return success_response({
                'dataset': dataset_name,
                'found': True,
                'text': result_item.get('text', ''),
                'event_list': result_item.get('event_list', []),
                'message': '找到匹配的训练数据'
            })
        else:
            return error_response(
                f'数据集中未找到该文本',
                404
            )
    
    except Exception as e:
        return error_response(str(e))


@app.route('/api/training-data', methods=['POST'])
def get_training_data():
    """
    获取分页训练数据
    
    请求示例:
    {
        "dataset": "Hangaozubenji",
        "limit": 100,
        "offset": 0
    }
    """
    try:
        request_data = request.get_json() or {}
        
        dataset_name = request_data.get('dataset', 'Hangaozubenji')
        limit = min(int(request_data.get('limit', 100)), 10000)
        offset = max(0, int(request_data.get('offset', 0)))
        
        data = dataset_manager.load_dataset(dataset_name)
        
        if not data:
            return error_response(
                f'数据集 {dataset_name} 不存在或为空',
                404
            )
        
        total = len(data)
        paginated_data = data[offset:offset + limit]
        
        return success_response({
            'dataset': dataset_name,
            'total': total,
            'offset': offset,
            'limit': limit,
            'count': len(paginated_data),
            'data': paginated_data
        })
    
    except Exception as e:
        return error_response(str(e))


@app.route('/api/training-stats/<dataset_name>', methods=['GET'])
def get_training_stats(dataset_name: str):
    """
    获取数据集统计信息
    
    示例: GET /api/training-stats/Hangaozubenji
    """
    try:
        data = dataset_manager.load_dataset(dataset_name)
        
        if not data:
            return error_response(
                f'数据集 {dataset_name} 不存在或为空',
                404
            )
        
        stats = dataset_manager.get_stats(dataset_name)
        return success_response({
            'dataset': dataset_name,
            **stats
        })
    
    except Exception as e:
        return error_response(str(e))


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return error_response('请求的资源不存在', 404)


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return error_response('服务器内部错误', 500)


# ==================== 主程序 ====================

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5003,
        debug=True,
        threaded=True
    )
