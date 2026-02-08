# 异步内容生成 API

## 概述

ContentHub 异步内容生成 API 允许您通过 RESTful 接口提交和管理异步内容生成任务。

**Base URL**: \`http://localhost:18010/api/v1\`

## 1. 提交异步任务

创建一个新的异步内容生成任务。

**请求**

\`\`\`http
POST /api/v1/content/generate/async
Content-Type: application/json
\`\`\`

**请求体**

\`\`\`json
{
  "account_id": 49,
  "topic": "AI技术发展",
  "keywords": "人工智能,机器学习",
  "priority": 8,
  "auto_approve": true
}
\`\`\`

**响应**

\`\`\`json
{
  "task_id": "task-abc123xyz",
  "status": "pending",
  "message": "任务已成功提交"
}
\`\`\`

## 2. 查询任务状态

**请求**

\`\`\`http
GET /api/v1/content/tasks/{task_id}
\`\`\`

**响应**

\`\`\`json
{
  "task_id": "task-abc123xyz",
  "status": "processing",
  "submitted_at": "2026-02-08T10:30:00Z"
}
\`\`\`

## 3. 列出任务

**请求**

\`\`\`http
GET /api/v1/content/tasks?account_id=49&status=pending&limit=20
\`\`\`

**响应**

\`\`\`json
{
  "total": 150,
  "items": [...]
}
\`\`\`

---

**版本**: 1.0.0
**更新**: 2026-02-08
