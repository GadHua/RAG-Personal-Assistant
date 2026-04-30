# 4_rag_chain.py
import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models import MiniMaxChat
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ========== 1. 加载向量库与检索器 ==========
embeddings = DashScopeEmbeddings(model="text-embedding-v4")
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# ========== 2. 初始化 Minimax 模型 ==========
llm = MiniMaxChat(
    model="MiniMax-M2.7",
    minimax_api_key=os.getenv("MINIMAX_API_KEY"),
    minimax_group_id=os.getenv("MINIMAX_GROUP_ID"),
    base_url="https://api.minimaxi.com/v1/text/chatcompletion_v2",
    temperature=0.1,
    max_tokens=1024
)

# ========== 3. 提示词模板 ==========
prompt = ChatPromptTemplate.from_template("""你是一个个人知识库助手，请严格依据以下「已知信息」来回答用户的问题。回答时请尽量引用原文，并在最后列出所有参考来源（文件名）。

如果已知信息不足以回答问题，请明确告知“根据现有知识库，我无法回答这个问题”，不要编造事实。

已知信息：
{context}

用户问题：{input}

请给出清晰、结构化的回答：""")

# ========== 4. 用 LCEL 组装链 ==========
def format_docs(docs):
    """将检索到的文档列表拼成一个上下文字符串"""
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    # 同时传递 context 和 input
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# ========== 5. 测试提问 ==========
if __name__ == "__main__":
    question = "Java 中的多态和重写有什么区别？"
    print(f"提问：{question}\n")

    # LCEL 链调用更简单，直接传字符串
    answer = rag_chain.invoke(question)
    print("回答：")
    print(answer)

    # 如果想看检索到的来源，可以单独调用 retriever
    print("\n--- 检索到的参考片段 ---")
    docs = retriever.get_relevant_documents(question)
    for i, doc in enumerate(docs, 1):
        print(f"{i}. {doc.metadata.get('source')}")
        print(f"   片段: {doc.page_content[:80]}...")