#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
事件聚类分析集成测试脚本
测试Spring Boot后端与Flask服务的集成
"""

import requests
import json
import sys

# API配置
SPRING_API_URL = "http://localhost:8080/api/analysis/event-cluster/cluster"
FLASK_API_URL = "http://localhost:5005/health"

# 测试数据
LOCATION_DATA = """ancient_name,modern_name,latitude,longitude
长安,西安,34.5,108.9
洛阳,洛阳,34.6,112.4
南京,南京,32.1,118.8
长江,长江,31.5,104.5
黄河,黄河,35.0,108.0"""

EVENTS_DATA = {
    "events": [
        {"id": "1", "year": 200, "location": "长安", "description": "刘邦定鼎长安，建立汉朝"},
        {"id": "2", "year": 201, "location": "长安", "description": "汉初政治稳定"},
        {"id": "3", "year": 190, "location": "洛阳", "description": "东汉迁都洛阳"},
        {"id": "4", "year": 192, "location": "洛阳", "description": "洛阳成为政治中心"},
        {"id": "5", "year": 220, "location": "南京", "description": "三国时期孙权建立东吴"},
        {"id": "6", "year": 221, "location": "南京", "description": "东吴政权稳定"},
        {"id": "7", "year": 1000, "location": "长江", "description": "宋代水运发达"}
    ]
}


def check_flask_service():
    """检查Flask服务是否运行"""
    print("[1] 检查Flask聚类服务...")
    try:
        response = requests.get(FLASK_API_URL, timeout=5)
        if response.status_code == 200:
            print("  ✓ Flask服务正常运行 (http://localhost:5005)")
            return True
        else:
            print("  ✗ Flask服务响应异常")
            return False
    except requests.exceptions.ConnectionError:
        print("  ✗ 无法连接到Flask服务")
        print("    请确保Flask服务运行在 http://localhost:5005")
        return False
    except Exception as e:
        print(f"  ✗ 检查Flask服务时出错: {e}")
        return False


def check_spring_service():
    """检查Spring Boot服务是否运行"""
    print("[2] 检查Spring Boot后端服务...")
    try:
        response = requests.get("http://localhost:8080/api/analysis/event-cluster/health", timeout=5)
        if response.status_code == 200:
            print("  ✓ Spring Boot服务正常运行 (http://localhost:8080)")
            return True
        else:
            print("  ✗ Spring Boot服务响应异常")
            return False
    except requests.exceptions.ConnectionError:
        print("  ✗ 无法连接到Spring Boot服务")
        print("    请确保Spring Boot服务运行在 http://localhost:8080")
        return False
    except Exception as e:
        print(f"  ✗ 检查Spring Boot服务时出错: {e}")
        return False


def test_clustering_api():
    """测试聚类分析API"""
    print("[3] 测试聚类分析API...")
    
    try:
        payload = {
            "locationData": LOCATION_DATA,
            "eventsData": json.dumps(EVENTS_DATA)
        }
        
        print(f"  发送请求到: {SPRING_API_URL}")
        response = requests.post(
            SPRING_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("  ✓ 聚类分析成功")
                
                # 显示结果摘要
                if "data" in result and "summary" in result["data"]:
                    summary = result["data"]["summary"]
                    print(f"    - 总事件数: {summary.get('total_events', 'N/A')}")
                    print(f"    - 聚类数量: {summary.get('num_clusters', 'N/A')}")
                    print(f"    - 噪声点数: {summary.get('num_noise', 'N/A')}")
                    params = summary.get('best_params', {})
                    print(f"    - 最佳参数: eps={params.get('eps')}, min_samples={params.get('min_samples')}")
                
                return True
            else:
                print(f"  ✗ 聚类分析失败: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"  ✗ 服务返回异常状态码: {response.status_code}")
            try:
                print(f"    响应内容: {response.json()}")
            except:
                print(f"    响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("  ✗ 请求超时（可能是数据量过大或服务响应慢）")
        return False
    except requests.exceptions.ConnectionError:
        print("  ✗ 无法连接到Spring Boot服务")
        return False
    except Exception as e:
        print(f"  ✗ 测试聚类API时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_validation():
    """测试数据验证"""
    print("[4] 测试数据验证...")
    
    # 测试空数据
    print("  测试空数据...")
    try:
        response = requests.post(
            SPRING_API_URL,
            json={"locationData": "", "eventsData": ""},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code != 200:
            print("    ✓ 正确拒绝空数据")
        else:
            print("    ✗ 应该拒绝空数据")
    except Exception as e:
        print(f"    ✗ 错误: {e}")
    
    # 测试无效JSON
    print("  测试无效JSON...")
    try:
        response = requests.post(
            SPRING_API_URL,
            json={"locationData": LOCATION_DATA, "eventsData": "invalid json"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code != 200:
            print("    ✓ 正确拒绝无效JSON")
        else:
            print("    ✗ 应该拒绝无效JSON")
    except Exception as e:
        print(f"    ✗ 错误: {e}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("事件聚类分析集成测试")
    print("=" * 60)
    print()
    
    # 检查服务
    flask_ok = check_flask_service()
    print()
    spring_ok = check_spring_service()
    print()
    
    if not (flask_ok and spring_ok):
        print("⚠️  某些服务未运行，请先启动所有服务")
        print()
        print("启动命令:")
        print("  Flask: python app.py (在 model/gujihuouha-scenery-flask 目录)")
        print("  Spring Boot: mvn spring-boot:run")
        sys.exit(1)
    
    # 测试API
    test_data_validation()
    print()
    api_ok = test_clustering_api()
    print()
    
    # 总结
    print("=" * 60)
    if api_ok:
        print("✓ 所有测试通过！系统集成成功")
        print()
        print("下一步:")
        print("  1. 启动Vue前端: cd gujihuohua_vue && npm run serve")
        print("  2. 打开浏览器访问: http://localhost:8081")
        print("  3. 导航到事件分析页面的聚类分析标签")
    else:
        print("✗ 某些测试失败，请检查服务状态和错误信息")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
