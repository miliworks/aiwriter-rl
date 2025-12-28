# 部署指南

本文档提供详细的部署说明，适用于不同的部署场景。

## 目录

1. [本地开发部署](#本地开发部署)
2. [Docker容器部署](#docker容器部署)
3. [生产环境部署](#生产环境部署)
4. [云平台部署](#云平台部署)
5. [常见问题排查](#常见问题排查)

## 本地开发部署

### 前置要求

- Python 3.11+
- Node.js 18+
- 阿里云DashScope API密钥

### 后端部署

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
# 编辑.env文件，填入API密钥
echo "DASHSCOPE_API_KEY=your_api_key_here" > .env

# 6. 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问:
- API: http://localhost:8000
- 文档: http://localhost:8000/docs

### 前端部署

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 配置环境变量（可选）
cp .env.example .env

# 4. 启动开发服务器
npm run dev
```

访问: http://localhost:3000

## Docker容器部署

### 快速开始

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env文件，填入API密钥

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

访问:
- 前端: http://localhost
- 后端: http://localhost:8000

### 自定义配置

#### 修改端口

编辑 `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 修改前端端口为8080

  backend:
    ports:
      - "9000:8000"  # 修改后端端口为9000
```

#### 使用PostgreSQL

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/aiwriter
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=aiwriter
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

## 生产环境部署

### 使用Nginx反向代理

#### 1. 安装Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 2. 配置Nginx

创建 `/etc/nginx/sites-available/aiwriter`:

```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/aiwriter/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 3. 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/aiwriter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 使用SSL证书（Let's Encrypt）

```bash
# 1. 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 2. 获取证书
sudo certbot --nginx -d your-domain.com

# 3. 自动续期
sudo certbot renew --dry-run
```

### 使用Systemd管理服务

#### 后端服务

创建 `/etc/systemd/system/aiwriter-backend.service`:

```ini
[Unit]
Description=AI Writer Backend Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/aiwriter/backend
Environment="DASHSCOPE_API_KEY=your_api_key"
ExecStart=/var/www/aiwriter/backend/venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    -b 0.0.0.0:8000 \
    app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable aiwriter-backend
sudo systemctl start aiwriter-backend
sudo systemctl status aiwriter-backend
```

### 性能优化配置

#### Gunicorn配置

创建 `gunicorn.conf.py`:

```python
import multiprocessing

# 绑定地址
bind = "0.0.0.0:8000"

# Worker数量
workers = multiprocessing.cpu_count() * 2 + 1

# Worker类型
worker_class = "uvicorn.workers.UvicornWorker"

# 超时设置
timeout = 120
keepalive = 5

# 日志
accesslog = "/var/log/aiwriter/access.log"
errorlog = "/var/log/aiwriter/error.log"
loglevel = "info"

# 优雅重启
graceful_timeout = 30
```

启动:
```bash
gunicorn -c gunicorn.conf.py app.main:app
```

## 云平台部署

### AWS部署

#### 使用AWS ECS + Fargate

1. **构建并推送Docker镜像到ECR**

```bash
# 登录ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# 构建镜像
docker build -t aiwriter-backend ./backend
docker build -t aiwriter-frontend ./frontend

# 标记镜像
docker tag aiwriter-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aiwriter-backend:latest
docker tag aiwriter-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aiwriter-frontend:latest

# 推送镜像
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aiwriter-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aiwriter-frontend:latest
```

2. **创建ECS任务定义和服务**

通过AWS Console或使用Infrastructure as Code工具（如Terraform）。

#### 使用AWS Elastic Beanstalk

```bash
# 初始化EB应用
eb init -p docker aiwriter

# 部署
eb create aiwriter-env
eb deploy
```

### 阿里云部署

#### 使用阿里云容器服务ACK

1. 创建Kubernetes集群
2. 配置kubectl
3. 应用Kubernetes配置

创建 `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiwriter-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aiwriter-backend
  template:
    metadata:
      labels:
        app: aiwriter-backend
    spec:
      containers:
      - name: backend
        image: registry.cn-hangzhou.aliyuncs.com/yournamespace/aiwriter-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: aiwriter-secrets
              key: dashscope-api-key
---
apiVersion: v1
kind: Service
metadata:
  name: aiwriter-backend
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: aiwriter-backend
```

部署:
```bash
kubectl apply -f k8s-deployment.yaml
```

### Google Cloud Platform部署

#### 使用Cloud Run

```bash
# 构建镜像
gcloud builds submit --tag gcr.io/PROJECT_ID/aiwriter-backend ./backend

# 部署
gcloud run deploy aiwriter-backend \
    --image gcr.io/PROJECT_ID/aiwriter-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DASHSCOPE_API_KEY=your_key
```

## 数据库迁移

### 从SQLite迁移到PostgreSQL

1. **导出SQLite数据**

```bash
sqlite3 aiwriter.db .dump > backup.sql
```

2. **转换SQL语法**

```bash
# 使用sed转换
sed -i 's/AUTOINCREMENT/SERIAL/g' backup.sql
sed -i 's/INTEGER PRIMARY KEY/SERIAL PRIMARY KEY/g' backup.sql
```

3. **导入PostgreSQL**

```bash
psql -U user -d aiwriter < backup.sql
```

4. **更新环境变量**

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/aiwriter
```

## 备份与恢复

### 自动备份脚本

创建 `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/aiwriter"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
if [ -f /app/data/aiwriter.db ]; then
    cp /app/data/aiwriter.db $BACKUP_DIR/aiwriter_$DATE.db
fi

# 删除30天前的备份
find $BACKUP_DIR -name "aiwriter_*.db" -mtime +30 -delete

echo "Backup completed: $DATE"
```

添加到crontab:
```bash
# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

### 恢复数据

```bash
# 停止服务
docker-compose down

# 恢复数据库
cp backup.db /path/to/data/aiwriter.db

# 重启服务
docker-compose up -d
```

## 监控配置

### 使用Prometheus + Grafana

#### 1. 添加监控端点

在 `backend/app/main.py` 添加:

```python
from prometheus_client import make_asgi_app

# 添加metrics端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

#### 2. Prometheus配置

`prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'aiwriter'
    static_configs:
      - targets: ['backend:8000']
```

#### 3. 启动监控栈

添加到 `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 常见问题排查

### 后端无法启动

1. 检查Python版本
```bash
python --version  # 应该 >= 3.11
```

2. 检查依赖安装
```bash
pip list
```

3. 查看错误日志
```bash
tail -f /var/log/aiwriter/error.log
```

### API调用失败

1. 检查API密钥
```bash
echo $DASHSCOPE_API_KEY
```

2. 测试API连接
```bash
curl -X POST http://localhost:8000/api/health
```

### 数据库连接问题

1. 检查数据库文件权限
```bash
ls -la aiwriter.db
```

2. 检查数据库连接字符串
```bash
echo $DATABASE_URL
```

### Docker容器问题

1. 查看容器状态
```bash
docker-compose ps
```

2. 查看容器日志
```bash
docker-compose logs backend
```

3. 进入容器调试
```bash
docker-compose exec backend bash
```

### 性能问题

1. 检查资源使用
```bash
docker stats
```

2. 增加Worker数量
```yaml
# docker-compose.yml
environment:
  - WORKERS=4
```

3. 启用缓存
```python
# 在experience_service.py添加缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def get_active_experiences():
    ...
```

## 安全检查清单

- [ ] API密钥通过环境变量管理，不提交到Git
- [ ] 生产环境启用HTTPS
- [ ] 配置CORS白名单
- [ ] 启用Rate Limiting
- [ ] 定期更新依赖包
- [ ] 配置防火墙规则
- [ ] 定期备份数据
- [ ] 监控异常访问
- [ ] 使用强密码
- [ ] 限制数据库访问权限

## 性能优化清单

- [ ] 启用Gzip压缩
- [ ] 配置静态资源缓存
- [ ] 使用CDN加速
- [ ] 数据库索引优化
- [ ] 启用连接池
- [ ] 配置适当的Worker数量
- [ ] 使用负载均衡
- [ ] 监控慢查询
- [ ] 启用异步处理
- [ ] 优化Docker镜像大小

## 更新与回滚

### 更新应用

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建
docker-compose build

# 3. 滚动更新
docker-compose up -d
```

### 回滚

```bash
# 1. 查看镜像历史
docker images

# 2. 回滚到指定版本
docker-compose down
docker tag aiwriter-backend:v1.0 aiwriter-backend:latest
docker-compose up -d
```

## 联系与支持

如遇到部署问题，请：
1. 查看日志文件
2. 检查GitHub Issues
3. 提交新的Issue并附上详细信息
