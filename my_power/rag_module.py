# rag_module.py
import os
from typing import List, Optional

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


class RerankRetriever(BaseRetriever):
    """
    用 DashScope gte-rerank 模型对候选文档重排序
    """
    base_retriever: object
    top_n: int = 5

    def _get_relevant_documents(self, query: str) -> List[Document]:
        # 1. 从基础混合检索器获取候选文档（数量可稍大）
        docs = self.base_retriever.invoke(query)

        if not docs:
            return docs

        # 2. 提取文档文本，准备调用重排序 API
        documents_text = [doc.page_content for doc in docs]

        response = TextReRank.call(
            model="gte-rerank",
            query=query,
            documents=documents_text,
            top_n=self.top_n,
            return_documents=True
        )

        # 3. 根据返回的索引构建最终文档列表
        if response.status_code == 200:
            reranked_docs = []
            for item in response.output.results:
                idx = item.index
                if 0 <= idx < len(docs):
                    reranked_docs.append(docs[idx])
            return reranked_docs
        else:
            # 失败时降级，返回混合检索的 Top N
            print(f"⚠️ Rerank API error: {response.message}")
            return docs[:self.top_n]

# ========== 语义缓存类 ==========
class SemanticCache:
    def __init__(self, embeddings, persist_dir: str, threshold: float = 0.95):
        self.embeddings = embeddings
        self.threshold = threshold
        # 使用独立的 collection 名称，与知识库分离
        self.store = Chroma(
            collection_name="qa_cache",
            embedding_function=embeddings,
            persist_directory=persist_dir
        )

    def lookup(self, query: str) -> Optional[str]:
        """搜索相似问题，若相似度足够高则返回缓存的答案"""
        results = self.store.similarity_search_with_score(query, k=1)
        if not results:
            return None
        doc, score = results[0]
        # Chroma 返回的是距离（越小越相似），需要转换为相似度
        # 余弦距离与相似度的关系：similarity ≈ 1 - distance (近似)
        similarity = 1 - score
        if similarity >= self.threshold:
            return doc.metadata.get("answer")
        return None

    def add(self, question: str, answer: str):
        """将问答对添加到缓存"""
        self.store.add_texts(
            texts=[question],
            metadatas=[{"answer": answer}]
        )

    def clear(self):
        """清空缓存（可留作界面按钮使用）"""
        self.store._collection.delete(where={})


@st.cache_resource
def load_rag_chain():
    # ========== 1. 向量库与向量检索器 ==========
    embeddings = DashScopeEmbeddings(model="text-embedding-v4")
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    # ========== 2. BM25 关键词检索器 ==========
    all_data = vectorstore._collection.get()
    docs_for_bm25 = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(all_data["documents"], all_data["metadatas"])
    ]
    bm25_retriever = BM25Retriever.from_documents(docs_for_bm25)
    bm25_retriever.k = 10

    # ========== 3. 混合检索器（向量 + BM25）==========
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.6, 0.4]  # 语义检索权重稍高
    )

    # ========== 4. 重排序检索器 ==========
    rerank_retriever = RerankRetriever(
        base_retriever=ensemble_retriever,
        top_n=5
    )

    # ========== 5. MiniMax 大模型 ==========
    llm = MiniMaxChat(
        model="minimax-m2.7",
        minimax_api_key=os.getenv("MINIMAX_API_KEY"),
        minimax_group_id=os.getenv("MINIMAX_GROUP_ID"),
        temperature=0.1,
        max_tokens=1024,
        base_url="https://api.minimaxi.com/v1/text/chatcompletion_v2"
    )

    # ===== 6. 历史感知检索器 =====
    # 用于根据对话历史改写用户问题
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个查询改写助手。你的任务是将用户的问题转化为一个独立、清晰、具体的检索查询语句。

    要求：
    1. 如果聊天历史中有相关信息，请结合历史将问题中的指代（如“它”、“那个”）替换为具体内容，确保查询完全独立。
    2. 如果聊天历史为空或无关，请优化用户的问题：补全缩写、解释模糊词汇、转化为更精准的关键词组合或短句。
    3. 不要回答问题，只输出改写后的查询语句。"""),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(
        llm, rerank_retriever, contextualize_q_prompt
    )

    # ===== 7. 最终回答提示词 =====
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

    # ===== 8. 链构建 =====
    def format_docs(docs):
        formatted = []
        for i, doc in enumerate(docs, start=1):  # 从 1 开始编号
            # 提取文件名（如有）
            source = doc.metadata.get("source", "未知")
            formatted.append(f"[{i}] (来源: {source})\n{doc.page_content}")
        return "\n\n".join(formatted)

    # 先组装 RAG 链（不含历史自动管理）
    rag_chain = (
            RunnablePassthrough.assign(
                context=history_aware_retriever | format_docs
            )
            | qa_prompt
            | llm
    )

    # ===== 9. 包装历史自动管理 =====
    # 使用内存历史，每次 Streamlit 会话独立
    store = {}

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        history = store[session_id]
        # 截断历史，只保留最近 4 条消息（加速）
        MAX_MESSAGES = 4
        if len(history.messages) > MAX_MESSAGES:
            history.messages = history.messages[-MAX_MESSAGES:]
        return history

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",  # 用户输入
        history_messages_key="chat_history",  # 历史占位符的键
        output_messages_key="output",  # 模型的输出会保存为 AI 消息
    )

    # 初始化语义缓存
    cache = SemanticCache(embeddings, persist_dir="./chroma_db")

    return conversational_rag_chain, cache, rerank_retriever, vectorstore