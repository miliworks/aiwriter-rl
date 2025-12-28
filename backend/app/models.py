"""
数据库ORM模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class WritingTask(Base):
    """写作任务表"""
    __tablename__ = "writing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False, comment="用户输入的写作描述")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    articles = relationship("Article", back_populates="task", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="task", uselist=False)


class Article(Base):
    """生成的文章表"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("writing_tasks.id"), nullable=False)
    content = Column(Text, nullable=False, comment="文章内容")
    variant_type = Column(String(50), nullable=False, comment="变体类型: A或B")

    # 文章特征（用于经验学习）
    style_params = Column(Text, comment="风格参数JSON")
    structure_type = Column(String(100), comment="结构类型")
    tone = Column(String(50), comment="语气风格")

    created_at = Column(DateTime, default=datetime.utcnow)
    is_selected = Column(Boolean, default=False, comment="是否被用户选择")

    # 关联关系
    task = relationship("WritingTask", back_populates="articles")


class UserFeedback(Base):
    """用户反馈表"""
    __tablename__ = "user_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("writing_tasks.id"), nullable=False)
    selected_article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    feedback_time = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    task = relationship("WritingTask", back_populates="feedback")
    selected_article = relationship("Article")


class Experience(Base):
    """经验知识库表"""
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), comment="经验分类")
    pattern = Column(Text, nullable=False, comment="识别出的模式")
    preference_summary = Column(Text, comment="用户偏好总结")
    confidence_score = Column(Float, default=0.5, comment="置信度分数")
    sample_count = Column(Integer, default=1, comment="支持该经验的样本数")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 经验元数据
    metadata = Column(Text, comment="额外元数据JSON")

    # GRPO相关字段
    reward_mean = Column(Float, default=0.0, comment="平均奖励")
    reward_std = Column(Float, default=1.0, comment="奖励标准差")
    iteration = Column(Integer, default=0, comment="迭代次数")
