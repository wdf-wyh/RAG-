"""轻量 REST API，包装现有的 RAG 功能，供前端调用"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import traceback

from config import Config
from rag_assistant import RAGAssistant
from document_processor import DocumentProcessor
from vector_store import VectorStore
from ollama_client import generate as ollama_generate, OllamaError


class QueryRequest(BaseModel):
    question: str
    provider: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_api_url: Optional[str] = None


class BuildRequest(BaseModel):
    documents_path: str


app = FastAPI(title="RAG Knowledge API")

# 允许前端跨域访问（开发阶段）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


assistant: RAGAssistant = None


def load_assistant() -> bool:
    global assistant
    try:
        Config.validate()
        if assistant is None:
            vector_store = VectorStore()
            vs = vector_store.load_vectorstore()
            if vs is None:
                return False
            assistant = RAGAssistant(vector_store=vector_store)
            assistant.setup_qa_chain()
        return True
    except Exception as e:
        print("加载助手失败:", e)
        return False


@app.get("/api/status")
def status():
    loaded = load_assistant()
    return {"vector_store_loaded": loaded}


@app.post("/api/build")
def build(req: BuildRequest):
    try:
        # 使用 DocumentProcessor 构建知识库
        processor = DocumentProcessor()
        chunks = processor.process_documents(req.documents_path)
        if not chunks:
            return {"success": False, "message": "未找到可处理的文档"}

        vector_store = VectorStore()
        vector_store.create_vectorstore(chunks)
        # 重新加载 assistant 下次查询可用
        global assistant
        assistant = None
        return {"success": True, "processed_chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def query(req: QueryRequest):
    if not load_assistant():
        raise HTTPException(status_code=500, detail="向量数据库未加载。请先构建或确认数据库目录。")

    # 请求优先使用查询中指定的 provider，否则使用全局配置
    req_provider = (req.provider or Config.MODEL_PROVIDER or '').strip().lower()

    try:
        # 本地 Ollama 分支：仅检索文档并把上下文发给本地 Ollama 模型
        if req_provider == 'ollama':
            try:
                if assistant is None:
                    load_assistant()

                docs = assistant.retrieve_documents(req.question, k=Config.TOP_K)

                contexts = []
                for doc in docs:
                    if hasattr(doc, "page_content"):
                        contexts.append(doc.page_content)
                    elif isinstance(doc, dict):
                        contexts.append(doc.get("page_content") or doc.get("content") or str(doc))
                    else:
                        contexts.append(str(doc))

                context_text = "\n\n".join(contexts)

                prompt = (
                    "请只返回一个 JSON 对象，格式为 {\"answer\": \"...\"}，其中 answer 是一段完整、连贯的中文回答。不要输出其他文本或解释。\n"
                    + f"基于以下上下文回答问题:\n{context_text}\n\n问题: {req.question}\n\n"
                    + "回答示例：{\"answer\": \"这是示例答案\"}\n"
                )

                model_name = req.ollama_model or Config.OLLAMA_MODEL
                api_url = req.ollama_api_url or Config.OLLAMA_API_URL

                ollama_text = ollama_generate(
                    model=model_name,
                    prompt=prompt,
                    max_tokens=Config.MAX_TOKENS,
                    temperature=Config.TEMPERATURE,
                    api_url=api_url,
                )

                sources = []
                for doc in docs:
                    src = getattr(doc, 'metadata', {}).get('source', '未知来源') if hasattr(doc, 'metadata') else (doc.get('metadata', {}).get('source') if isinstance(doc, dict) and doc.get('metadata') else '未知来源')
                    preview = getattr(doc, 'page_content', '')
                    preview = preview[:200].replace('\n', ' ') if preview else ''
                    sources.append({"source": src, "preview": preview})

                return {"question": req.question, "answer": ollama_text, "sources": sources}

            except OllamaError as oe:
                # 本地 Ollama 调用失败，记录并回退到默认 RAGAssistant
                print(f"调用本地 Ollama 失败: {oe}")

        # 默认使用 RAGAssistant（LangChain LLM）生成答案
        result = assistant.query(req.question)
        answer = result.get("answer", "")
        sources = []
        if "sources" in result and result["sources"]:
            for doc in result["sources"]:
                src = doc.metadata.get("source", "未知来源")
                preview = getattr(doc, "page_content", "")
                preview = preview[:200].replace("\n", " ") if preview else ""
                sources.append({"source": src, "preview": preview})

        return {"question": req.question, "answer": answer, "sources": sources}

    except Exception as e:
        # 打印完整 traceback 到服务端日志，便于定位问题
        traceback.print_exc()
        # 如果是网络连接相关的错误，给出更明确的提示
        err_msg = str(e)
        if "Connection" in err_msg or "ConnectionError" in err_msg or "APIConnectionError" in err_msg:
            extra = (
                "可能是模型提供者无法连接。请检查网络、模型提供者配置（MODEL_PROVIDER、OPENAI_API_BASE、OLLAMA_API_URL）\n"
                f"当前 OpenAI API Base: {Config.OPENAI_API_BASE}\n"
                f"当前 Ollama API URL: {Config.OLLAMA_API_URL}\n"
                "如果使用本地 Ollama，请确认 Ollama 服务已启动并监听对应端口（默认 http://localhost:11434）。"
            )
            err_msg = err_msg + "\n" + extra

        raise HTTPException(status_code=500, detail=err_msg)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_api:app", host="0.0.0.0", port=8000, reload=True)
