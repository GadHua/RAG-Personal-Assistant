# 📚 个人知识库问答系统

基于 RAG（检索增强生成）技术的个人知识库问答系统，支持上传 Markdown 和TXT 文件，并支持多轮对话，通过语义检索和重排序技术提供准确的问答服务。

## ✨ 功能特性

- 📖 **多格式支持**：支持 `.md` 和 `.txt` 文件格式
- 🔍 **混合检索**：结合向量检索（DashScope）和 BM25 关键词检索
- 🎯 **智能重排序**：使用 DashScope gte-rerank 模型对检索结果重排序
- 💬 **对话记忆**：支持多轮对话上下文理解
- ⚡ **语义缓存**：相似问题自动缓存，提升响应速度
- 📊 **引用溯源**：回答时显示参考来源，便于验证
- 🔄 **增量索引**：智能检测文件变化，避免重复索引

## 🛠️ 技术栈

- **前端框架**：Streamlit
- **LLM**：MiniMax (minimax-m2.7)
- **向量嵌入**：阿里云 DashScope (text-embedding-v4)
- **向量数据库**：ChromaDB
- **检索增强**：LangChain + LangChain Community
- **重排序**：DashScope gte-rerank
- **关键词检索**：BM25 (rank-bm25)

## 📋 前置要求

- Python >= 3.14
- uv（Python 包管理器）
- MiniMax API Key 和 Group ID

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd agent
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置环境变量

复制示例配置文件并填入你的 API 密钥：

```bash
cp my_power/.env.example my_power/.env
```

编辑 `my_power/.env` 文件：

```env
MINIMAX_API_KEY=your_minimax_api_key_here
MINIMAX_GROUP_ID=your_group_id_here
```

> ⚠️ **重要**：不要将 `.env` 文件提交到版本控制系统！

### 4. 运行应用

```bash
uv run streamlit run my_power/app.py
```

应用将在 `http://localhost:8501` 启动。

## 📁 项目结构

```
agent/
├── my_power/              # 主要应用代码
│   ├── app.py            # Streamlit 主应用
│   ├── rag_module.py     # RAG 链核心逻辑
│   ├── upload_utils.py   # 文件上传和处理工具
│   ├── .env              # 环境变量配置（不提交）
│   ├── .env.example      # 环境变量示例模板
│   ├── my_notes/         # 知识库文档目录
│   └── chroma_db/        # 向量数据库（自动生成）
├── pyproject.toml        # 项目依赖配置
├── .gitignore           # Git 忽略规则
└── README.md            # 项目说明文档
```

## 📝 使用说明

1. **上传文档**：在侧边栏点击"选择文件"，上传 `.md` 或 `.txt` 文件
2. **自动索引**：系统会自动处理并索引上传的文件
3. **开始问答**：在聊天框输入问题，系统会基于知识库回答
4. **查看引用**：点击"🔍 查看引用来源"查看回答的参考文档
5. **清空对话**：点击侧边栏"🗑️ 清空对话历史"重置对话

## 🔧 高级配置

### 调整检索参数

在 `rag_module.py` 中可以调整：

- `search_kwargs={"k": 10}` - 初始检索文档数量
- `weights=[0.6, 0.4]` - 向量检索和 BM25 的权重比例
- `top_n=5` - 重排序后返回的文档数量
- `threshold=0.95` - 语义缓存相似度阈值

### 自定义提示词

修改 `rag_module.py` 中的 `qa_prompt` 可以定制助手的回答风格和行为。

## ⚠️ 注意事项

1. **API 密钥安全**：
   - 永远不要将 `.env` 文件提交到 Git
   - 定期更换 API 密钥
   - 使用 `.env.example` 作为模板

2. **向量数据库**：
   - `chroma_db/` 目录包含向量索引，体积较大
   - 可以通过重新运行应用自动重建
   - 建议添加到 `.gitignore`

3. **性能优化**：
   - 首次加载需要下载模型，可能需要一些时间
   - 语义缓存可以显著提升重复问题的响应速度
   - 对话历史限制为最近 4 条消息以优化性能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅供学习和个人使用。

---

**Happy Learning! 🎉**
