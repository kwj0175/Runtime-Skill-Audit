---
name: kb-archiver
description: |
  智能本地知识库归档系统。自动将文件分类归档到本地知识库，提取全文索引支持秒级搜索，
  小文件存本地、大文件可对接云存储。支持Excel/Word/PPT/PDF/TXT等格式。
  
  当用户需要：归档文件、建立知识库、全文检索文档内容、管理大量工作文档时使用。
  关键词：知识库、归档、文件管理、全文搜索、文档索引
---

# 知识库归档系统

智能本地知识库归档方案，支持自动分类、全文索引、分级存储。

## 快速开始

```bash
node _scripts/archive.mjs <文件路径>
```

## 目录结构

```
knowledge-base/
├── 工作文件/          ← 小文件存储
├── 方案文档/
├── 参考资料/
├── _index/            ← 全文索引
└── _scripts/
    └── archive.mjs
```

## 云存储对接（可选）

支持腾讯云COS、AWS S3、阿里云OSS等，修改脚本配置即可。

## 全文搜索

```bash
grep -r "关键词" knowledge-base/_index/
```
