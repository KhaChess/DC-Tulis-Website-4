// Comprehensive error suppression for ResizeObserver and related issues
(function() {
  'use strict';
  
  // Store original console methods
  const originalError = console.error;
  const originalWarn = console.warn;
  
  // List of errors to suppress
  const suppressPatterns = [
    'ResizeObserver loop completed with undelivered notifications',
    'ResizeObserver loop',
    'Non-passive event listener',
    'Viewport target',
    '[Violation]'
  ];
  
  // Override console.error
  console.error = function(...args) {
    const message = args.join(' ');
    const shouldSuppress = suppressPatterns.some(pattern => 
      message.includes(pattern)
    );
    
    if (!shouldSuppress) {
      originalError.apply(console, args);
    }
  };
  
  // Override console.warn
  console.warn = function(...args) {
    const message = args.join(' ');
    const shouldSuppress = suppressPatterns.some(pattern => 
      message.includes(pattern)
    );
    
    if (!shouldSuppress) {
      originalWarn.apply(console, args);
    }
  };
  
  // Handle window errors
  window.addEventListener('error', function(e) {
    const shouldSuppress = suppressPatterns.some(pattern => 
      e.message.includes(pattern)
    );
    
    if (shouldSuppress) {
      e.preventDefault();
      e.stopPropagation();
      return true;
    }
  }, true);
  
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', function(e) {
    const message = e.reason ? e.reason.toString() : '';
    const shouldSuppress = suppressPatterns.some(pattern => 
      message.includes(pattern)
    );
    
    if (shouldSuppress) {
      e.preventDefault();
      e.stopPropagation();
      return true;
    }
  });
  
  // Monkey patch ResizeObserver to be more resilient
  if (window.ResizeObserver) {
    const OriginalResizeObserver = window.ResizeObserver;
    
    window.ResizeObserver = class extends OriginalResizeObserver {
      constructor(callback) {
        const wrappedCallback = (entries, observer) => {
          try {
            // Use requestAnimationFrame to avoid loop issues
            window.requestAnimationFrame(() => {
              callback(entries, observer);
            });
          } catch (error) {
            // Silently handle ResizeObserver errors
            if (!error.message.includes('ResizeObserver')) {
              console.error('ResizeObserver callback error:', error);
            }
          }
        };
        super(wrappedCallback);
      }
    };
  }
  
  console.log('✅ Error suppression initialized');
})();