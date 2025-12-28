/**
 * API服务
 */
import axios from 'axios';
import type { WritingResponse, Experience, FeedbackRequest, FeedbackResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // AI生成可能需要较长时间
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  /**
   * 创建写作任务
   */
  async createWriting(description: string): Promise<WritingResponse> {
    const response = await api.post<WritingResponse>('/write', { description });
    return response.data;
  },

  /**
   * 提交用户反馈
   */
  async submitFeedback(feedback: FeedbackRequest): Promise<FeedbackResponse> {
    const response = await api.post<FeedbackResponse>('/feedback', feedback);
    return response.data;
  },

  /**
   * 获取所有经验
   */
  async getExperiences(): Promise<Experience[]> {
    const response = await api.get<Experience[]>('/experiences');
    return response.data;
  },

  /**
   * 获取经验统计数据
   */
  async getExperienceStats(): Promise<any> {
    const response = await api.get('/experiences/stats');
    return response.data;
  },

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};
