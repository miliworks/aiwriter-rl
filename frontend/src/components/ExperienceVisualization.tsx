/**
 * 经验可视化组件 - 展示GRPO学习进度和风格偏好
 */
import React from 'react';
import './ExperienceVisualization.css';

interface StyleParams {
  formality?: number;
  emotion?: number;
  detail_level?: number;
  creativity?: number;
  technicality?: number;
  narrative?: number;
}

interface ExperienceStats {
  total_feedbacks: number;
  total_experiences: number;
  current_iteration: number;
  confidence_score: number;
  preferred_params: StyleParams;
  reward_mean: number;
  reward_std: number;
}

interface ExperienceVisualizationProps {
  stats: ExperienceStats | null;
}

export const ExperienceVisualization: React.FC<ExperienceVisualizationProps> = ({
  stats,
}) => {
  if (!stats || stats.total_feedbacks === 0) {
    return (
      <div className="viz-empty">
        <p>暂无学习数据，请先完成几次写作反馈</p>
      </div>
    );
  }

  const styleParams = stats.preferred_params || {};
  const dimNames: Record<string, string> = {
    formality: '正式度',
    emotion: '情感度',
    detail_level: '详细度',
    creativity: '创新度',
    technicality: '专业度',
    narrative: '叙事性',
  };

  return (
    <div className="experience-viz">
      <h2>经验学习可视化</h2>

      {/* 统计概览 */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.total_feedbacks}</div>
          <div className="stat-label">总反馈次数</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.current_iteration}</div>
          <div className="stat-label">GRPO迭代次数</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{(stats.confidence_score * 100).toFixed(0)}%</div>
          <div className="stat-label">置信度</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.reward_mean.toFixed(2)}</div>
          <div className="stat-label">平均奖励</div>
        </div>
      </div>

      {/* 风格参数雷达图（CSS实现） */}
      <div className="style-params-section">
        <h3>偏好风格分布</h3>
        <div className="params-bars">
          {Object.entries(dimNames).map(([key, name]) => {
            const value = styleParams[key as keyof StyleParams] || 0.5;
            const percentage = value * 100;

            return (
              <div key={key} className="param-bar-container">
                <div className="param-label">{name}</div>
                <div className="param-bar-wrapper">
                  <div
                    className="param-bar"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: getColorForValue(value),
                    }}
                  >
                    <span className="param-value">{value.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 学习进度指示器 */}
      <div className="learning-progress-section">
        <h3>学习进度</h3>
        <div className="progress-info">
          <div className="progress-item">
            <span className="progress-label">探索阶段</span>
            <div className="progress-bar-container">
              <div
                className="progress-bar"
                style={{
                  width: `${Math.min((stats.total_feedbacks / 10) * 100, 100)}%`,
                }}
              />
            </div>
            <span className="progress-text">
              {stats.total_feedbacks}/10 次反馈
            </span>
          </div>

          <div className="progress-item">
            <span className="progress-label">置信度提升</span>
            <div className="progress-bar-container">
              <div
                className="progress-bar confidence"
                style={{
                  width: `${stats.confidence_score * 100}%`,
                }}
              />
            </div>
            <span className="progress-text">
              {(stats.confidence_score * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* GRPO指标 */}
      <div className="grpo-metrics">
        <h3>GRPO优化指标</h3>
        <div className="metrics-grid">
          <div className="metric-item">
            <span className="metric-label">奖励均值</span>
            <span className="metric-value">{stats.reward_mean.toFixed(3)}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">奖励标准差</span>
            <span className="metric-value">{stats.reward_std.toFixed(3)}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">迭代次数</span>
            <span className="metric-value">{stats.current_iteration}</span>
          </div>
        </div>
        <div className="grpo-explanation">
          <p>
            <strong>GRPO (Group Relative Policy Optimization)</strong>
            通过对比同一任务中被选择和未被选择的文章，
            计算相对奖励并迭代优化偏好模型。
            标准差越小表示偏好越稳定。
          </p>
        </div>
      </div>
    </div>
  );
};

/**
 * 根据参数值返回颜色
 */
function getColorForValue(value: number): string {
  if (value > 0.7) return '#4caf50'; // 绿色 - 高偏好
  if (value > 0.3) return '#2196f3'; // 蓝色 - 中等偏好
  return '#ff9800'; // 橙色 - 低偏好
}
