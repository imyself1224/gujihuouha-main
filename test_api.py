"""
古籍事件关系识别 Flask API - 简化测试脚本
测试古文例句: "项羽怨怀王不肯令与沛公俱西入关，而北救赵，後天下约。"
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5004"
TEST_TEXT = "项羽怨怀王不肯令与沛公俱西入关，而北救赵，後天下约。"


def main():
    print("\n" + "="*70)
    print("  古籍事件关系识别 API - 快速测试")
    print("="*70)
    print(f"\n📝 测试文本: {TEST_TEXT}")
    print(f"🌐 服务地址: {BASE_URL}")
    
    # 1. 检查服务是否运行
    print("\n[1] 检查服务状态...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ 服务正常运行")
            print(f"  - 设备: {health_data.get('device')}")
            print(f"  - 模型加载: {health_data.get('model_loaded')}")
            print(f"  - 关系类型: {health_data.get('relation_types')}")
        else:
            print(f"✗ 服务异常，状态码: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"✗ 无法连接到服务 {BASE_URL}")
        print("  请先启动 Flask 应用: python app.py")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)
    
    
    # 2. 测试单个预测
    print("\n[2] 测试单个预测接口...")
    
    test_cases = [
        {"head": "令", "tail": "入", "desc": "『令』→『入』关"},
        {"head": "不肯", "tail": "救赵", "desc": "『不肯』→『救赵』"},
        {"head": "怨", "tail": "入", "desc": "『怨』→『入』"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n  测试 {i}: {case['desc']}")
        print(f"    触发词: head='{case['head']}', tail='{case['tail']}'")
        
        payload = {
            "text": TEST_TEXT,
            "head_trigger": case['head'],
            "tail_trigger": case['tail']
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/predict",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                relation = result.get('predicted_relation', 'N/A')
                probs = result.get('probabilities', {})
                
                print(f"    ✓ 预测关系: {relation}")
                for rel_type, prob in probs.items():
                    bar = "█" * int(prob * 15) + "░" * (15 - int(prob * 15))
                    print(f"      {rel_type:8} [{bar}] {prob:.4f}")
            else:
                print(f"    ✗ 请求失败，状态码: {response.status_code}")
                print(f"    {response.text}")
        except Exception as e:
            print(f"    ✗ 错误: {e}")
    
    
    # 3. 测试批量预测
    print("\n[3] 测试批量预测接口...")
    
    batch_payload = {
        "samples": [
            {"text": TEST_TEXT, "head_trigger": "令", "tail_trigger": "入"},
            {"text": TEST_TEXT, "head_trigger": "不肯", "tail_trigger": "救赵"},
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict_batch",
            json=batch_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            results = result.get('results', [])
            print(f"  ✓ 批量预测成功，处理了 {len(results)} 个样本")
            for i, r in enumerate(results, 1):
                if r.get('status') == 'success':
                    print(f"    样本 {i}: {r.get('predicted_relation')}")
                else:
                    print(f"    样本 {i}: 失败 - {r.get('error')}")
        else:
            print(f"  ✗ 请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")
    
    print("\n" + "="*70)
    print("✓ 测试完成")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
