# GC TE Policy 知识库 — 总览

> BCG Global China Travel & Expense Policy (v202212) 研究与学习指南

## 文档信息

| 属性 | 值 |
|------|-----|
| 文档名称 | GC TE Policy |
| 版本 | v202212 (2022年12月) |
| 适用范围 | 中国大陆、香港、台湾 |
| 维护团队 | GFOS T&E |

## 知识库结构

本知识库将 GC TE Policy 拆解为 **12 个章节**、**46 条规则**、**35 个术语**、**76 张闪卡** 和 **10 个情景案例**，覆盖以下六大领域：

### 1. 总则与原则 (General)
- 政策目的与适用范围
- 四大核心原则：合理、审慎、经济、合规
- 员工与 Manager 职责

### 2. 差旅管理 (Travel)
- **航空**：舱位标准、Preferred Airlines、提前预订
- **铁路/地面**：高铁优先、Didi 企业账户
- **酒店**：Nightly Cap 分级、Preferred Partners
- **预订**：Amex GBT / TripSource、Pre-trip Approval

### 3. 费用报销 (Expense)
- Daily Meal Allowance (国内 ¥300/国际 $75)
- Client Entertainment 限额与文件要求
- 不可报销费用清单

### 4. 提交流程 (Submission)
- SAP Concur 四步流程
- 30 天提交时限
- Expense Type 分类

### 5. 合规与审计 (Compliance)
- 三级审批体系
- GFOS Pre-payment Audit
- 违规分级处理

### 6. 中国区特殊规定 (China)
- Fapiao 发票要求
- VAT 处理
- Didi/高德企业账户
- TripSource China 集成

## 推荐学习路径

| 路径 | 适合人群 | 章节 |
|------|---------|------|
| 新员工入门 | 刚加入 BCG | ch01→02→06→10→12 |
| 高频出差顾问 | Consultant/PL | ch03→04→05→07→08→11 |
| 费用审核专员 | GFOS/Finance | ch09→10→11→12 |
| 全面掌握 | 系统学习 | ch01-ch12 顺序 |

## 使用方式

1. **Web 学习中心**：访问 `/kb` 进行交互式学习
2. **API 检索**：`GET /api/kb/search?q=关键词`
3. **PDF 导入**：将原始 PDF 上传至 `/api/kb/upload` 自动更新

## 重要提示

⚠️ 本知识库内容基于 GC TE Policy v202212 结构化整理。**请将原始 PDF 上传至系统以获取完整精确的政策原文**。上传方式：

1. 访问学习中心 → 点击「上传 PDF」
2. 或放置文件至 `knowledge-base/gc-te-policy/source/GC_TE_Policy_v202212.pdf` 后运行 `python scripts/ingest_pdf.py`
