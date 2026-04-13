import React from 'react';
import { motion } from 'framer-motion';
import { FileText, ExternalLink, Clock } from 'lucide-react';

const PagesList = ({ pages, currentPageId, onOpenPage, onClose }) => {
  return (
    <div className="p-6 md:p-10" data-testid="pages-list-modal">
      <div className="max-w-[800px] mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h2
            className="font-headline text-2xl font-bold tracking-tight"
            style={{ color: 'var(--on-surface)' }}
          >
            Pages
          </h2>
          <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
            Select a page to edit its content
          </p>
        </div>

        {/* Pages grid */}
        <div className="space-y-2">
          {pages.map((page, index) => (
            <motion.button
              key={page._id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
              onClick={() => onOpenPage(page._id)}
              data-testid={`pages-list-item-${page.slug}`}
              className="w-full text-left p-4 rounded-[4px] flex items-center gap-4 transition-colors duration-150 group"
              style={{
                backgroundColor:
                  currentPageId === page._id
                    ? 'rgba(16, 185, 129, 0.08)'
                    : 'rgba(255, 255, 255, 0.02)',
              }}
              onMouseEnter={(e) => {
                if (currentPageId !== page._id) {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                }
              }}
              onMouseLeave={(e) => {
                if (currentPageId !== page._id) {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
                }
              }}
            >
              {/* Icon */}
              <div
                className="w-10 h-10 rounded-[4px] grid place-items-center flex-shrink-0"
                style={{
                  backgroundColor:
                    currentPageId === page._id
                      ? 'rgba(16, 185, 129, 0.14)'
                      : 'rgba(255, 255, 255, 0.04)',
                  color:
                    currentPageId === page._id
                      ? 'var(--primary-2)'
                      : 'var(--muted)',
                }}
              >
                <FileText size={18} />
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span
                    className="font-headline font-semibold text-sm"
                    style={{ color: 'var(--on-surface)' }}
                  >
                    {page.name}
                  </span>
                  <span
                    className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-[3px]"
                    style={{
                      backgroundColor:
                        page.status === 'published'
                          ? 'rgba(16, 185, 129, 0.14)'
                          : 'rgba(245, 158, 11, 0.14)',
                      color:
                        page.status === 'published' ? '#4edea3' : '#fbbf24',
                    }}
                  >
                    {page.status}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs" style={{ color: 'var(--muted-2)' }}>
                    {page.slug}
                  </span>
                  <span className="text-xs" style={{ color: 'var(--muted-2)' }}>
                    {page.element_count} elements
                  </span>
                </div>
              </div>

              {/* Arrow */}
              <ExternalLink
                size={14}
                className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
                style={{ color: 'var(--muted)' }}
              />
            </motion.button>
          ))}
        </div>

        {pages.length === 0 && (
          <div className="text-center py-16">
            <p className="font-headline text-sm" style={{ color: 'var(--muted)' }}>
              No pages yet
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PagesList;
