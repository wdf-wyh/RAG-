"""
Ollama 配置测试
"""

from config import Config
from vector_store import VectorStore
from rag_assistant import RAGAssistant
import time

def test_ollama_config():
    """测试 Ollama 配置"""
    print("\n" + "="*70)
    print("【步骤1】检查 Ollama 配置")
    print("="*70 + "\n")
    
    print(f"MODEL_PROVIDER: {Config.MODEL_PROVIDER}")
    print(f"OLLAMA_API_URL: {Config.OLLAMA_API_URL}")
    print(f"OLLAMA_MODEL: {Config.OLLAMA_MODEL}\n")
    
    if Config.MODEL_PROVIDER != "ollama":
        print("❌ MODEL_PROVIDER 不是 ollama，请检查 .env 配置")
        return False
    
    return True


def test_ollama_connection():
    """测试 Ollama 连接"""
    print("\n" + "="*70)
    print("【步骤2】检查 Ollama 连接")
    print("="*70 + "\n")
    
    try:
        import requests
        
        print(f"连接到: {Config.OLLAMA_API_URL}/api/tags")
        response = requests.get(f"{Config.OLLAMA_API_URL}/api/tags", timeout=5)
        
        if response.status_code == 200:
            print("✅ Ollama 连接成功\n")
            
            models = response.json().get('models', [])
            print(f"可用模型 ({len(models)} 个):")
            for model in models:
                name = model.get('name', '未知')
                size = model.get('size', 0)
                size_gb = size / (1024**3)
                print(f"  • {name} ({size_gb:.2f} GB)")
            
            # 检查指定的模型是否存在
            model_names = [m.get('name') for m in models]
            if Config.OLLAMA_MODEL in model_names:
                print(f"\n✅ 指定模型 {Config.OLLAMA_MODEL} 已安装")
                return True
            else:
                print(f"\n⚠️  指定模型 {Config.OLLAMA_MODEL} 未安装")
                print(f"   建议使用已安装的模型之一")
                return False
        else:
            print(f"❌ Ollama 返回错误: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 Ollama")
        print("   请确保 Ollama 已启动:")
        print("   运行: ollama serve")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_llm_generation():
    """测试 LLM 生成"""
    print("\n" + "="*70)
    print("【步骤3】测试 LLM 生成")
    print("="*70 + "\n")
    
    try:
        # 直接使用 Ollama
        from langchain_community.llms import Ollama
        
        print(f"初始化 LLM: {Config.OLLAMA_MODEL}")
        llm = Ollama(
            base_url=Config.OLLAMA_API_URL,
            model=Config.OLLAMA_MODEL,
            temperature=Config.TEMPERATURE,
            num_predict=Config.MAX_TOKENS,
        )
        
        print("✅ LLM 初始化成功\n")
        
        print("测试简单生成...")
        print("-" * 70)
        
        start = time.time()
        response = llm.invoke("你好，请简单介绍一下自己")
        elapsed = time.time() - start
        
        content = str(response)
        print(f"{content}\n")
        print(f"⏱️  耗时: {elapsed:.2f}秒")
        print("✅ LLM 生成成功\n")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM 生成失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval():
    """测试检索"""
    print("\n" + "="*70)
    print("【步骤4】测试检索功能")
    print("="*70 + "\n")
    
    try:
        vector_store = VectorStore()
        query = "深度学习的主要架构"
        
        print(f"查询: {query}\n")
        docs = vector_store.similarity_search(query, k=3)
        
        print(f"✅ 找到 {len(docs)} 个文档\n")
        
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:80].replace('\n', ' ')
            source = doc.metadata.get('source', '未知')
            print(f"  [{i}] {source}")
            print(f"      {content}...")
        
        return len(docs) > 0
        
    except Exception as e:
        print(f"❌ 检索失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_complete():
    """测试完整的 RAG 查询"""
    print("\n" + "="*70)
    print("【步骤5】测试完整 RAG 查询")
    print("="*70 + "\n")
    
    try:
        assistant = RAGAssistant()
        query = "深度学习的主要架构有哪些？"
        
        print(f"查询: {query}\n")
        print("处理中...（可能需要一些时间）\n")
        
        start = time.time()
        result = assistant.query(query, return_sources=True, method='vector', k=3)
        elapsed = time.time() - start
        
        print(f"📝 答案:")
        print("-" * 70)
        answer = result.get('answer', '无答案')
        print(answer)
        print()
        
        if 'sources' in result and len(result['sources']) > 0:
            print(f"📚 参考来源 ({len(result['sources'])} 个):")
            print("-" * 70)
            for i, doc in enumerate(result['sources'], 1):
                try:
                    if hasattr(doc, 'page_content'):
                        content = doc.page_content[:100].replace('\n', ' ')
                    else:
                        content = str(doc)[:100]
                    
                    if hasattr(doc, 'metadata'):
                        source = doc.metadata.get('source', '未知')
                    else:
                        source = '未知'
                    
                    print(f"  [{i}] {source}")
                    print(f"      {content}...\n")
                except Exception as e:
                    print(f"  [{i}] 无法展示 ({e})\n")
        
        print(f"⏱️  耗时: {elapsed:.2f}秒")
        print("✅ RAG 查询成功\n")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG 查询失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("Ollama LLM 配置测试")
    print("="*80)
    
    # 测试流程
    tests = [
        ("配置检查", test_ollama_config),
        ("连接检查", test_ollama_connection),
        ("LLM 生成", test_llm_generation),
        ("检索功能", test_retrieval),
        ("完整 RAG", test_rag_complete),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ {name} 异常: {e}")
            results[name] = False
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80 + "\n")
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有测试通过！系统已准备就绪。")
    else:
        print("\n⚠️  某些测试失败，请检查日志。")
        
        if not results.get("连接检查"):
            print("\n【解决方案】")
            print("1. 启动 Ollama 服务:")
            print("   ollama serve")
            print("\n2. 在另一个终端下载模型（如果未安装）:")
            print("   ollama pull gemma2:2b")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
