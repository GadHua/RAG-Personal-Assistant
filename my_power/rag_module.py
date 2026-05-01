# rag_module.py
import os
from typing import List, Optional, Dict, Any

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models import MiniMaxChat
from langchain_chroma import Chroma
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.retrievers import BaseRetriever
from dashscope import TextReRank
import streamlit as st


# ========== 重排序检索器（加入重试） ==========
class RerankRetriever(BaseRetriever):
    base_retriever: object
    top_n: int = 5

    def _get_relevant_documents(self, query: str) -> List[Document]:
        docs = self.base_retriever.invoke(query)
        if not docs:
            return docs

        documents_text = [doc.page_content for doc in docs]

        # 对 rerank API 加重试（最多3次，间隔1秒）
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_fixed(1),
            retry=retry_if_exception_type(Exception),
            reraise=False,   # 不抛出异常，返回特殊标记
        )
        def call_rerank():
            response = TextReRank.call(
                model="gte-rerank",
                query=query,
                documents=documents_text,
                top_n=self.top_n,
                return_documents=True
            )
            if response.status_code != 200:
                # 将状态异常也当作需要重试的错误
                raise Exception(f"Rerank API error: {response.message}")
            return response

        try:
            response = call_rerank()
        except Exception as e:
            # 降级：重试全部失败后，直接返回混合检索的前 top_n 个结果
            print(f"⚠️ Rerank failed after retries: {e}")
            return docs[:self.top_n]

        # 正常处理结果
        reranked_docs = []
        for item in response.output.results:
            idx = item.index
            if 0 <= idx < len(docs):
                reranked_docs.append(docs[idx])
        return reranked_docs


# ========== 语义缓存（降级处理） ==========
class SemanticCache:
    def __init__(self, embeddings, persist_dir: str, threshold: float = 0.95):
        self.embeddings = embeddings
        self.threshold = threshold
        self.store = Chroma(
            collection_name="qa_cache",
            embedding_function=embeddings,
            persist_directory=persist_dir
        )

    def lookup(self, query: str) -> Optional[str]:
        try:
            results = self.store.similarity_search_with_score(query, k=1)
            if not results:
                return None
            doc, score = results[0]
            similarity = 1 - score
            if similarity >= self.threshold:
                return doc.metadata.get("answer")
            return None
        except Exception as e:
            # Embedding 调用或 Chroma 查询失败，降级为未命中
            print(f"⚠️ Cache lookup failed: {e}")
            return None

    def add(self, question: str, answer: str):
        try:
            self.store.add_texts(
                texts=[question],
                metadatas=[{"answer": answer}]
            )
        except Exception as e:
            # 添加缓存失败不阻断主流程
            print(f"⚠️ Cache add failed: {e}")

    def clear(self):
        self.store._collection.delete(where={})


# ========== 持久化底层资源 ==========
@st.cache_resource
def get_embeddings():
    return DashScopeEmbeddings(model="text-embedding-v4")

@st.cache_resource
def get_vectorstore(_embeddings):
    persist_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
    os.makedirs(persist_dir, exist_ok=True)
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=_embeddings
    )

@st.cache_resource
def get_bm25_retriever(_vectorstore):
    all_data = _vectorstore._collection.get()
    docs_for_bm25 = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(all_data["documents"], all_data["metadatas"])
    ]
    return BM25Retriever.from_documents(docs_for_bm25)

@st.cache_resource
def get_semantic_cache(_embeddings):
    persist_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
    return SemanticCache(_embeddings, persist_dir=persist_dir)



# ========== 动态构建链 ==========
def build_rag_chain(params: Dict[str, Any]):
    embeddings = get_embeddings()
    vectorstore = get_vectorstore(embeddings)
    bm25_retriever = get_bm25_retriever(vectorstore)

    vector_k = params.get("vector_k", 10)
    bm25_k = params.get("bm25_k", 10)
    ensemble_weights = params.get("ensemble_weights", [0.6, 0.4])
    rerank_top_n = params.get("rerank_top_n", 5)
    temperature = params.get("temperature", 0.1)
    max_tokens = params.get("max_tokens", 1024)

    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": vector_k})
    bm25_retriever.k = bm25_k

    ensemble_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=ensemble_weights
    )
    rerank_retriever = RerankRetriever(
        base_retriever=ensemble_retriever,
        top_n=rerank_top_n
    )

    # MiniMax LLM 设置重试（最多重试2次）
    llm = MiniMaxChat(
        model="minimax-m2.7",
        minimax_api_key=os.getenv("MINIMAX_API_KEY"),
        minimax_group_id=os.getenv("MINIMAX_GROUP_ID"),
        temperature=temperature,
        max_tokens=max_tokens,
        base_url="https://api.minimaxi.com/v1/text/chatcompletion_v2",
        max_retries=2   # 原生支持重试
    )

    # 查询改写提示词
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个查询改写助手。你的任务是将用户的问题转化为一个独立、清晰、具体的检索查询语句。
要求：
1. 如果聊天历史中有相关信息，请结合历史将问题中的指代（如“它”、“那个”）替换为具体内容。
2. 如果聊天历史为空或无关，请优化用户的问题：补全缩写、解释模糊词汇、转化为更精准的关键词组合或短句。
3. 不要回答问题，只输出改写后的查询语句。"""),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(
        llm, rerank_retriever, contextualize_q_prompt
    )

    # 最终回答提示词
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个个人知识库助手。请严格依据以下「已知信息」回答用户问题。
要求：
1. 采用清晰的结构组织回答，优先使用**分点列表**、**表格**或**代码块**（如适用）。
2. 回答中如果直接引用或参考了已知信息中的某一段落，请在对应句末插入引用角标，例如 [1]、[2]。
3. 在回答的最后，列出所有实际使用的参考来源（格式为：[编号] 文件名）。
4. 如果已知信息不足以回答问题，请明确告知“根据现有知识库，我无法回答这个问题”，不要编造事实。"""),
        MessagesPlaceholder("chat_history"),
        ("human", """已知信息：
{context}

用户问题：{input}

请按要求回答："""),
    ])

    def format_docs(docs):
        formatted = []
        for i, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "未知")
            formatted.append(f"[{i}] (来源: {source})\n{doc.page_content}")
        return "\n\n".join(formatted)

    rag_chain = (
        RunnablePassthrough.assign(
            context=history_aware_retriever | format_docs
        )
        | qa_prompt
        | llm
    )

    # 对话历史存储
    global store
    if "store" not in globals():
        store = {}

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        history = store[session_id]
        MAX_MESSAGES = 4
        if len(history.messages) > MAX_MESSAGES:
            history.messages = history.messages[-MAX_MESSAGES:]
        return history

    conversational_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="output",
    )

    return conversational_chain, rerank_retriever