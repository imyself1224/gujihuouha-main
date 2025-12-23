# -*- coding: utf-8 -*-
"""
Flask API 测试脚本
测试人物画像分析模型的各个端点
"""

import requests
import json
import sys
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Flask 应用地址
BASE_URL = "http://localhost:5002"


def test_health():
    """测试健康检查端点"""
    print("\n" + "=" * 60)
    print("测试健康检查 GET /health")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"请求失败: {e}")


def test_index():
    """测试首页端点"""
    print("\n" + "=" * 60)
    print("测试首页 GET /")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"服务: {data['service']}")
        print(f"版本: {data['version']}")
        print(f"可用端点:")
        for endpoint, info in data['endpoints'].items():
            print(f"  - {info['method']} {info['path']}: {info['description']}")
    except Exception as e:
        print(f"请求失败: {e}")


def test_analyze_with_text():
    """测试分析文本端点"""
    print("\n" + "=" * 60)
    print("测试分析文本 POST /analyze")
    print("=" * 60)
    
    # 简单的测试文本
    test_text = "{刘邦|PER}为沛{丰邑|LOC}人。{项羽|PER}与{刘邦|PER}争天下。{刘邦|PER}为{沛令|OFI}。"
    
    payload = {
        "text": test_text,
        "person_aliases": {
            "高祖,季,刘季": "刘邦"
        }
    }
    
    print(f"请求数据:")
    print(f"  文本: {test_text}")
    print(f"  人物别名: {payload['person_aliases']}")
    
    try:
        response = requests.post(f"{BASE_URL}/analyze", json=payload)
        print(f"\n状态码: {response.status_code}")
        result = response.json()
        print(f"成功: {result['success']}")
        print(f"信息: {result['message']}")
        if result.get('data'):
            print(f"分析结果:")
            if 'cooccurrence' in result['data']:
                print(f"  共现矩阵类型: {result['data']['cooccurrence']['matrix_types']}")
                print(f"  前5个共现结果:")
                for item in result['data']['cooccurrence']['top_results'][:5]:
                    print(f"    {item['entity1']} - {item['entity2']}: {item['count']} 次")
            if 'similarity' in result['data']:
                print(f"  相似度矩阵类型: {result['data']['similarity']['matrix_types']}")
                print(f"  前5个相似结果:")
                for item in result['data']['similarity']['top_results'][:5]:
                    print(f"    {item['entity1']} - {item['entity2']}: {item['similarity']:.4f}")
    except Exception as e:
        print(f"请求失败: {e}")


def test_analyze_with_file():
    """测试分析文件端点"""
    print("\n" + "=" * 60)
    print("测试分析文件 POST /analyze/file")
    print("=" * 60)
    
    payload = {
        "file_path": "HanGaozuBenji_simple.txt",
        "person_aliases": {
            "高祖,季,刘季": "刘邦"
        }
    }
    
    print(f"请求数据:")
    print(f"  文件路径: {payload['file_path']}")
    print(f"  人物别名: {payload['person_aliases']}")
    
    try:
        response = requests.post(f"{BASE_URL}/analyze/file", json=payload)
        print(f"\n状态码: {response.status_code}")
        result = response.json()
        print(f"成功: {result['success']}")
        print(f"信息: {result['message']}")
        if result.get('data'):
            print(f"分析结果:")
            if 'cooccurrence' in result['data']:
                print(f"  共现矩阵类型: {result['data']['cooccurrence']['matrix_types']}")
                print(f"  前5个共现结果:")
                for item in result['data']['cooccurrence']['top_results'][:5]:
                    print(f"    {item['entity1']} - {item['entity2']}: {item['count']} 次")
            if 'similarity' in result['data']:
                print(f"  相似度矩阵类型: {result['data']['similarity']['matrix_types']}")
                print(f"  前5个相似结果:")
                for item in result['data']['similarity']['top_results'][:5]:
                    print(f"    {item['entity1']} - {item['entity2']}: {item['similarity']:.4f}")
    except Exception as e:
        print(f"请求失败: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("Flask API 测试脚本")
    print("=" * 60)
    
    # 测试各个端点
    test_health()
    test_index()
    test_analyze_with_text()
    # test_analyze_with_file()  # 取消注释以测试文件分析
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
