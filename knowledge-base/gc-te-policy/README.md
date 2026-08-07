# GC TE Policy 知识库 (v202212)

基于 **BCG Global China Travel & Expense Policy (December 2022)** 构建的结构化研究与学习知识库。

## 知识库架构

```
gc-te-policy/
├── source/                    # 放置原始 PDF
│   └── GC_TE_Policy_v202212.pdf
├── data/
│   ├── index.json             # 总索引与元数据
│   ├── taxonomy.json          # 分类体系
│   ├── chapters/              # 分章节结构化内容
│   ├── glossary.json          # 术语表
│   ├── decision_trees.json    # 决策树（合规判断）
│   ├── flashcards.json        # 闪卡（自测）
│   ├── scenarios.json         # 情景案例
│   └── quick_reference.json   # 速查表
├── docs/                      # Markdown 学习文档
├── scripts/
│   ├── ingest_pdf.py          # PDF → 结构化数据
│   └── build_study_materials.py
└── README.md
```

## 快速开始

### 1. 导入 PDF（首次使用）

将 `GC TE Policy_v202212.pdf` 复制到 `source/` 目录，然后运行：

```bash
cd knowledge-base/gc-te-policy
pip install pymupdf
python scripts/ingest_pdf.py
python scripts/build_study_materials.py
```

### 2. 启动学习界面

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

访问 **http://localhost:8000/kb** 打开 GC TE Policy 学习中心。

### 3. API 端点

| 端点 | 说明 |
|------|------|
| `GET /api/kb/overview` | 知识库概览与统计 |
| `GET /api/kb/chapters` | 全部章节列表 |
| `GET /api/kb/chapters/{id}` | 单章详情 |
| `GET /api/kb/search?q=` | 全文检索 |
| `GET /api/kb/glossary` | 术语表 |
| `GET /api/kb/flashcards` | 闪卡列表 |
| `GET /api/kb/scenarios` | 情景案例 |
| `GET /api/kb/decision-tree/{id}` | 决策树 |
| `GET /api/kb/quick-reference` | 速查表 |
| `POST /api/kb/upload` | 上传 PDF 并重建知识库 |

## 学习路径建议

1. **入门** → 阅读 `docs/00-overview.md`，了解政策适用范围与核心原则
2. **系统学习** → 按 taxonomy 顺序学习各章节（Travel → Expense → Compliance）
3. **实战演练** → 完成 scenarios 情景案例
4. **自测巩固** → 使用 flashcards 闪卡
5. **日常速查** → quick_reference 速查表 + decision_trees 决策树

## 分类体系 (Taxonomy)

| 一级分类 | 二级主题 |
|---------|---------|
| **General** | 适用范围、核心原则、角色职责 |
| **Travel** | 机票、火车、地面交通、酒店 |
| **Expense** | 餐饮、客户招待、会议活动 |
| **Submission** | Concur/Chrome River 提交流程 |
| **Compliance** | 审批、审计、不合规处理 |
| **China-Specific** | 发票、VAT、本地货币、WeChat |
