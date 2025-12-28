.PHONY: help install dev build up down logs clean

help:
	@echo "AI写作助手 - 可用命令："
	@echo "  make install    - 安装依赖"
	@echo "  make dev        - 启动开发环境"
	@echo "  make build      - 构建Docker镜像"
	@echo "  make up         - 启动Docker容器"
	@echo "  make down       - 停止Docker容器"
	@echo "  make logs       - 查看日志"
	@echo "  make clean      - 清理资源"

install:
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install

dev-backend:
	@echo "启动后端开发服务器..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "启动前端开发服务器..."
	cd frontend && npm run dev

build:
	@echo "构建Docker镜像..."
	docker-compose build

up:
	@echo "启动Docker容器..."
	docker-compose up -d

down:
	@echo "停止Docker容器..."
	docker-compose down

logs:
	docker-compose logs -f

clean:
	@echo "清理资源..."
	docker-compose down -v
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf backend/*.db
	rm -rf frontend/dist
	rm -rf frontend/node_modules
