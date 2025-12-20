#!/usr/bin/env python
"""测试 API 是否正确返回检索到的文档元数据"""
import requests
import json
import time

def test_api():
    """测试 API query 端点"""
    url = 'http://localhost:8000/api/query'
    
    # 等待 API 启动
    for attempt in range(60):
        try:
            response = requests.get('http://localhost:8000/', timeout=2)
            print("✅ API 已启动")
            break
        except:
            if attempt % 10 == 0:
                print(f"⏳ 等待 API 启动... ({attempt}s)")
            time.sleep(1)
    else:
        print("❌ API 启动超时")
        return False
    
    # 测试查询
    payload = {
        'question': '深度学习的主要架构有哪些？',
        'provider': 'ollama',
        'top_k': 3
    }
    
    print("\n" + "="*60)
    print("发送查询...")
    print("="*60)
    print(f"问题: {payload['question']}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=300)
        elapsed = time.time() - start_time
        
        result = response.json()
        
        print(f"\n✅ 响应成功 (耗时: {elapsed:.1f}秒)")
        print(f"状态码: {response.status_code}\n")
        
        # 检查答案
        answer = result.get('answer', '')
        if answer and answer != '我无法根据现有知识库中的信息回答这个问题':
            print("✅ 有有效答案")
        else:
            print("❌ 无有效答案")
        
        # 检查来源
        sources = result.get('sources', [])
        print(f"\n📚 来源 ({len(sources)} 个):")
        
        all_valid = True
        for i, src in enumerate(sources):
            source_name = src.get('source', '未知来源')
            preview = src.get('preview', '')
            
            is_valid = source_name != '未知来源'
            status = '✅' if is_valid else '❌'
            
            print(f"{status} [{i+1}] {source_name}")
            if preview:
                print(f"       {preview[:80]}...")
            
            if not is_valid:
                all_valid = False
        
        print("\n" + "="*60)
        print(f"测试结果: {'✅ 通过' if all_valid else '❌ 失败'}")
        print("="*60)
        
        # 打印完整答案
        if answer:
            print(f"\n📝 完整答案:\n{answer}")
        
        return all_valid
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时 (Ollama 生成可能需要很长时间)")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == '__main__':
    success = test_api()
    exit(0 if success else 1)
