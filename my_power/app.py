# app.py
import streamlit as st
import time
import os
from rag_module import load_rag_chain
from upload_utils import process_uploaded_files  # 假设将上述函数放在 upload_utils.py 中

st.set_page_config(page_title="个人知识库问答", page_icon="📚")
st.title("📚 个人知识库问答系统")

# ========== 加载链和所有必需对象 ==========
conversational_rag_chain, cache, retriever, vectorstore = load_rag_chain()

# ========== 侧边栏：文件管理与知识库状态 ==========
with st.sidebar:
    st.header("📁 知识库管理")
    uploaded_files = st.file_uploader(
        "上传 txt / md 文件",
        type=["txt", "md"],
        accept_multiple_files=True,
        help="文件将添加到 my_notes 目录并自动索引"
    )
    if uploaded_files:
        with st.spinner("正在索引文件..."):
            processed = process_uploaded_files(uploaded_files, vectorstore)
        if processed:
            st.success(f"成功处理 {processed} 个文件！")
        else:
            st.info("文件已存在且无变化，无需更新。")

    # 显示现有文件列表
    st.subheader("已索引文件")
    notes_dir = "./my_notes"
    if os.path.exists(notes_dir):
        files = [f for f in os.listdir(notes_dir) if f.endswith((".txt", ".md"))]
        if files:
            for f in files:
                st.write(f"📄 {f}")
        else:
            st.write("暂无文件")
    else:
        st.write("目录不存在")

    st.divider()
    # 可选：清空对话按钮
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# ========== 会话初始化 ==========
if "session_id" not in st.session_state:
    st.session_state.session_id = "user"
if "messages" not in st.session_state:
    st.session_state.messages = []

# ========== 显示历史 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 用户输入 ==========
if prompt := st.chat_input("问我任何关于你知识库的问题"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # 先查缓存
        cached_answer = cache.lookup(prompt)
        if cached_answer:
            # 模拟流式输出
            for i in range(0, len(cached_answer), 2):
                full_response = cached_answer[:i + 2]
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)
            message_placeholder.markdown(cached_answer)
            full_response = cached_answer
        else:
            config = {"configurable": {"session_id": st.session_state.session_id}}
            try:
                for chunk in conversational_rag_chain.stream(
                        {"input": prompt}, config=config
                ):
                    if hasattr(chunk, "content"):
                        full_response += chunk.content
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                if full_response:
                    cache.add(prompt, full_response)
            except Exception as e:
                message_placeholder.error(f"出错了：{e}")
                full_response = "抱歉，处理请求时出现错误。"

        # 展示引用来源（无论缓存与否）
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

    st.session_state.messages.append({"role": "assistant", "content": full_response})