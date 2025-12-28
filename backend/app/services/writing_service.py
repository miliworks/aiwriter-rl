"""
写作服务 - 整合AI调用、经验学习和随机风格生成
"""
from sqlalchemy.orm import Session
from typing import Tuple, List
from ..models import WritingTask, Article
from .ai_service import AIService
from .experience_service import ExperienceService
from .style_generator import StyleGenerator
import asyncio


class WritingService:
    """写作服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.experience_service = ExperienceService(db)
        self.style_generator = StyleGenerator()

    async def create_writing_task(self, description: str) -> Tuple[WritingTask, List[Article]]:
        """
        创建写作任务并生成两篇文章

        核心改进：
        1. 使用随机风格生成，而非固定A/B模式
        2. 支持从经验中学习偏好参数
        3. 保持一定探索性以全面覆盖用户偏好空间

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
        preferred_params = self.experience_service.get_preferred_style_params()

        # 3. 生成两个差异较大的随机风格
        if preferred_params:
            # 如果有经验，基于偏好生成，但保持30%探索率
            style_a = self.style_generator.generate_from_preferences(
                preferred_params,
                exploration_rate=0.3
            )
            # B版本完全随机，用于探索新空间
            style_b = self.style_generator.generate_random_style()
        else:
            # 没有经验时，生成两个差异较大的随机风格
            style_a, style_b = self.style_generator.generate_diverse_pair()

        # 4. 并行生成两篇文章
        try:
            article_a_data, article_b_data = await asyncio.gather(
                self.ai_service.generate_article(description, style_a, experiences),
                self.ai_service.generate_article(description, style_b, experiences)
            )

            # 5. 保存文章到数据库
            article_a = Article(
                task_id=task.id,
                content=article_a_data["content"],
                variant_type="A",
                style_params=article_a_data["style_params"]
            )

            article_b = Article(
                task_id=task.id,
                content=article_b_data["content"],
                variant_type="B",
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
