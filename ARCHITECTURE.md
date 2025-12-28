# 架构设计文档

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户浏览器                            │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
┌────────────────────▼────────────────────────────────────────┐
│                    Nginx (前端服务)                          │
│  - 静态文件服务                                              │
│  - API反向代理                                               │
│  - Gzip压缩                                                  │
└────────────────────┬────────────────────────────────────────┘
                     │ /api/* → Backend
┌────────────────────▼────────────────────────────────────────┐
│              FastAPI (后端API服务)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API层 (endpoints.py)                                │   │
│  │  - 写作API                                           │   │
│  │  - 反馈API                                           │   │
│  │  - 经验查询API                                       │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  服务层 (services/)                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│  │  │ AI Service   │  │ Experience   │  │  Writing   │ │   │
│  │  │              │  │  Service     │  │  Service   │ │   │
│  │  │ - 调用AI模型 │  │ - 经验学习   │  │ - 业务编排 │ │   │
│  │  │ - 提示词构建 │  │ - 模式识别   │  │            │ │   │
│  │  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │   │
│  └─────────┼──────────────────┼─────────────────┼────────┘   │
│            │                  │                 │            │
│  ┌─────────▼──────────────────▼─────────────────▼────────┐   │
│  │  数据层 (models.py)                                   │   │
│  │  - WritingTask                                        │   │
│  │  - Article                                            │   │
│  │  - UserFeedback                                       │   │
│  │  - Experience                                         │   │
│  └────────────┬──────────────────────────────────────────┘   │
└───────────────┼──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│              SQLite 数据库                                    │
│  - 写作任务表                                                │
│  - 文章表                                                    │
│  - 用户反馈表                                                │
│  - 经验知识库表                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│           阿里云 DashScope API                               │
│           DeepSeek-V3 模型                                   │
└──────────────────────────────────────────────────────────────┘
```

## 核心流程

### 1. 文章生成流程

```
用户输入描述
    ↓
前端发送请求 → POST /api/write
    ↓
WritingService.create_writing_task()
    ↓
    ├─→ 创建WritingTask记录
    │
    ├─→ ExperienceService.get_active_experiences()
    │   └─→ 获取高置信度经验（用于指导生成）
    │
    ├─→ 并行调用AI服务
    │   ├─→ AIService.generate_article(variant="A")
    │   │   ├─→ 构建提示词（包含经验）
    │   │   ├─→ 调用DeepSeek API
    │   │   └─→ 返回正式风格文章
    │   │
    │   └─→ AIService.generate_article(variant="B")
    │       ├─→ 构建提示词（包含经验）
    │       ├─→ 调用DeepSeek API
    │       └─→ 返回生动风格文章
    │
    ├─→ 保存Article记录（A和B）
    │
    └─→ 返回WritingResponse
        └─→ 前端展示两篇文章
```

### 2. 用户反馈与经验学习流程

```
用户选择文章
    ↓
前端发送反馈 → POST /api/feedback
    ↓
创建UserFeedback记录
    ↓
ExperienceService.learn_from_feedback()
    ↓
    ├─→ 标记selected_article.is_selected = True
    │
    ├─→ 收集历史数据
    │   ├─→ 查询所有UserFeedback
    │   ├─→ 获取选中的文章特征
    │   └─→ 获取未选中的文章特征
    │
    ├─→ 分析偏好模式
    │   ├─→ 统计结构类型偏好
    │   │   └─→ 计算置信度 = 选择次数/总次数
    │   │
    │   ├─→ 统计语气风格偏好
    │   │   └─→ 计算置信度
    │   │
    │   └─→ AI总结综合偏好
    │       └─→ AIService.summarize_experience()
    │
    └─→ 更新Experience表
        ├─→ structure_preference
        ├─→ tone_preference
        └─→ general_preference
```

### 3. 经验应用流程

```
下次生成文章时
    ↓
ExperienceService.get_active_experiences()
    ↓
    ├─→ 查询Experience表
    │   └─→ WHERE confidence_score >= 0.5
    │       ORDER BY confidence_score DESC
    │       LIMIT 5
    │
    └─→ 返回preference_summary列表
        ↓
AIService.generate_article()
    ↓
    ├─→ 构建提示词
    │   ├─→ 基础写作要求
    │   ├─→ **用户偏好参考**（经验列表）
    │   └─→ 风格指导
    │
    └─→ 调用DeepSeek生成
        └─→ 模型会参考偏好生成更符合期待的内容
```

## 数据模型详解

### WritingTask (写作任务)
```python
id: int                    # 主键
description: str           # 用户输入的描述
created_at: datetime       # 创建时间
articles: List[Article]    # 关联的文章
feedback: UserFeedback     # 用户反馈
```

### Article (文章)
```python
id: int                    # 主键
task_id: int              # 关联任务
content: str              # 文章内容
variant_type: str         # A或B
structure_type: str       # formal/narrative
tone: str                 # professional/conversational
style_params: str         # JSON格式的风格参数
is_selected: bool         # 是否被选择
created_at: datetime      # 创建时间
```

### UserFeedback (用户反馈)
```python
id: int                         # 主键
task_id: int                   # 关联任务
selected_article_id: int       # 选中的文章
feedback_time: datetime        # 反馈时间
```

### Experience (经验知识库)
```python
id: int                        # 主键
category: str                  # 经验类别
pattern: str                   # 识别的模式
preference_summary: str        # 偏好总结
confidence_score: float        # 置信度 (0-1)
sample_count: int             # 样本数
created_at: datetime          # 创建时间
updated_at: datetime          # 更新时间
metadata: str                 # 额外元数据
```

## 强化学习机制

### 经验类别

1. **structure_preference** (结构偏好)
   - 识别用户偏好的文章结构
   - formal: 总分总、逻辑严谨
   - narrative: 故事化、灵活结构

2. **tone_preference** (语气偏好)
   - 识别用户偏好的语言风格
   - professional: 正式、专业
   - conversational: 亲切、生动

3. **general_preference** (综合偏好)
   - 使用AI总结的综合偏好描述
   - 更细粒度、更全面

### 置信度计算

```python
confidence = 选择该特征的次数 / 总选择次数

例如：
- 总共选择10次
- 其中7次选择了formal结构
- 则structure_preference的confidence = 0.7
```

### 经验应用策略

1. **阈值过滤**: 只使用置信度 >= 0.5 的经验
2. **排序**: 按置信度降序排列
3. **限量**: 最多使用前5条经验
4. **提示词注入**: 将经验描述加入AI提示词

## 性能优化策略

### 1. 并行生成
- 使用`asyncio.gather()`并行生成A和B两篇文章
- 减少50%的等待时间

### 2. 数据库优化
- 使用索引加速查询
- 连接池管理
- 预加载关联数据

### 3. 前端优化
- 静态资源CDN
- Gzip压缩
- 图片懒加载
- 代码分割

### 4. 缓存策略
- 经验查询结果可缓存
- 静态资源长期缓存

## 可扩展性

### 水平扩展
- 无状态API服务，可部署多实例
- 负载均衡器分发请求
- 数据库可迁移至PostgreSQL/MySQL

### 垂直扩展
- 增加服务器资源
- 调整Worker数量
- 数据库性能调优

### 功能扩展点

1. **多模型支持**
   - 抽象AI接口
   - 实现不同模型的Adapter

2. **用户系统**
   - 添加User表
   - 每个用户独立的经验库

3. **高级分析**
   - 添加Analytics服务
   - 可视化偏好趋势

4. **实时协作**
   - WebSocket支持
   - 多人同时编辑

## 安全性设计

### 1. 认证授权
- API密钥通过环境变量
- 生产环境建议添加JWT认证

### 2. 输入验证
- Pydantic自动验证
- 防XSS/SQL注入

### 3. 限流
- 可添加Rate Limiting
- 防止API滥用

### 4. 数据隔离
- Docker容器隔离
- 数据库访问控制

## 部署架构

### 开发环境
```
Frontend (Vite Dev Server :3000)
    ↓ proxy
Backend (Uvicorn :8000)
    ↓
SQLite (本地文件)
```

### 生产环境
```
                    ┌─→ Frontend Container (Nginx :80)
Load Balancer ──────┤
                    └─→ Backend Container (Gunicorn+Uvicorn :8000)
                            ↓
                        Database (SQLite Volume / PostgreSQL)
```

## 监控与日志

### 日志级别
- ERROR: 错误信息
- WARNING: 警告信息
- INFO: 一般信息
- DEBUG: 调试信息

### 监控指标
- API响应时间
- AI调用成功率
- 用户反馈频率
- 经验库增长
- 系统资源使用

### 建议工具
- 日志: ELK Stack / Loki
- 监控: Prometheus + Grafana
- 追踪: Jaeger / Zipkin
