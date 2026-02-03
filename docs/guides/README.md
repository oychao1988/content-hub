# 用户指南

本目录包含面向用户的操作和使用指南。

> **最后更新**: 2026-02-04

---

## 文档列表

| 文档 | 描述 | 目标读者 |
|------|------|---------|
| [quick-start.md](quick-start.md) | Web 应用快速开始指南 | 新成员 |
| [cli-quick-start.md](cli-quick-start.md) | CLI 命令行快速开始指南 | 运维/开发人员 |
| [quick-reference.md](quick-reference.md) | 快速参考手册 | 所有用户 |

---

## 使用指南

### 新成员入门

1. **CLI 用户**：阅读 [cli-quick-start.md](cli-quick-start.md) 快速了解命令行操作
2. **Web 用户**：阅读 [quick-start.md](quick-start.md) 快速了解 Web 界面
3. 查看 [项目主 README](../README.md) 了解完整信息
4. 参考 [架构文档](../architecture/) 了解系统设计

### 常用操作

- **CLI 参考**: [cli-quick-start.md](cli-quick-start.md)
- **快速参考**: [quick-reference.md](quick-reference.md)
- **系统架构**: [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- **技术参考**: [../references/](../references/)

---

## CLI 快速链接

### 核心功能

- **数据库管理**: `contenthub db init`
- **用户管理**: `contenthub users create --username admin --role admin`
- **平台管理**: `contenthub platform create --name "微信" --code weixin`
- **客户管理**: `contenthub customer create --name "测试客户"`
- **账号管理**: `contenthub accounts create --name "测试账号" --customer-id 1 --platform-id 1`

### 查看帮助

```bash
# 查看所有命令
contenthub --help

# 查看模块帮助
contenthub users --help

# 查看命令帮助
contenthub users create --help
```

---

## 维护指南

### 添加新指南

1. 创建新文件：`<功能名>-guide.md`
2. 使用 [templates](../references/TEMPLATES.md) 中的用户指南模板
3. 在上表中添加文档条目

### 指南类型

- `quick-start.md` - 快速开始（固定命名）
- `cli-quick-start.md` - CLI 快速开始（固定命名）
- `user-guide.md` - 用户手册（固定命名）
- `<功能名>-guide.md` - 功能指南

---

**相关文档**:
- [文档分类说明](../references/CATEGORIES.md)
- [文档模板](../references/TEMPLATES.md)
- [CLI 实施总结](../development/CLI-IMPLEMENTATION-SUMMARY.md)
- [CLI 命令参考](../references/CLI-REFERENCE.md)
