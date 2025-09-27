import React, { useState, useEffect, useRef } from 'react';

const StableContainer = ({ children, className = "", delay = 100 }) => {
  const [isReady, setIsReady] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsReady(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  if (!isReady) {
    return (
      <div className={className} style={{ minHeight: '200px' }}>
        <div className="flex items-center justify-center h-full">
          <div className="text-slate-400">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  );
};

export default StableContainer;