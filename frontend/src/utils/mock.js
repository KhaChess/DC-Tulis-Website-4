export const mockData = {
  sessions: [
    {
      id: '1',
      channel: 'general',
      messages: 5,
      status: 'running',
      startTime: '2025-01-15T10:30:00Z'
    },
    {
      id: '2', 
      channel: 'random',
      messages: 3,
      status: 'paused',
      startTime: '2025-01-15T09:15:00Z'
    }
  ],
  
  channels: [
    { id: 'general', name: 'general', type: 'text' },
    { id: 'random', name: 'random', type: 'text' },
    { id: 'gaming', name: 'gaming', type: 'text' },
    { id: 'dev-chat', name: 'dev-chat', type: 'text' },
    { id: 'announcements', name: 'announcements', type: 'text' }
  ],
  
  messages: [
    'Hello everyone! 👋',
    'How is everyone doing today?',
    'Great weather today!',
    'Anyone up for a game?',
    'Good morning! ☀️'
  ],
  
  stats: {
    totalSent: 1247,
    totalFailed: 23,
    successRate: 98.2,
    avgResponseTime: 2.3
  }
};