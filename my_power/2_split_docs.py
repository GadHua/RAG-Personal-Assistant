# 2_split_docs.py
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------- 1. 重新加载文档（与模块1相同）----------
loader = DirectoryLoader(
    "./my_notes",
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"}  # 识别编码，防止中文乱码
)
documents = loader.load()
print(f"加载了 {len(documents)} 个文档，准备分割...")

# ---------- 2. 创建分割器 ----------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # 每块最多500个字符
    chunk_overlap=50,     # 相邻块重叠50字符
    separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]  # 中文友好
)

# ---------- 3. 分割所有文档 ----------
chunks = splitter.split_documents(documents)

print(f"分割完成，共生成 {len(chunks)} 个文本块")

# ---------- 4. 预览前3个块 ----------
for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- 块 {i+1} ---")
    print(f"来源: {chunk.metadata.get('source')}")
    print(f"内容: {chunk.page_content}")