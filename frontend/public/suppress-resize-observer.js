// Suppress ResizeObserver errors that are safe to ignore
(function() {
  const originalError = console.error;
  console.error = function(...args) {
    if (
      args.length > 0 &&
      typeof args[0] === 'string' &&
      args[0].includes('ResizeObserver loop completed with undelivered notifications')
    ) {
      // Suppress this specific error as it's harmless
      return;
    }
    originalError.apply(console, args);
  };

  // Also suppress via window error handler
  window.addEventListener('error', function(e) {
    if (e.message && e.message.includes('ResizeObserver loop completed')) {
      e.preventDefault();
      return true;
    }
  });
})();