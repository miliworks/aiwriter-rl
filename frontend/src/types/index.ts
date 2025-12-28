/**
 * 类型定义
 */

export interface Article {
  id: number;
  content: string;
  variant_type: string;
  structure_type?: string;
  tone?: string;
}

export interface WritingResponse {
  task_id: number;
  articles: Article[];
  created_at: string;
}

export interface Experience {
  id: number;
  category: string;
  preference_summary: string | null;
  confidence_score: number;
  sample_count: number;
  updated_at: string;
}

export interface FeedbackRequest {
  task_id: number;
  selected_article_id: number;
}

export interface FeedbackResponse {
  message: string;
  experience_updated: boolean;
}
