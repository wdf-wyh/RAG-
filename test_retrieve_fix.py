#!/usr/bin/env python
"""测试 RAG Assistant 的 retrieve_documents 功能是否正确修复"""
import sys
sys.path.insert(0, '/Users/apple/Documents/AI/RAG知识库')

from rag_assistant import RAGAssistant
from langchain_core.documents import Document

# 创建助手
assistant = RAGAssistant()

# 测试 1: retrieve_documents 返回正确的格式
print("=" * 60)
print("测试 1: retrieve_documents 返回格式")
print("=" * 60)

docs = assistant.retrieve_documents('深度学习', k=2)

print(f'\n✅ 检索到 {len(docs)} 个文档\n')
all_valid = True
for i, doc in enumerate(docs):
    is_valid_doc = isinstance(doc, Document)
    has_metadata = hasattr(doc, 'metadata') and isinstance(doc.metadata, dict)
    has_source = has_metadata and 'source' in doc.metadata if has_metadata else False
    
    status = '✅' if (is_valid_doc and has_metadata and has_source) else '❌'
    print(f'{status} 文档 {i+1}:')
    print(f'   类型: {type(doc).__name__}')
    print(f'   是 Document: {is_valid_doc}')
    print(f'   有 metadata: {has_metadata}')
    if has_metadata:
        print(f'   source: {doc.metadata.get("source", "无")}')
    print(f'   内容 (前60字): {doc.page_content[:60]}...\n')
    
    if not (is_valid_doc and has_metadata and has_source):
        all_valid = False

print("=" * 60)
print(f"总体结果: {'✅ 通过' if all_valid else '❌ 失败'}")
print("=" * 60)
