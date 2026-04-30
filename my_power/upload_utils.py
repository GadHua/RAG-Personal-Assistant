# app.py
import os
import json
import hashlib
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

NOTES_DIR = "./my_notes"
FINGERPRINT_FILE = "./indexed_files.json"


def get_file_hash(filepath):
    """计算文件 MD5 哈希"""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def load_fingerprints():
    if os.path.exists(FINGERPRINT_FILE):
        with open(FINGERPRINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_fingerprints(fps):
    with open(FINGERPRINT_FILE, "w", encoding="utf-8") as f:
        json.dump(fps, f, indent=2)


def process_uploaded_files(uploaded_files, vectorstore):
    """处理上传的文件，实现增量索引"""
    if not uploaded_files:
        return

    # 确保 my_notes 目录存在
    os.makedirs(NOTES_DIR, exist_ok=True)
    fingerprints = load_fingerprints()
    processed_count = 0

    for uploaded_file in uploaded_files:
        # 构造保存路径
        file_path = os.path.join(NOTES_DIR, uploaded_file.name)
        # 保存文件到 my_notes
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 计算哈希
        file_hash = get_file_hash(file_path)
        # 检查是否为已索引且未修改的文件
        if file_path in fingerprints and fingerprints[file_path] == file_hash:
            continue  # 无变化，跳过

        # 如果该路径之前已索引（说明是修改），先删除旧向量
        if file_path in fingerprints:
            vectorstore._collection.delete(where={"source": file_path})

        # 加载并分割文档
        loader = TextLoader(file_path, autodetect_encoding=True)
        docs = loader.load()
        if not docs:
            continue

        # 根据文件类型选择分割器
        if file_path.endswith(".md"):
            splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[
                    ("#", "h1"),
                    ("##", "h2"),
                    ("###", "h3"),
                ],
                strip_headers=False
            )
            chunks = []
            for doc in docs:
                md_chunks = splitter.split_text(doc.page_content)
                for chunk in md_chunks:
                    chunk.metadata.update(doc.metadata)
                    chunks.append(chunk)
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
            )
            chunks = splitter.split_documents(docs)

        if chunks:
            vectorstore.add_documents(chunks)
            processed_count += 1
            # 更新指纹
            fingerprints[file_path] = file_hash

    save_fingerprints(fingerprints)
    return processed_count