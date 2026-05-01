# embed_store.py
import os
import json
import hashlib
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma

# ========== 配置 ==========
NOTES_DIR = "./my_notes"
CHROMA_DIR = "./chroma_db"
FINGERPRINT_FILE = "./indexed_files.json"   # 记录已索引文件及其哈希

# ========== 1. 工具函数 ==========
def get_file_hash(filepath):
    """计算文件的 MD5 哈希，用于判断文件是否变化"""
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        print(f"无法读取 {filepath}: {e}")
        return None

def load_previous_fingerprint():
    """加载之前索引的文件指纹"""
    if os.path.exists(FINGERPRINT_FILE):
        with open(FINGERPRINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_fingerprint(fingerprints):
    """保存当前文件指纹"""
    with open(FINGERPRINT_FILE, "w", encoding="utf-8") as f:
        json.dump(fingerprints, f, indent=2)

def collect_all_files(directory):
    """收集目录下所有 .txt 和 .md 文件的绝对路径"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith((".txt", ".md")):
                files.append(os.path.join(root, filename))
    return files

# ========== 2. 加载并分割新文件/修改的文件 ==========
def process_files(file_paths):
    """
    根据文件列表，加载并按各自格式分割，返回 chunk 列表
    """
    txt_chunks = []
    md_chunks = []

    # 分离文件类型
    txt_files = [f for f in file_paths if f.endswith(".txt")]
    md_files = [f for f in file_paths if f.endswith(".md")]

    # 处理 .txt 文件
    if txt_files:
        # 使用 DirectoryLoader 只加载指定列表（这里直接循环实例化 TextLoader）
        # 更简单：逐个 TextLoader 加载
        txt_docs = []
        for fp in txt_files:
            loader = TextLoader(fp, encoding="utf-8")
            txt_docs.extend(loader.load())
        splitter_txt = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        txt_chunks = splitter_txt.split_documents(txt_docs)

    # 处理 .md 文件
    if md_files:
        md_docs = []
        for fp in md_files:
            loader = TextLoader(fp, encoding="utf-8")
            md_docs.extend(loader.load())
        md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
                ("####", "h4"),
            ],
            strip_headers=False
        )
        for doc in md_docs:
            chunks = md_splitter.split_text(doc.page_content)
            for chunk in chunks:
                chunk.metadata.update(doc.metadata)
                md_chunks.append(chunk)

    return txt_chunks + md_chunks

# ========== 3. 主逻辑：增量更新 ==========
def main():
    # 初始化嵌入模型和向量库
    embeddings = DashScopeEmbeddings(model="text-embedding-v4")

    # 如果向量库还不存在，说明是首次运行，后续会创建
    if not os.path.exists(CHROMA_DIR):
        print("未发现向量库，将执行全量构建...")
        vectorstore = None  # 稍后创建
    else:
        vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings
        )
        print(f"已加载现有向量库，包含 {vectorstore._collection.count()} 个向量")

    # 收集当前知识库中的所有文件
    current_files = collect_all_files(NOTES_DIR)
    current_fingerprints = {}
    for f in current_files:
        current_fingerprints[f] = get_file_hash(f)

    # 加载上次记录的指纹
    previous_fingerprints = load_previous_fingerprint()

    # 比较变化
    new_or_modified_files = []
    for f, h in current_fingerprints.items():
        if f not in previous_fingerprints or previous_fingerprints[f] != h:
            new_or_modified_files.append(f)

    # 处理被删除的文件（从向量库中移除）
    if vectorstore is not None:
        deleted_files = set(previous_fingerprints.keys()) - set(current_fingerprints.keys())
        if deleted_files:
            print(f"检测到 {len(deleted_files)} 个文件已删除，正在从向量库中移除...")
            for del_file in deleted_files:
                # Chroma 支持按元数据删除：source 与文件路径对应
                # 注意：TextLoader 的 metadata 中 source 就是文件绝对路径
                vectorstore._collection.delete(
                    where={"source": del_file}
                )
            print("删除的文件块已清理。")

    # 处理新增和修改的文件
    if new_or_modified_files:
        print(f"检测到 {len(new_or_modified_files)} 个新文件或已修改文件，正在处理...")
        new_chunks = process_files(new_or_modified_files)
        if new_chunks:
            if vectorstore is None:
                # 首次创建
                vectorstore = Chroma.from_documents(
                    documents=new_chunks,
                    embedding=embeddings,
                    persist_directory=CHROMA_DIR
                )
            else:
                # 增量添加
                vectorstore.add_documents(new_chunks)
            print(f"成功添加 {len(new_chunks)} 个新文本块")
        else:
            print("新文件处理后未产生有效文本块")
    else:
        print("所有文件均为最新，无需更新。")

    # 保存当前指纹
    save_fingerprint(current_fingerprints)

    if vectorstore:
        total = vectorstore._collection.count()
        print(f"✅ 向量库更新完毕，当前共 {total} 个向量")
    else:
        print("⚠️ 未创建向量库，请确认 my_notes 目录下有文件。")

if __name__ == "__main__":
    main()