"""
写作服务 - 整合AI调用和经验学习
"""
from sqlalchemy.orm import Session
from typing import Tuple, List
from ..models import WritingTask, Article
from .ai_service import AIService
from .experience_service import ExperienceService
import asyncio


class WritingService:
    """写作服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.experience_service = ExperienceService(db)

    async def create_writing_task(self, description: str) -> Tuple[WritingTask, List[Article]]:
        """
        创建写作任务并生成两篇文章

        Args:
            description: 用户输入的写作描述

        Returns:
            (任务对象, 文章列表)
        """
        # 1. 创建写作任务
        task = WritingTask(description=description)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        # 2. 获取历史经验
        experiences = self.experience_service.get_active_experiences()

        # 3. 并行生成两篇文章（变体A和B）
        try:
            article_a_data, article_b_data = await asyncio.gather(
                self.ai_service.generate_article(description, "A", experiences),
                self.ai_service.generate_article(description, "B", experiences)
            )

            # 4. 保存文章到数据库
            article_a = Article(
                task_id=task.id,
                content=article_a_data["content"],
                variant_type=article_a_data["variant_type"],
                structure_type=article_a_data["structure_type"],
                tone=article_a_data["tone"],
                style_params=article_a_data["style_params"]
            )

            article_b = Article(
                task_id=task.id,
                content=article_b_data["content"],
                variant_type=article_b_data["variant_type"],
                structure_type=article_b_data["structure_type"],
                tone=article_b_data["tone"],
                style_params=article_b_data["style_params"]
            )

            self.db.add(article_a)
            self.db.add(article_b)
            self.db.commit()
            self.db.refresh(article_a)
            self.db.refresh(article_b)

            return task, [article_a, article_b]

        except Exception as e:
            self.db.rollback()
            raise Exception(f"生成文章失败: {str(e)}")

    def get_task_with_articles(self, task_id: int) -> Tuple[WritingTask, List[Article]]:
        """
        获取任务和关联的文章

        Args:
            task_id: 任务ID

        Returns:
            (任务对象, 文章列表)
        """
        task = self.db.query(WritingTask).filter(
            WritingTask.id == task_id
        ).first()

        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        articles = self.db.query(Article).filter(
            Article.task_id == task_id
        ).all()

        return task, articles
