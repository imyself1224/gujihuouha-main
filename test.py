# -*- coding: utf-8 -*-
"""
测试脚本 - 人物画像分析完整示例
"""

import sys
import io
import traceback
from data_loader import load_text_file
from cooccurrence import CooccurrenceAnalyzer
from similarity import ImprovedBertSimilarityAnalyzer

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_analysis(file_path="HanGaozuBenji_simple.txt"):
    """
    测试函数 - 人物画像分析完整工作流
    """
    # 1. 加载数据
    print("=" * 60)
    print("第一步：加载数据")
    print("=" * 60)
    
    try:
        text = load_text_file(file_path)
        print(f"成功加载文本文件，共 {len(text)} 个字符")
    except Exception as e:
        print(f"加载文件失败: {e}")
        return None, None

    # 2. 共现矩阵分析
    print("\n" + "=" * 60)
    print("第二步：共现矩阵分析")
    print("=" * 60)
    
    try:
        coanalyzer = CooccurrenceAnalyzer(window_size=20)
        coanalyzer.extract_entities(text)
        coanalyzer.add_person_alias(['高祖', '季', '刘季'], '刘邦')
        matrices = coanalyzer.analyze_all_cooccurrences()
        
        print("\n共现矩阵分析完成！")
        print(f"分析的矩阵类型: {list(matrices.keys())}")
        
    except Exception as e:
        print(f"共现矩阵分析失败: {e}")
        coanalyzer = None

    # 3. BERT语义相似度分析
    print("\n" + "=" * 60)
    print("第三步：BERT语义相似度分析")
    print("=" * 60)
    
    try:
        analyzer = ImprovedBertSimilarityAnalyzer(
            model_name='./GuWen-Bert',
            device='auto'
        )
        analyzer.extract_entities(text)
        analyzer.add_person_alias(['高祖', '季'], '刘邦')
        
        print("\n开始计算语义相似度...")
        matrices = analyzer.analyze_all_similarities(
            context_window=60, 
            embedding_strategy='entity_only'
        )
        
        print("\n语义相似度分析完成！")
        print(f"分析的矩阵类型: {list(matrices.keys())}")
        
    except Exception as e:
        print(f"语义相似度分析失败: {e}")
        traceback.print_exc()
        analyzer = None

    # 4. 输出结果示例
    print("\n" + "=" * 60)
    print("第四步：输出分析结果")
    print("=" * 60)
    
    if coanalyzer:
        print("\n共现矩阵 - 人物与官职前5个共现:")
        top_cooccs = coanalyzer.get_top_cooccurrences('人物-官职', top_n=5)
        for item in top_cooccs:
            print(f"  {item['entity1']} - {item['entity2']}: {item['count']} 次")

    if analyzer:
        print("\n语义相似度 - 人物与官职前5个相似:")
        top_sims = analyzer.get_top_similarities('人物-官职', top_n=5, threshold=0.0)
        for item in top_sims:
            print(f"  {item['entity1']} - {item['entity2']}: {item['similarity']:.4f}")

    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)

    return coanalyzer, analyzer


if __name__ == "__main__":
    test_analysis()
