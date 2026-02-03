# ContentHub - 快速启动指南

## 启动服务

### 1. 启动后端服务
```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend
python main.py
```

后端将运行在：http://localhost:8000

### 2. 启动前端服务
```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/frontend
npm run dev
```

前端将运行在：http://localhost:5173

## 访问新功能

### 写作风格管理
直接访问：http://localhost:5173/writing-styles

功能：
- 查看所有写作风格
- 创建新的写作风格
- 编辑现有风格
- 删除自定义风格（系统级不可删除）
- 按名称、代码、类型筛选

### 内容主题管理
直接访问：http://localhost:5173/content-themes

功能：
- 查看所有内容主题
- 创建新的内容主题
- 编辑现有主题
- 删除自定义主题（系统级不可删除）
- 按名称、代码、类型筛选

### 系统配置（快速导航）
直接访问：http://localhost:5173/config

在系统配置页面顶部，有两个快速导航卡片：
- 写作风格管理
- 内容主题管理

## API 文档

### Swagger UI
http://localhost:8000/docs

### ReDoc
http://localhost:8000/redoc

## 测试数据初始化

如果需要创建测试数据：

```bash
cd /Users/Oychao/Documents/Projects/content-hub/src/backend
python init_test_data.py
```

这将创建：
- 3 个系统级写作风格
- 5 个系统级内容主题

## 功能验证清单

### 写作风格管理
- [ ] 页面正常加载
- [ ] 显示现有风格列表
- [ ] 搜索功能正常
- [ ] 创建新风格成功
- [ ] 编辑风格成功
- [ ] 删除自定义风格成功
- [ ] 系统级风格删除按钮禁用
- [ ] 表单验证正常

### 内容主题管理
- [ ] 页面正常加载
- [ ] 显示现有主题列表
- [ ] 搜索功能正常
- [ ] 创建新主题成功
- [ ] 编辑主题成功
- [ ] 删除自定义主题成功
- [ ] 系统级主题删除按钮禁用
- [ ] 表单验证正常

### API 测试
使用 Swagger UI (http://localhost:8000/docs) 测试：

写作风格 API：
- [ ] GET /api/v1/config/writing-styles
- [ ] GET /api/v1/config/writing-styles/{id}
- [ ] POST /api/v1/config/writing-styles
- [ ] PUT /api/v1/config/writing-styles/{id}
- [ ] DELETE /api/v1/config/writing-styles/{id}

内容主题 API：
- [ ] GET /api/v1/config/content-themes
- [ ] GET /api/v1/config/content-themes/{id}
- [ ] POST /api/v1/config/content-themes
- [ ] PUT /api/v1/config/content-themes/{id}
- [ ] DELETE /api/v1/config/content-themes/{id}

## 常见问题

### Q: 页面无法访问
A: 确保后端和前端服务都已启动，检查端口是否被占用

### Q: API 调用失败
A: 检查后端服务是否正常运行，查看浏览器控制台错误信息

### Q: 数据未保存
A: 检查数据库文件权限，确保后端有写入权限

### Q: 系统级数据无法删除
A: 这是正常行为，系统级数据（is_system=True）不允许删除

## 下一步

1. 测试所有功能
2. 创建更多测试数据
3. 根据实际需求调整字段和验证规则
4. 添加更多自定义风格和主题

## 技术支持

如有问题，请查看：
- API 文档：http://localhost:8000/docs
- 实施报告：verify_implementation.md
- 项目文档：CLAUDE.md
