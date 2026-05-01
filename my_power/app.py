# app.py
import streamlit as st
import time
import os
from rag_module import (
    build_rag_chain,
    get_semantic_cache,
    get_embeddings,
    get_vectorstore,
)
from upload_utils import process_uploaded_files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="个人知识库问答", page_icon="📚")
st.title("📚 个人知识库问答系统")

# ========== 侧边栏：参数调节 ==========
with st.sidebar:
    st.header("⚙️ 参数调节")
    vector_k = st.slider("向量检索数量", 3, 20, 10)
    bm25_k = st.slider("BM25 检索数量", 3, 20, 10)
    rerank_top_n = st.slider("重排序保留数量", 2, 10, 5)
    temperature = st.slider("LLM 温度", 0.0, 1.0, 0.1, 0.05)
    cache_threshold = st.slider("缓存相似度阈值", 0.8, 1.0, 0.95, 0.01)
    st.divider()

    st.header("📁 知识库管理")
    uploaded_files = st.file_uploader(
        "上传 txt / md 文件",
        type=["txt", "md"],
        accept_multiple_files=True,
        help="文件将放入 my_notes 并自动索引"
    )
    if uploaded_files:
        embeddings = get_embeddings()
        vectorstore = get_vectorstore(embeddings)
        with st.spinner("正在索引文件..."):
            processed = process_uploaded_files(uploaded_files, vectorstore)
        if processed:
            st.success(f"成功处理 {processed} 个文件！")
        else:
            st.info("文件已存在或无变化。")

    st.subheader("已索引文件")
    notes_dir = os.path.join(os.path.dirname(__file__), "my_notes")
    if os.path.exists(notes_dir):
        files = [f for f in os.listdir(notes_dir) if f.endswith((".txt", ".md"))]
        for f in files:
            st.write(f"📄 {f}")
    st.divider()

    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# ========== 主界面初始化 ==========
if "session_id" not in st.session_state:
    st.session_state.session_id = "user"
if "messages" not in st.session_state:
    st.session_state.messages = []

# 动态构建链
params = {
    "vector_k": vector_k,
    "bm25_k": bm25_k,
    "rerank_top_n": rerank_top_n,
    "temperature": temperature,
    "max_tokens": 1024,
    "ensemble_weights": [0.6, 0.4],
}
conversational_rag_chain, retriever = build_rag_chain(params)

embeddings = get_embeddings()
cache = get_semantic_cache(embeddings)
cache.threshold = cache_threshold

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 用户输入处理 ==========
if prompt := st.chat_input("问我任何关于你知识库的问题"):
    # 保存用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 显示助手回答
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 1. 检查缓存
            cached_answer = cache.lookup(prompt)

            if cached_answer:
                full_response = cached_answer
                token_info = "缓存响应"
            else:
                config = {"configurable": {"session_id": st.session_state.session_id}}
                try:
                    # 非流式调用，一次拿到完整结果（稳定可靠）
                    result = conversational_rag_chain.invoke(
                        {"input": prompt}, config=config
                    )
                    full_response = result.content if hasattr(result, "content") else ""

                    # Token 统计
                    if hasattr(result, "usage_metadata") and result.usage_metadata is not None:
                        token_data = result.usage_metadata
                        input_t = token_data.get("input_tokens", "?")
                        output_t = token_data.get("output_tokens", "?")
                        total_t = token_data.get("total_tokens", "?")
                        token_info = f"输入 {input_t} / 输出 {output_t} / 总计 {total_t}"
                    else:
                        token_info = "Token 信息未获取"

                    # 存入缓存
                    if full_response:
                        cache.add(prompt, full_response)

                except Exception as e:
                    full_response = f"抱歉，处理请求时出现错误：{e}"
                    token_info = "异常中断"

            # 显示回答（一次性）
            st.markdown(full_response)

            # 展示 Token 用量
            st.caption(token_info)

    # 3. 在消息外部展示引用来源
    if full_response and not full_response.startswith("抱歉"):
        with st.expander("🔍 查看引用来源"):
            try:
                docs = retriever.invoke(prompt)
                if docs:
                    for i, doc in enumerate(docs, 1):
                        source = doc.metadata.get("source", "未知")
                        st.markdown(f"**{i}. {source}**")
                        st.text(doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else ""))
                else:
                    st.write("未检索到相关文档")
            except Exception as e:
                st.write(f"来源展示出错：{e}")

    # 保存助手消息
    st.session_state.messages.append({"role": "assistant", "content": full_response})