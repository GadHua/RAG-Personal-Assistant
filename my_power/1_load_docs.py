# 1_load_docs.py
from langchain_community.document_loaders import DirectoryLoader, TextLoader

# 指定你要加载的文件夹和文件类型
loader = DirectoryLoader(
    "./my_notes",              # 你的笔记目录
    glob="**/*.txt",           # 先加载 txt 文件；也可以改成 "**/*.md" 或 "**/*"
    loader_cls=TextLoader,     # 使用基础文本加载器
    loader_kwargs={"encoding": "utf-8"}  # 自动识别编码，防止中文乱码
)

documents = loader.load()

print(f"成功加载 {len(documents)} 个文档")
for i, doc in enumerate(documents[:3]):  # 只打印前3个文档的前100字作为预览
    print(f"\n--- 文档 {i+1} ---")
    print(f"来源: {doc.metadata.get('source')}")
    print(f"内容预览: {doc.page_content[:100]}")