/**
 * 主应用组件
 */
import React, { useState, useEffect } from 'react';
import { ArticleCard } from './components/ArticleCard';
import { ExperienceList } from './components/ExperienceList';
import { ExperienceVisualization } from './components/ExperienceVisualization';
import { apiService } from './services/api';
import type { WritingResponse, Experience } from './types';
import './App.css';

function App() {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState<WritingResponse | null>(null);
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [experienceStats, setExperienceStats] = useState<any>(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载经验
  const loadExperiences = async () => {
    try {
      const data = await apiService.getExperiences();
      setExperiences(data);
    } catch (err) {
      console.error('加载经验失败:', err);
    }
  };

  // 加载经验统计
  const loadExperienceStats = async () => {
    try {
      const stats = await apiService.getExperienceStats();
      setExperienceStats(stats);
    } catch (err) {
      console.error('加载统计失败:', err);
    }
  };

  useEffect(() => {
    loadExperiences();
    loadExperienceStats();
  }, []);

  // 提交写作请求
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) {
      setError('请输入写作描述');
      return;
    }

    setLoading(true);
    setError(null);
    setFeedbackSubmitted(false);

    try {
      const response = await apiService.createWriting(description);
      setCurrentTask(response);
    } catch (err) {
      setError('生成文章失败，请检查后端服务是否正常运行');
      console.error('生成失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 选择文章
  const handleSelectArticle = async (articleId: number) => {
    if (!currentTask) return;

    try {
      const response = await apiService.submitFeedback({
        task_id: currentTask.task_id,
        selected_article_id: articleId,
      });

      setFeedbackSubmitted(true);
      alert(response.message);

      // 重新加载经验和统计数据
      await Promise.all([loadExperiences(), loadExperienceStats()]);

      // 清空当前任务，准备下一次
      setTimeout(() => {
        setCurrentTask(null);
        setDescription('');
        setFeedbackSubmitted(false);
      }, 1500);
    } catch (err) {
      setError('提交反馈失败');
      console.error('反馈失败:', err);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI写作助手</h1>
        <p className="subtitle">基于强化学习，不断优化您的写作体验</p>
      </header>

      <main className="app-main">
        <section className="input-section">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="description">写作描述</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="请输入您想创作的内容描述，例如：写一篇关于人工智能发展趋势的文章，800字左右"
                rows={4}
                disabled={loading || feedbackSubmitted}
              />
            </div>
            <button
              type="submit"
              className="submit-button"
              disabled={loading || feedbackSubmitted}
            >
              {loading ? '生成中...' : '生成文章'}
            </button>
          </form>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </section>

        {currentTask && (
          <section className="articles-section">
            <h2>请选择您更喜欢的文章</h2>
            <div className="articles-grid">
              {currentTask.articles.map((article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  onSelect={handleSelectArticle}
                  disabled={feedbackSubmitted}
                />
              ))}
            </div>
          </section>
        )}

        <section className="experiences-section">
          <ExperienceVisualization stats={experienceStats} />
          <ExperienceList experiences={experiences} />
        </section>
      </main>

      <footer className="app-footer">
        <p>通过GRPO强化学习，不断优化写作效果</p>
      </footer>
    </div>
  );
}

export default App;
