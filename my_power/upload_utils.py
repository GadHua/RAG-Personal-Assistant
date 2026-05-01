# upload_utils.py
import os
import json
import hashlib
from tenacity import retry, stop_after_attempt, wait_fixed

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

NOTES_DIR = "./my_notes"
FINGERPRINT_FILE = "./indexed_files.json"

def get_file_hash(filepath):
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

# 带重试的文档添加函数
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
def add_docs_with_retry(vectorstore, chunks):
    vectorstore.add_documents(chunks)

def process_uploaded_files(uploaded_files, vectorstore):
    if not uploaded_files:
        return 0
    os.makedirs(NOTES_DIR, exist_ok=True)
    fingerprints = load_fingerprints()
    processed = 0

    for uploaded_file in uploaded_files:
        file_path = os.path.join(NOTES_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        file_hash = get_file_hash(file_path)
        if file_path in fingerprints and fingerprints[file_path] == file_hash:
            continue

        # 如果是更新，先删除旧向量
        if file_path in fingerprints:
            try:
                vectorstore._collection.delete(where={"source": file_path})
            except Exception as e:
                print(f"⚠️ Delete old vectors failed: {e}")

        loader = TextLoader(file_path, autodetect_encoding=True)
        docs = loader.load()
        if not docs:
            continue

        if file_path.endswith(".md"):
            splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
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
                chunk_size=500, chunk_overlap=50,
                separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
            )
            chunks = splitter.split_documents(docs)

        if chunks:
            try:
                add_docs_with_retry(vectorstore, chunks)
                fingerprints[file_path] = file_hash
                processed += 1
            except Exception as e:
                print(f"⚠️ Failed to add documents for {file_path}: {e}")
                # 继续处理其他文件

    save_fingerprints(fingerprints)
    return processed