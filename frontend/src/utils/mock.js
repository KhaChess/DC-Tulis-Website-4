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
    { id: 'general', name: 'general', type: 'text', server: 'My Discord Server' },
    { id: 'random', name: 'random', type: 'text', server: 'My Discord Server' },
    { id: 'gaming', name: 'gaming', type: 'text', server: 'Gaming Community' },
    { id: 'dev-chat', name: 'dev-chat', type: 'text', server: 'Developer Hub' },
    { id: 'announcements', name: 'announcements', type: 'text', server: 'My Discord Server' },
    { id: 'off-topic', name: 'off-topic', type: 'text', server: 'Community Server' },
    { id: 'memes', name: 'memes', type: 'text', server: 'Fun Server' },
    { id: 'crypto-discussion', name: 'crypto-discussion', type: 'text', server: 'Finance Hub' },
    { id: 'tech-support', name: 'tech-support', type: 'text', server: 'Developer Hub' },
    { id: 'music', name: 'music', type: 'text', server: 'Entertainment' }
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