"""
经验学习服务 - 基于用户反馈的强化学习模块
"""
from sqlalchemy.orm import Session
from typing import List, Dict
from ..models import Experience, UserFeedback, Article
from .ai_service import AIService
import json
from collections import Counter


class ExperienceService:
    """经验学习服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    async def learn_from_feedback(
        self,
        task_id: int,
        selected_article_id: int
    ) -> bool:
        """
        从用户反馈中学习

        Args:
            task_id: 任务ID
            selected_article_id: 用户选择的文章ID

        Returns:
            是否成功更新经验
        """
        # 获取选中的文章和未选中的文章
        selected_article = self.db.query(Article).filter(
            Article.id == selected_article_id
        ).first()

        if not selected_article:
            return False

        # 标记选中的文章
        selected_article.is_selected = True

        # 获取所有历史反馈
        all_feedbacks = self.db.query(UserFeedback).all()

        if len(all_feedbacks) >= 3:  # 至少3次反馈后开始总结
            await self._update_experiences(all_feedbacks)

        self.db.commit()
        return True

    async def _update_experiences(self, feedbacks: List[UserFeedback]):
        """
        更新经验知识库

        Args:
            feedbacks: 用户反馈列表
        """
        # 收集选中和未选中的文章
        selected_articles = []
        rejected_articles = []

        for feedback in feedbacks:
            selected = self.db.query(Article).filter(
                Article.id == feedback.selected_article_id
            ).first()

            if selected:
                selected_articles.append({
                    "structure_type": selected.structure_type,
                    "tone": selected.tone,
                    "variant_type": selected.variant_type
                })

            # 获取同一任务中未选中的文章
            all_task_articles = self.db.query(Article).filter(
                Article.task_id == feedback.task_id
            ).all()

            for article in all_task_articles:
                if article.id != feedback.selected_article_id:
                    rejected_articles.append({
                        "structure_type": article.structure_type,
                        "tone": article.tone,
                        "variant_type": article.variant_type
                    })

        # 分析偏好模式
        await self._analyze_patterns(selected_articles, rejected_articles)

    async def _analyze_patterns(
        self,
        selected: List[Dict],
        rejected: List[Dict]
    ):
        """
        分析用户偏好模式

        Args:
            selected: 选中的文章特征
            rejected: 未选中的文章特征
        """
        # 1. 分析结构偏好
        selected_structures = [a["structure_type"] for a in selected if a.get("structure_type")]
        if selected_structures:
            structure_counter = Counter(selected_structures)
            most_common_structure = structure_counter.most_common(1)[0]

            confidence = most_common_structure[1] / len(selected_structures)

            self._upsert_experience(
                category="structure_preference",
                pattern=most_common_structure[0],
                preference_summary=f"用户偏好{most_common_structure[0]}结构的文章",
                confidence_score=confidence,
                sample_count=len(selected_structures)
            )

        # 2. 分析语气偏好
        selected_tones = [a["tone"] for a in selected if a.get("tone")]
        if selected_tones:
            tone_counter = Counter(selected_tones)
            most_common_tone = tone_counter.most_common(1)[0]

            confidence = most_common_tone[1] / len(selected_tones)

            self._upsert_experience(
                category="tone_preference",
                pattern=most_common_tone[0],
                preference_summary=f"用户偏好{most_common_tone[0]}语气的文章",
                confidence_score=confidence,
                sample_count=len(selected_tones)
            )

        # 3. 使用AI生成综合经验总结
        if len(selected) >= 3:
            summary = await self.ai_service.summarize_experience(
                selected, rejected
            )

            if summary:
                self._upsert_experience(
                    category="general_preference",
                    pattern="综合偏好",
                    preference_summary=summary,
                    confidence_score=0.7,
                    sample_count=len(selected)
                )

    def _upsert_experience(
        self,
        category: str,
        pattern: str,
        preference_summary: str,
        confidence_score: float,
        sample_count: int
    ):
        """
        插入或更新经验

        Args:
            category: 经验类别
            pattern: 模式
            preference_summary: 偏好总结
            confidence_score: 置信度
            sample_count: 样本数
        """
        existing = self.db.query(Experience).filter(
            Experience.category == category
        ).first()

        if existing:
            # 更新现有经验
            existing.pattern = pattern
            existing.preference_summary = preference_summary
            existing.confidence_score = confidence_score
            existing.sample_count = sample_count
        else:
            # 创建新经验
            new_exp = Experience(
                category=category,
                pattern=pattern,
                preference_summary=preference_summary,
                confidence_score=confidence_score,
                sample_count=sample_count
            )
            self.db.add(new_exp)

        self.db.commit()

    def get_active_experiences(self, min_confidence: float = 0.5) -> List[str]:
        """
        获取活跃的经验（用于指导AI生成）

        Args:
            min_confidence: 最小置信度阈值

        Returns:
            经验总结列表
        """
        experiences = self.db.query(Experience).filter(
            Experience.confidence_score >= min_confidence
        ).order_by(
            Experience.confidence_score.desc()
        ).limit(5).all()

        return [
            exp.preference_summary
            for exp in experiences
            if exp.preference_summary
        ]

    def get_all_experiences(self) -> List[Experience]:
        """
        获取所有经验

        Returns:
            经验列表
        """
        return self.db.query(Experience).order_by(
            Experience.updated_at.desc()
        ).all()
