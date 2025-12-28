# AI写作助手 - 基于强化学习

一个创新的AI写作Web应用，通过**用户反馈的强化学习**机制，不断优化写作效果，最终生成符合用户期待的内容。

## 核心特性

- 每次生成两篇不同风格的文章供用户选择
- 基于用户选择自动学习偏好模式
- 随着使用次数增加，生成质量持续优化
- 使用阿里云DeepSeek-V3模型进行文本生成
- 现代化的前后端分离架构
- 完整的Docker容器化支持

## 技术栈

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: SQLite
- **AI模型**: 阿里云DashScope (DeepSeek-V3)
- **Python**: 3.11+

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **HTTP客户端**: Axios
- **样式**: 原生CSS

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx

## 项目结构

```
aiwriter-rl/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── services/       # 业务逻辑
│   │   │   ├── ai_service.py          # AI模型调用
│   │   │   ├── experience_service.py  # 经验学习
│   │   │   └── writing_service.py     # 写作服务
│   │   ├── database.py     # 数据库配置
│   │   ├── models.py       # 数据模型
│   │   ├── schemas.py      # API数据模型
│   │   └── main.py         # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── services/      # API服务
│   │   ├── types/         # TypeScript类型
│   │   ├── App.tsx        # 主组件
│   │   └── main.tsx       # 入口文件
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml      # Docker编排
├── Makefile               # 便捷命令
└── README.md
```

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- 阿里云DashScope API密钥 ([获取地址](https://dashscope.console.aliyun.com/apiKey))

### 使用Docker部署（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd aiwriter-rl
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，填入您的API密钥
nano .env
```

3. **启动服务**
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

4. **访问应用**
- 前端: http://localhost
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 本地开发

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问: http://localhost:3000

## 使用说明

### 基本流程

1. **输入描述**: 在文本框中输入您想创作的内容描述
   - 例如: "写一篇关于人工智能发展趋势的文章，800字左右"

2. **生成文章**: 点击"生成文章"按钮
   - 系统会并行生成两篇风格略有差异的文章
   - 版本A: 正式、专业风格
   - 版本B: 生动、亲切风格

3. **选择偏好**: 阅读两篇文章后，选择更符合您期待的版本

4. **持续优化**: 系统自动学习您的选择模式
   - 分析您偏好的结构类型
   - 总结您喜欢的语气风格
   - 在下次生成时应用这些经验

5. **查看经验**: 在页面下方查看系统学到的经验总结

### 强化学习机制

应用采用**人工反馈的强化学习**思想：

1. **模式识别**: 分析用户历史选择，识别偏好模式
2. **经验积累**: 将模式转化为可复用的经验知识
3. **置信度评分**: 根据样本数量计算经验的可靠性
4. **指导生成**: 将高置信度经验应用于新的文章生成
5. **持续迭代**: 每次反馈都会更新经验库

## API文档

### 创建写作任务
```http
POST /api/write
Content-Type: application/json

{
  "description": "写作内容描述"
}
```

### 提交用户反馈
```http
POST /api/feedback
Content-Type: application/json

{
  "task_id": 1,
  "selected_article_id": 2
}
```

### 获取经验列表
```http
GET /api/experiences
```

### 健康检查
```http
GET /api/health
```

完整API文档: http://localhost:8000/docs

## 数据库模型

### WritingTask (写作任务)
- 存储用户的写作描述
- 关联生成的文章

### Article (文章)
- 存储生成的文章内容
- 包含风格特征元数据

### UserFeedback (用户反馈)
- 记录用户的选择
- 作为经验学习的数据源

### Experience (经验知识库)
- 存储总结出的偏好模式
- 包含置信度和样本数

## 运维管理

### 使用Makefile

```bash
make help        # 显示帮助
make install     # 安装依赖
make build       # 构建Docker镜像
make up          # 启动服务
make down        # 停止服务
make logs        # 查看日志
make clean       # 清理资源
```

### 数据备份

```bash
# 备份SQLite数据库
docker cp aiwriter-backend:/app/data/aiwriter.db ./backup-$(date +%Y%m%d).db
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 只查看后端日志
docker-compose logs -f backend

# 只查看前端日志
docker-compose logs -f frontend
```

## 配置说明

### 后端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DASHSCOPE_API_KEY | 阿里云API密钥 | 必填 |
| DATABASE_URL | 数据库连接URL | sqlite:///./aiwriter.db |
| DEBUG | 调试模式 | False |

### 前端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| VITE_API_URL | 后端API地址 | /api |

## 性能优化

- 并行生成两篇文章，减少等待时间
- 数据库连接池管理
- 前端静态资源CDN缓存
- Nginx gzip压缩
- Docker多阶段构建减小镜像体积

## 安全考虑

- API密钥通过环境变量管理
- CORS配置限制（生产环境需配置具体域名）
- 输入验证和清理
- SQL注入防护（使用ORM）
- Docker容器隔离

## 常见问题

### Q: 如何获取阿里云API密钥？
A: 访问 https://dashscope.console.aliyun.com/apiKey 登录后即可创建

### Q: 生成文章失败怎么办？
A: 检查：
1. API密钥是否正确配置
2. 后端服务是否正常运行
3. 网络连接是否正常
4. 查看后端日志获取详细错误信息

### Q: 如何重置学习经验？
A: 删除或重命名数据库文件即可：
```bash
docker-compose down
docker volume rm aiwriter-rl_backend-data
docker-compose up -d
```

### Q: 支持其他AI模型吗？
A: 可以修改 `backend/app/services/ai_service.py` 中的模型配置

## 未来规划

- [ ] 支持更多AI模型选择
- [ ] 用户账号系统
- [ ] 文章历史记录管理
- [ ] 导出文章为Markdown/PDF
- [ ] 更细粒度的风格控制
- [ ] A/B测试分析面板
- [ ] 多语言支持

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue。
