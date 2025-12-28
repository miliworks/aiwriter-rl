"""
API路由端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import (
    WritingRequest,
    WritingResponse,
    FeedbackRequest,
    FeedbackResponse,
    ExperienceResponse,
    HealthResponse,
    ArticleResponse
)
from ..services.writing_service import WritingService
from ..services.experience_service import ExperienceService
from ..models import UserFeedback

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "sqlite"
    }


@router.post("/write", response_model=WritingResponse)
async def create_writing(
    request: WritingRequest,
    db: Session = Depends(get_db)
):
    """
    创建写作任务并生成两篇文章

    Args:
        request: 写作请求
        db: 数据库会话

    Returns:
        写作响应（包含两篇文章）
    """
    try:
        service = WritingService(db)
        task, articles = await service.create_writing_task(request.description)

        return WritingResponse(
            task_id=task.id,
            articles=[
                ArticleResponse(
                    id=article.id,
                    content=article.content,
                    variant_type=article.variant_type,
                    structure_type=article.structure_type,
                    tone=article.tone
                )
                for article in articles
            ],
            created_at=task.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    提交用户反馈并更新经验

    Args:
        request: 反馈请求
        db: 数据库会话

    Returns:
        反馈响应
    """
    try:
        # 创建反馈记录
        feedback = UserFeedback(
            task_id=request.task_id,
            selected_article_id=request.selected_article_id
        )
        db.add(feedback)
        db.commit()

        # 学习经验
        experience_service = ExperienceService(db)
        updated = await experience_service.learn_from_feedback(
            request.task_id,
            request.selected_article_id
        )

        return FeedbackResponse(
            message="反馈已提交，系统正在学习您的偏好",
            experience_updated=updated
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiences", response_model=List[ExperienceResponse])
async def get_experiences(db: Session = Depends(get_db)):
    """
    获取所有经验总结

    Args:
        db: 数据库会话

    Returns:
        经验列表
    """
    try:
        experience_service = ExperienceService(db)
        experiences = experience_service.get_all_experiences()

        return [
            ExperienceResponse(
                id=exp.id,
                category=exp.category,
                preference_summary=exp.preference_summary,
                confidence_score=exp.confidence_score,
                sample_count=exp.sample_count,
                updated_at=exp.updated_at
            )
            for exp in experiences
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=WritingResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """
    获取指定任务的详情

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        任务详情
    """
    try:
        service = WritingService(db)
        task, articles = service.get_task_with_articles(task_id)

        return WritingResponse(
            task_id=task.id,
            articles=[
                ArticleResponse(
                    id=article.id,
                    content=article.content,
                    variant_type=article.variant_type,
                    structure_type=article.structure_type,
                    tone=article.tone
                )
                for article in articles
            ],
            created_at=task.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
