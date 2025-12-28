"""
经验学习服务 - 基于GRPO的强化学习模块
Group Relative Policy Optimization
"""
from sqlalchemy.orm import Session
from typing import List, Dict
from ..models import Experience, UserFeedback, Article
from .ai_service import AIService
import json


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
        从用户反馈中学习（GRPO方式）

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

        # 至少3次反馈后开始GRPO优化
        if len(all_feedbacks) >= 3:
            await self._update_experiences_grpo(all_feedbacks)

        self.db.commit()
        return True

    async def _update_experiences_grpo(self, feedbacks: List[UserFeedback]):
        """
        使用GRPO方法更新经验知识库

        GRPO核心思想：
        1. 对比同一组（任务）中被选择和未被选择的输出
        2. 计算相对奖励
        3. 迭代优化偏好模型

        Args:
            feedbacks: 用户反馈列表
        """
        # 1. 收集选中和未选中的文章
        selected_articles = []
        rejected_articles = []

        for feedback in feedbacks:
            selected = self.db.query(Article).filter(
                Article.id == feedback.selected_article_id
            ).first()

            if selected and selected.style_params:
                selected_articles.append({
                    "id": selected.id,
                    "style_params": selected.style_params,
                    "content": selected.content[:200]  # 只保存前200字用于分析
                })

            # 获取同一任务中未选中的文章
            all_task_articles = self.db.query(Article).filter(
                Article.task_id == feedback.task_id
            ).all()

            for article in all_task_articles:
                if article.id != feedback.selected_article_id and article.style_params:
                    rejected_articles.append({
                        "id": article.id,
                        "style_params": article.style_params,
                        "content": article.content[:200]
                    })

        if not selected_articles:
            return

        # 2. 获取当前经验的迭代次数
        current_exp = self.db.query(Experience).filter(
            Experience.category == "style_preference"
        ).first()

        current_iteration = current_exp.iteration if current_exp else 0

        # 3. 使用GRPO方法分析和总结经验
        experience_data = await self.ai_service.summarize_experience_grpo(
            selected_articles,
            rejected_articles,
            current_iteration
        )

        # 4. 更新或创建经验记录
        self._upsert_experience_grpo(
            category="style_preference",
            summary=experience_data["preference_summary"],
            preferred_params=experience_data["preferred_params"],
            reward_info=experience_data["reward_info"],
            iteration=experience_data["iteration"],
            sample_count=len(selected_articles)
        )

    def _upsert_experience_grpo(
        self,
        category: str,
        summary: str,
        preferred_params: Dict[str, float],
        reward_info: Dict[str, float],
        iteration: int,
        sample_count: int
    ):
        """
        插入或更新GRPO经验

        Args:
            category: 经验类别
            summary: 自然语言总结
            preferred_params: 偏好的风格参数
            reward_info: 奖励统计信息
            iteration: 迭代次数
            sample_count: 样本数
        """
        existing = self.db.query(Experience).filter(
            Experience.category == category
        ).first()

        # 计算置信度：基于样本数和奖励标准差
        # 样本越多、标准差越小，置信度越高
        confidence = min(0.9, 0.3 + (sample_count / 50) * 0.5 + (1 - reward_info.get('std', 1.0)) * 0.2)

        if existing:
            # 更新现有经验（迭代优化）
            existing.preference_summary = summary
            existing.pattern = json.dumps(preferred_params)
            existing.confidence_score = confidence
            existing.sample_count = sample_count
            existing.reward_mean = reward_info.get('mean', 0.0)
            existing.reward_std = reward_info.get('std', 1.0)
            existing.iteration = iteration
            existing.metadata = json.dumps({
                "last_params": preferred_params,
                "reward_history": reward_info
            })
        else:
            # 创建新经验
            new_exp = Experience(
                category=category,
                pattern=json.dumps(preferred_params),
                preference_summary=summary,
                confidence_score=confidence,
                sample_count=sample_count,
                reward_mean=reward_info.get('mean', 0.0),
                reward_std=reward_info.get('std', 1.0),
                iteration=iteration,
                metadata=json.dumps({
                    "last_params": preferred_params,
                    "reward_history": reward_info
                })
            )
            self.db.add(new_exp)

        self.db.commit()

    def get_active_experiences(self, min_confidence: float = 0.4) -> List[str]:
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

    def get_preferred_style_params(self) -> Dict[str, float]:
        """
        获取偏好的风格参数（用于生成）

        Returns:
            偏好参数字典
        """
        exp = self.db.query(Experience).filter(
            Experience.category == "style_preference"
        ).order_by(
            Experience.confidence_score.desc()
        ).first()

        if exp and exp.pattern:
            try:
                return json.loads(exp.pattern)
            except:
                pass

        return {}

    def get_all_experiences(self) -> List[Experience]:
        """
        获取所有经验

        Returns:
            经验列表
        """
        return self.db.query(Experience).order_by(
            Experience.updated_at.desc()
        ).all()

    def get_experience_stats(self) -> Dict:
        """
        获取经验学习统计信息（用于可视化）

        Returns:
            统计信息字典
        """
        total_feedbacks = self.db.query(UserFeedback).count()
        experiences = self.get_all_experiences()

        # 获取风格参数分布
        style_exp = next(
            (exp for exp in experiences if exp.category == "style_preference"),
            None
        )

        preferred_params = {}
        if style_exp and style_exp.pattern:
            try:
                preferred_params = json.loads(style_exp.pattern)
            except:
                pass

        # 获取历史趋势（简化版）
        history = []
        if style_exp and style_exp.metadata:
            try:
                metadata = json.loads(style_exp.metadata)
                history = metadata.get('reward_history', [])
            except:
                pass

        return {
            "total_feedbacks": total_feedbacks,
            "total_experiences": len(experiences),
            "current_iteration": style_exp.iteration if style_exp else 0,
            "confidence_score": style_exp.confidence_score if style_exp else 0.0,
            "preferred_params": preferred_params,
            "reward_mean": style_exp.reward_mean if style_exp else 0.0,
            "reward_std": style_exp.reward_std if style_exp else 1.0,
            "history": history
        }
