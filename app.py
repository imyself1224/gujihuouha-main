# -*- coding: utf-8 -*-
"""
Flask应用 - 人物画像分析模型服务
监听 5002 端口，接收来自 Spring Boot 的请求
"""

import sys
import io
import json
import traceback
import os
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from data_loader import load_text_file
from cooccurrence import CooccurrenceAnalyzer
from similarity import ImprovedBertSimilarityAnalyzer
from utils import format_text_with_entities

# 设置不缓冲的UTF-8编码输出
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域请求

# 全局分析器
coanalyzer = None
analyzer = None


def analyze_text(text_content, person_aliases=None):
    """
    分析文本的核心函数
    
    Args:
        text_content: 待分析的文本内容
        person_aliases: 人物别名字典，格式 {'别名1': '规范名', '别名2': '规范名'}
        
    Returns:
        dict: 分析结果
    """
    global coanalyzer, analyzer
    
    try:
        result = {
            'success': True,
            'message': 'Analysis successful',
            'data': {}
        }
        
        # 1. Cooccurrence matrix analysis
        coanalyzer = CooccurrenceAnalyzer(window_size=20)
        coanalyzer.extract_entities(text_content)
        
        # 添加人物别名
        if person_aliases:
            for aliases_list, canonical_name in person_aliases.items():
                alias_names = aliases_list.split(',')
                coanalyzer.add_person_alias(alias_names, canonical_name)
        else:
            # 默认别名
            coanalyzer.add_person_alias(['高祖', '季', '刘季'], '刘邦')
        
        matrices = coanalyzer.analyze_all_cooccurrences()
        
        # 获取共现矩阵前10个结果
        top_cooccs = []
        for matrix_type in matrices.keys():
            matrix = matrices[matrix_type]
            if isinstance(matrix, dict) and matrix:
                sorted_items = sorted(matrix.items(), key=lambda x: x[1], reverse=True)[:10]
                for item, score in sorted_items:
                    top_cooccs.append({
                        'entity1': item[0],
                        'entity2': item[1],
                        'cooccurrence': int(score),
                        'type': matrix_type
                    })
        
        # Sort by cooccurrence count in descending order
        top_cooccs.sort(key=lambda x: x['cooccurrence'], reverse=True)
        
        result['data']['cooccurrence'] = {
            'matrix_types': list(matrices.keys()),
            'extracted_entities': {
                'PER': coanalyzer.entities.get('PER', []),
                'LOC': coanalyzer.entities.get('LOC', []),
                'TIME': coanalyzer.entities.get('TIME', []),
                'OFI': coanalyzer.entities.get('OFI', [])
            },
            'top_results': top_cooccs
        }
        
        # 2. BERT semantic similarity analysis
        analyzer = ImprovedBertSimilarityAnalyzer(
            model_name='./GuWen-Bert',
            device='auto'
        )
        analyzer.extract_entities(text_content)
        
        # 添加人物别名
        if person_aliases:
            for aliases_list, canonical_name in person_aliases.items():
                alias_names = aliases_list.split(',')
                analyzer.add_person_alias(alias_names, canonical_name)
        else:
            # 默认别名
            analyzer.add_person_alias(['高祖', '季'], '刘邦')
        
        sim_matrices = analyzer.analyze_all_similarities(
            context_window=60,
            embedding_strategy='entity_only'
        )
        
        # Get top 10 similarity results
        top_sims = []
        for matrix_type in sim_matrices.keys():
            matrix = sim_matrices[matrix_type]
            if isinstance(matrix, pd.DataFrame) and not matrix.empty:
                top_sims.extend(analyzer.get_top_similarities(matrix_type, top_n=10, threshold=0.0))
            elif isinstance(matrix, dict) and matrix:
                sorted_items = sorted(matrix.items(), key=lambda x: x[1], reverse=True)[:10]
                for item, score in sorted_items:
                    top_sims.append({
                        'entity1': item[0],
                        'entity2': item[1],
                        'similarity': float(score),
                        'type': matrix_type
                    })
        
        # Sort by similarity in descending order
        top_sims.sort(key=lambda x: x['similarity'], reverse=True)
        
        result['data']['similarity'] = {
            'matrix_types': list(sim_matrices.keys()),
            'extracted_entities': {
                'PER': analyzer.entities.get('PER', []),
                'LOC': analyzer.entities.get('LOC', []),
                'TIME': analyzer.entities.get('TIME', []),
                'OFI': analyzer.entities.get('OFI', [])
            },
            'top_results': top_sims
        }
        
        return result
        
    except Exception as e:
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Analysis failed: {str(e)}',
            'data': {}
        }


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    分析端点
    接收 POST 请求，包含待分析的文本
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'message': 'Request body missing text field',
                'data': {}
            }), 400
        
        text_content = data.get('text')
        entities = data.get('entities', {})
        person_aliases = data.get('person_aliases', {})
        
        # Convert data format: convert SpringBoot format to model format
        formatted_text = format_text_with_entities(text_content, entities)
        
        # Use converted text for analysis
        text_content = formatted_text
        
        result = analyze_text(text_content, person_aliases)
        
        return jsonify(result)
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Request processing failed: {str(e)}',
            'data': {}
        }), 500


@app.route('/analyze/file', methods=['POST'])
def analyze_file():
    """
    File analysis endpoint
    Receives POST request with file path
    """
    try:
        data = request.get_json()
        
        if not data or 'file_path' not in data:
            return jsonify({
                'success': False,
                'message': 'Request body missing file_path field',
                'data': {}
            }), 400
        
        file_path = data.get('file_path')
        person_aliases = data.get('person_aliases', None)
        
        # Load file content
        try:
            text_content = load_text_file(file_path)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'File loading failed: {str(e)}',
                'data': {}
            }), 400
        
        result = analyze_text(text_content, person_aliases)
        return jsonify(result)
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Request processing failed: {str(e)}',
            'data': {}
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'ok',
        'message': 'Service is running normally'
    })


@app.route('/', methods=['GET'])
def index():
    """
    Home page information
    """
    return jsonify({
        'service': 'Character Portrait Analysis Model',
        'version': '1.0',
        'endpoints': {
            'analyze': {
                'method': 'POST',
                'path': '/analyze',
                'description': 'Analyze text content',
                'body': {
                    'text': 'Text content to analyze',
                    'person_aliases': '(Optional) Person alias dictionary'
                }
            },
            'analyze_file': {
                'method': 'POST',
                'path': '/analyze/file',
                'description': 'Analyze file content',
                'body': {
                    'file_path': 'File path',
                    'person_aliases': '(Optional) Person alias dictionary'
                }
            },
            'health': {
                'method': 'GET',
                'path': '/health',
                'description': 'Health check'
            }
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Character Portrait Analysis Model Service Started")
    print("Listening on port: 5002")
    print("=" * 60)
    
    # Start Flask application
    app.run(host='0.0.0.0', port=5002, debug=False)
