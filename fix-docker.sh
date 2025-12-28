#!/bin/bash

echo "=== Docker镜像拉取问题修复脚本 ==="
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    DOCKER_CONFIG_DIR="/etc/docker"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS用户请通过Docker Desktop界面配置镜像加速器"
    echo "路径: Docker Desktop -> Preferences -> Docker Engine"
    exit 0
else
    echo "Windows用户请通过Docker Desktop界面配置镜像加速器"
    exit 0
fi

echo "方案1: 配置Docker镜像加速器（推荐）"
echo "----------------------------------------"

# 备份现有配置
if [ -f "$DOCKER_CONFIG_DIR/daemon.json" ]; then
    echo "备份现有配置..."
    sudo cp $DOCKER_CONFIG_DIR/daemon.json $DOCKER_CONFIG_DIR/daemon.json.backup
fi

# 创建新配置
echo "配置国内镜像加速器..."
sudo tee $DOCKER_CONFIG_DIR/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF

echo "重启Docker服务..."
sudo systemctl restart docker || sudo service docker restart

echo ""
echo "✅ 配置完成！"
echo ""
echo "方案2: 手动拉取镜像"
echo "----------------------------------------"
echo "如果上述方法不生效，可以尝试手动拉取镜像："
echo ""
echo "  docker pull python:3.11-slim"
echo "  docker pull node:18-alpine"
echo "  docker pull nginx:alpine"
echo ""
echo "然后再运行: docker-compose up -d"
echo ""
