/**
 * 经验列表组件
 */
import React from 'react';
import type { Experience } from '../types';
import './ExperienceList.css';

interface ExperienceListProps {
  experiences: Experience[];
}

export const ExperienceList: React.FC<ExperienceListProps> = ({ experiences }) => {
  if (experiences.length === 0) {
    return (
      <div className="experience-empty">
        <p>暂无学习经验，请先完成几次写作并选择您喜欢的文章</p>
      </div>
    );
  }

  return (
    <div className="experience-list">
      <h2>学习到的经验</h2>
      <div className="experience-items">
        {experiences.map((exp) => (
          <div key={exp.id} className="experience-item">
            <div className="experience-header">
              <span className="experience-category">{exp.category}</span>
              <div className="experience-stats">
                <span className="confidence">
                  置信度: {(exp.confidence_score * 100).toFixed(0)}%
                </span>
                <span className="sample-count">
                  样本数: {exp.sample_count}
                </span>
              </div>
            </div>
            {exp.preference_summary && (
              <p className="experience-summary">{exp.preference_summary}</p>
            )}
            <div className="experience-footer">
              <small>更新时间: {new Date(exp.updated_at).toLocaleString('zh-CN')}</small>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
