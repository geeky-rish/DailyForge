import React from 'react';
import type { Quote } from '../types';

interface QuoteCardProps {
  quote: Quote | null;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({ quote }) => {
  if (!quote) return null;

  return (
    <div className="quote-card">
      <div className="quote-text">
        &ldquo;{quote.text}&rdquo;
      </div>
      <div className="quote-author">
        &mdash; {quote.author || 'DailyForge'}
      </div>
    </div>
  );
};
