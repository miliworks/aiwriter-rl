# Docker镜像拉取问题解决方案

## 问题描述

运行 `docker-compose up -d` 时遇到以下错误：
```
failed to resolve source metadata for docker.io/library/python:3.11-slim:
unexpected status from HEAD request to https://xwx6wxd1.mirror.aliyuncs.com/v2/library/python/manifests/3.11-slim?ns=docker.io: 403 Forbidden
```

这是因为阿里云镜像源访问受限导致的。

## 解决方案

### 方案1: 使用修复脚本（Linux用户推荐）

```bash
# 运行修复脚本
./fix-docker.sh
```

脚本会自动：
1. 配置国内Docker镜像加速器
2. 重启Docker服务
3. 提供手动拉取镜像的命令

### 方案2: 手动配置镜像加速器

#### Linux系统

1. 创建或编辑 `/etc/docker/daemon.json`：
```bash
sudo nano /etc/docker/daemon.json
```

2. 添加以下内容：
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.ccs.tencentyun.com"
  ]
}
```

3. 重启Docker服务：
```bash
sudo systemctl restart docker
# 或
sudo service docker restart
```

4. 验证配置：
```bash
docker info | grep -A 5 "Registry Mirrors"
```

#### macOS系统

1. 打开Docker Desktop
2. 点击右上角设置图标
3. 选择 "Docker Engine"
4. 添加镜像配置：
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```
5. 点击 "Apply & Restart"

#### Windows系统

1. 打开Docker Desktop
2. 点击设置图标
3. 选择 "Docker Engine"
4. 添加镜像配置（同macOS）
5. 点击 "Apply & Restart"

### 方案3: 手动拉取镜像

如果配置镜像加速器后仍有问题，可以手动拉取镜像：

```bash
# 拉取后端镜像
docker pull python:3.11-slim

# 拉取前端镜像
docker pull node:18-alpine
docker pull nginx:alpine

# 然后重新构建
docker-compose build
docker-compose up -d
```

### 方案4: 使用其他镜像源

修改 `backend/Dockerfile`，在FROM语句前添加：

```dockerfile
# 使用中科大镜像源
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim

# 或使用网易镜像源
FROM hub-mirror.c.163.com/library/python:3.11-slim
```

### 方案5: 直接使用官方源（需要稳定网络）

如果您有稳定的国际网络连接，可以直接使用官方Docker Hub：

1. 删除或注释掉 `/etc/docker/daemon.json` 中的镜像加速配置
2. 重启Docker服务
3. 运行 `docker-compose up -d`

## 验证修复

配置完成后，运行以下命令验证：

```bash
# 1. 检查Docker服务状态
docker info

# 2. 测试拉取镜像
docker pull python:3.11-slim

# 3. 如果成功，清理并重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

## 推荐镜像源列表

按稳定性和速度排序：

1. **中国科技大学镜像** ⭐⭐⭐⭐⭐
   - `https://docker.mirrors.ustc.edu.cn`

2. **网易云镜像** ⭐⭐⭐⭐
   - `https://hub-mirror.c.163.com`

3. **腾讯云镜像** ⭐⭐⭐⭐
   - `https://mirror.ccs.tencentyun.com`

4. **华为云镜像** ⭐⭐⭐
   - `https://swr.cn-north-4.myhuaweicloud.com`

5. **阿里云镜像**（需要登录）⭐⭐⭐
   - 访问 https://cr.console.aliyun.com/
   - 获取专属加速地址

## 常见问题

### Q1: 配置后仍然无法拉取镜像？

A: 尝试以下步骤：
1. 检查网络连接
2. 清除Docker缓存：`docker system prune -a`
3. 更换其他镜像源
4. 检查防火墙设置

### Q2: 如何检查当前使用的镜像源？

A: 运行以下命令：
```bash
docker info | grep -A 5 "Registry Mirrors"
```

### Q3: 是否可以同时配置多个镜像源？

A: 可以，Docker会按顺序尝试每个镜像源。

### Q4: macOS/Windows用户如何快速配置？

A:
1. 打开Docker Desktop
2. 设置 -> Docker Engine
3. 粘贴本文提供的JSON配置
4. Apply & Restart

## 后续建议

配置成功后，建议：

1. **定期更新镜像**：
```bash
docker-compose pull
docker-compose up -d
```

2. **清理无用镜像**：
```bash
docker image prune -a
```

3. **监控磁盘空间**：
```bash
docker system df
```

## 联系支持

如果以上方法都无法解决问题，请：
1. 查看完整错误日志：`docker-compose logs`
2. 提交Issue并附上错误信息
3. 检查Docker和docker-compose版本是否过旧

---

**最后更新**: 2025-12-28
