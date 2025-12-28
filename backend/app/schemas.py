"""
Pydantic数据模型（用于API请求和响应）
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class WritingRequest(BaseModel):
    """写作请求"""
    description: str = Field(..., min_length=1, description="写作内容描述")


class ArticleResponse(BaseModel):
    """文章响应"""
    id: int
    content: str
    variant_type: str
    structure_type: Optional[str] = None
    tone: Optional[str] = None

    class Config:
        from_attributes = True


class WritingResponse(BaseModel):
    """写作响应（包含两篇文章）"""
    task_id: int
    articles: List[ArticleResponse]
    created_at: datetime


class FeedbackRequest(BaseModel):
    """用户反馈请求"""
    task_id: int = Field(..., description="任务ID")
    selected_article_id: int = Field(..., description="选中的文章ID")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    message: str
    experience_updated: bool


class ExperienceResponse(BaseModel):
    """经验响应"""
    id: int
    category: str
    preference_summary: Optional[str]
    confidence_score: float
    sample_count: int
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    database: str
