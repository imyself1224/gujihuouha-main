"""
测试脚本 - 验证 Flask API 是否正常工作
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = 'http://localhost:5003'

class Colors:
    """ANSI 颜色代码"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


# ==================== 测试函数 ====================

def test_health_check() -> bool:
    """测试 1: 健康检查"""
    print("\n测试 1: 健康检查")
    print("-" * 50)
    try:
        response = requests.get(f'{BASE_URL}/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"服务状态: {data['message']}")
            return True
        else:
            print_error(f"HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到服务器。请确保 Flask 应用在运行")
        return False
    except Exception as e:
        print_error(f"错误: {str(e)}")
        return False


def test_list_datasets() -> bool:
    """测试 2: 获取数据集列表"""
    print("\n测试 2: 获取数据集列表")
    print("-" * 50)
    try:
        response = requests.get(f'{BASE_URL}/api/datasets', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"总共有 {data['total']} 个数据集")
            print(f"数据集: {', '.join(data['datasets'][:5])}")
            if len(data['datasets']) > 5:
                print(f"... 等共 {len(data['datasets'])} 个")
            return True
        else:
            print_error(f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"错误: {str(e)}")
        return False


def test_query_by_text() -> bool:
    """测试 3: 按文本查询（核心功能）"""
    print("\n测试 3: 按文本查询训练数据（核心功能）")
    print("-" * 50)
    try:
        # 使用数据集中实际存在的文本
        text = "其先刘媪尝息大泽之陂，梦与神遇。是时雷电晦冥，太公往视，则见蛟龙於其上。"
        
        response = requests.post(
            f'{BASE_URL}/api/query-by-text',
            json={
                'text': text,
                'dataset': 'Hangaozubenji'
            },
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 404:
            data = response.json()
            if data.get('found'):
                print_success("找到匹配的训练数据")
                print(f"文本: {data['text']}")
                print(f"事件数: {len(data['event_list'])}")
                
                # 显示返回的事件数据
                if data['event_list']:
                    print(f"\n返回的事件标注数据:")
                    for i, event in enumerate(data['event_list'], 1):
                        print(f"  事件 {i}:")
                        print(f"    - 类型: {event['event_type']}")
                        print(f"    - 触发词: {event['trigger']}")
                        print(f"    - 论元:")
                        for arg in event['arguments']:
                            print(f"        • {arg['role']}: {arg['argument']}")
                
                return True
            else:
                print_info("未找到该文本（文本可能不存在）")
                return True
        else:
            print_error(f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"错误: {str(e)}")
        return False


def test_get_training_data() -> bool:
    """测试 4: 获取分页训练数据"""
    print("\n测试 4: 获取分页训练数据")
    print("-" * 50)
    try:
        response = requests.post(
            f'{BASE_URL}/api/training-data',
            json={
                'dataset': 'Hangaozubenji',
                'limit': 3,
                'offset': 0
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("获取数据成功")
            print(f"数据集: {data['dataset']}")
            print(f"总条数: {data['total']}")
            print(f"本次返回: {data['count']} 条")
            
            if data['data']:
                print(f"\n样例数据:")
                item = data['data'][0]
                print(f"  文本: {item['text'][:50]}...")
                print(f"  事件数: {len(item['event_list'])}")
            return True
        else:
            print_error(f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"错误: {str(e)}")
        return False


def test_get_stats() -> bool:
    """测试 5: 获取数据集统计"""
    print("\n测试 5: 获取数据集统计")
    print("-" * 50)
    try:
        response = requests.get(
            f'{BASE_URL}/api/training-stats/Hangaozubenji',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("获取统计信息成功")
            print(f"总条数: {data['total_items']}")
            print(f"总事件数: {data['total_events']}")
            print(f"平均每条事件数: {data['avg_events_per_item']}")
            print(f"事件类型数: {len(data['event_types'])}")
            
            # 显示前 5 个事件类型
            sorted_types = sorted(
                data['event_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            print(f"\n事件类型分布 (TOP 5):")
            for event_type, count in sorted_types:
                print(f"  - {event_type}: {count}")
            
            return True
        else:
            print_error(f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"错误: {str(e)}")
        return False


# ==================== 主程序 ====================

def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("=" * 50)
    print("汉高祖本纪事件抽取接口 - 测试套件")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health_check),
        ("获取数据集列表", test_list_datasets),
        ("按文本查询（核心）", test_query_by_text),
        ("获取分页数据", test_get_training_data),
        ("获取数据统计", test_get_stats),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"测试异常: {str(e)}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name:20} ... {status}")
    
    print("=" * 50)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 50)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
