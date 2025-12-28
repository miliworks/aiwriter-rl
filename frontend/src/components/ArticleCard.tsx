/**
 * 文章卡片组件
 */
import React from 'react';
import type { Article } from '../types';
import './ArticleCard.css';

interface ArticleCardProps {
  article: Article;
  onSelect: (articleId: number) => void;
  disabled?: boolean;
}

export const ArticleCard: React.FC<ArticleCardProps> = ({
  article,
  onSelect,
  disabled = false,
}) => {
  return (
    <div className="article-card">
      <div className="article-header">
        <h3>版本 {article.variant_type}</h3>
        <div className="article-meta">
          {article.structure_type && (
            <span className="tag">结构: {article.structure_type}</span>
          )}
          {article.tone && (
            <span className="tag">语气: {article.tone}</span>
          )}
        </div>
      </div>
      <div className="article-content">
        <div className="content-text">{article.content}</div>
      </div>
      <div className="article-footer">
        <button
          className="select-button"
          onClick={() => onSelect(article.id)}
          disabled={disabled}
        >
          选择这篇文章
        </button>
      </div>
    </div>
  );
};
