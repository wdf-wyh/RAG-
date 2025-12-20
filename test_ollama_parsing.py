#!/usr/bin/env python
"""测试改进的 Ollama 返回解析逻辑"""
import requests
import json
import time
import sys

def test_query(question, num_tests=3):
    """重复测试同一个查询"""
    url = 'http://localhost:8000/api/query'
    
    payload = {
        'question': question,
        'provider': 'ollama',
        'top_k': 2
    }
    
    print(f"\n{'='*60}")
    print(f"🧪 测试查询: {question}")
    print(f"{'='*60}\n")
    
    successes = 0
    failures = 0
    
    for attempt in range(1, num_tests + 1):
        print(f"【尝试 {attempt}/{num_tests}】")
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            result = response.json()
            
            answer = result.get('answer', '')
            sources = result.get('sources', [])
            
            # 检查答案有效性
            is_valid = (
                answer and 
                answer != '我无法根据现有知识库中的信息回答这个问题' and
                len(answer) > 10
            )
            
            if is_valid:
                print(f"✅ 成功")
                print(f"   答案长度: {len(answer)} 字符")
                print(f"   来源数: {len(sources)}")
                print(f"   答案预览: {answer[:80]}...")
                successes += 1
            else:
                print(f"⚠️ 答案可能无效")
                print(f"   答案: {answer[:100]}")
                failures += 1
            
        except requests.exceptions.Timeout:
            print(f"⏱️ 超时 (Ollama 生成需要时间)")
            failures += 1
        except Exception as e:
            print(f"❌ 错误: {str(e)[:100]}")
            failures += 1
        
        print()
        if attempt < num_tests:
            time.sleep(2)
    
    print(f"{'='*60}")
    print(f"📊 结果统计")
    print(f"{'='*60}")
    print(f"成功: {successes}/{num_tests}")
    print(f"失败: {failures}/{num_tests}")
    print(f"成功率: {100*successes/num_tests:.0f}%")
    print()
    
    return successes == num_tests

def main():
    # 等待 API 启动
    print("⏳ 等待 API 启动...")
    for attempt in range(60):
        try:
            requests.get('http://localhost:8000/', timeout=2)
            print("✅ API 已启动\n")
            break
        except:
            if attempt % 10 == 0 and attempt > 0:
                print(f"   还在等待... ({attempt}s)")
            time.sleep(1)
    else:
        print("❌ API 启动超时")
        return False
    
    # 测试多个查询
    test_queries = [
        "深度学习的主要架构有哪些？",
        "什么是机器学习",
        "Python 数据处理的主要方法有什么",
    ]
    
    all_passed = True
    for question in test_queries:
        if not test_query(question, num_tests=2):
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ 所有测试通过!")
    else:
        print("⚠️ 部分测试失败，但系统仍能运行")
    print(f"{'='*60}\n")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
