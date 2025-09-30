import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { toast } from '../hooks/use-toast';
import { Toaster } from '../components/ui/toaster';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  MessageSquare, 
  Clock, 
  Activity,
  Plus,
  Trash2,
  Wifi,
  WifiOff,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Loader
} from 'lucide-react';
import { mockData } from '../utils/mock';
import useWebSocket from '../hooks/useWebSocket';

const EnhancedDashboard = () => {
  // Basic session state
  const [messageList, setMessageList] = useState(['']);
  const [selectedChannel, setSelectedChannel] = useState('');
  const [customChannelId, setCustomChannelId] = useState('');
  const [typingDelay, setTypingDelay] = useState(1000);
  const [messageDelay, setMessageDelay] = useState(5000);
  const [customChannels, setCustomChannels] = useState([]);

  // Enhanced session state
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionStatus, setSessionStatus] = useState('idle');
  const [sessionStats, setSessionStats] = useState({ 
    sent: 0, 
    failed: 0, 
    uptime: '00:00:00',
    current_message: '',
    typing_progress: 0,
    current_message_index: 0,
    total_messages: 0
  });
  
  // Real-time features state
  const [isTyping, setIsTyping] = useState(false);
  const [canResume, setCanResume] = useState(false);
  const [failedMessages, setFailedMessages] = useState([]);
  const [lastError, setLastError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  
  // UI state
  const [showRetryPanel, setShowRetryPanel] = useState(false);
  const [sessionStartTime, setSessionStartTime] = useState(null);
  const uptimeIntervalRef = useRef(null);

  // WebSocket connection
  const handleWebSocketMessage = useCallback((data) => {
    console.log('WebSocket message received in component:', data);
    
    switch (data.type) {
      case 'session_update':
        handleSessionUpdate(data.data);
        break;
      case 'typing_update':
        handleTypingUpdate(data.data);
        break;
      case 'error_notification':
        handleErrorNotification(data.data);
        break;
      case 'retry_initiated':
        handleRetryInitiated(data.data);
        break;
      case 'connection_established':
        console.log('WebSocket connection established');
        break;
      case 'pong':
        console.log('WebSocket pong received');
        break;
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }, []);

  const { connectionStatus, sendMessage, requestStatus } = useWebSocket(currentSessionId, handleWebSocketMessage);

  // Handle different types of real-time updates
  const handleSessionUpdate = useCallback((data) => {
    console.log('Session update:', data);
    
    if (data.status) setSessionStatus(data.status);
    if (data.messages_sent !== undefined) {
      setSessionStats(prev => ({ ...prev, sent: data.messages_sent }));
    }
    if (data.messages_failed !== undefined) {
      setSessionStats(prev => ({ ...prev, failed: data.messages_failed }));
    }
    if (data.current_message) {
      setSessionStats(prev => ({ ...prev, current_message: data.current_message }));
    }
    if (data.current_message_index !== undefined) {
      setSessionStats(prev => ({ ...prev, current_message_index: data.current_message_index }));
    }
    if (data.can_resume !== undefined) setCanResume(data.can_resume);
    if (data.failed_messages) setFailedMessages(data.failed_messages);
    if (data.last_error) setLastError(data.last_error);
    if (data.retry_count !== undefined) setRetryCount(data.retry_count);
    if (data.is_typing !== undefined) setIsTyping(data.is_typing);
  }, []);

  const handleTypingUpdate = useCallback((data) => {
    console.log('Typing update:', data);
    
    if (data.typing_progress !== undefined) {
      setSessionStats(prev => ({ ...prev, typing_progress: data.typing_progress }));
    }
    setIsTyping(true);
    
    // Auto-reset typing indicator after progress completion
    if (data.typing_progress >= 100) {
      setTimeout(() => setIsTyping(false), 1000);
    }
  }, []);

  const handleErrorNotification = useCallback((data) => {
    console.log('Error notification:', data);
    
    setLastError(data.error);
    
    toast({
      title: "🚨 Error Occurred",
      description: data.error,
      variant: "destructive",
      action: data.can_retry ? (
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setShowRetryPanel(true)}
        >
          Retry Options
        </Button>
      ) : undefined
    });

    if (data.can_retry) {
      setCanResume(true);
      setShowRetryPanel(true);
    }
  }, []);

  const handleRetryInitiated = useCallback((data) => {
    console.log('Retry initiated:', data);
    
    setRetryCount(data.retry_count);
    setShowRetryPanel(false);
    
    toast({
      title: "🔄 Retry Started",
      description: `Retrying ${data.messages_to_retry} failed messages (Attempt #${data.retry_count})`,
    });
  }, []);

  // Uptime calculation
  useEffect(() => {
    if (sessionStatus === 'running' && sessionStartTime) {
      uptimeIntervalRef.current = setInterval(() => {
        const elapsed = Date.now() - sessionStartTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        setSessionStats(prev => ({
          ...prev,
          uptime: `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
        }));
      }, 1000);
    } else {
      if (uptimeIntervalRef.current) {
        clearInterval(uptimeIntervalRef.current);
        uptimeIntervalRef.current = null;
      }
    }

    return () => {
      if (uptimeIntervalRef.current) {
        clearInterval(uptimeIntervalRef.current);
      }
    };
  }, [sessionStatus, sessionStartTime]);

  // Initialize component
  useEffect(() => {
    console.log('EnhancedDashboard component mounted');
    setSelectedChannel(mockData.channels[0]?.id || '');
  }, []);

  // Message management
  const addMessage = () => {
    setMessageList([...messageList, '']);
  };

  const removeMessage = (index) => {
    const newList = messageList.filter((_, i) => i !== index);
    setMessageList(newList.length > 0 ? newList : ['']);
  };

  const updateMessage = (index, value) => {
    const newList = [...messageList];
    newList[index] = value;
    setMessageList(newList);
  };

  // Channel management
  const addCustomChannel = () => {
    if (!customChannelId.trim()) return;
    
    const extractedId = extractChannelId(customChannelId);
    if (!extractedId) {
      toast({
        title: "Invalid Channel ID",
        description: "Please enter a valid Discord Channel ID or URL.",
        variant: "destructive"
      });
      return;
    }

    const newChannel = {
      id: extractedId,
      name: `custom-${extractedId.slice(-4)}`,
      server: 'Custom Channel',
      custom: true
    };

    const exists = customChannels.some(c => c.id === extractedId);
    if (!exists) {
      setCustomChannels(prev => [...prev, newChannel]);
      toast({
        title: "✅ Channel Added",
        description: `Custom channel ${extractedId} added to list.`,
      });
    }
    
    setSelectedChannel(extractedId);
    setCustomChannelId('');
  };

  const extractChannelId = (input) => {
    if (!input) return null;
    
    if (/^\d{17,19}$/.test(input.trim())) {
      return input.trim();
    }
    
    const urlMatch = input.match(/discord\.com\/channels\/\d+\/(\d+)/);
    if (urlMatch) {
      return urlMatch[1];
    }
    
    return null;
  };

  // Enhanced session control
  const startSession = async () => {
    const channelId = customChannelId || selectedChannel;
    const extractedId = extractChannelId(channelId);
    
    if (!channelId || messageList.every(msg => !msg.trim())) {
      toast({
        title: "⚠️ Validation Error",
        description: "Please select a channel and add at least one message.",
        variant: "destructive"
      });
      return;
    }

    if (customChannelId && !extractedId) {
      toast({
        title: "❌ Invalid Channel ID",
        description: "Please enter a valid Discord Channel ID or URL.",
        variant: "destructive"
      });
      return;
    }

    try {
      const channelDisplay = extractedId || selectedChannel;
      const validMessages = messageList.filter(msg => msg.trim());
      
      // Reset session state
      setSessionStatus('starting');
      setSessionStats(prev => ({ 
        ...prev, 
        sent: 0, 
        failed: 0, 
        uptime: '00:00:00',
        current_message: 'Starting session...',
        typing_progress: 0,
        current_message_index: 0,
        total_messages: validMessages.length
      }));
      setIsTyping(false);
      setCanResume(false);
      setFailedMessages([]);
      setLastError(null);
      setRetryCount(0);
      setShowRetryPanel(false);
      
      // Start backend session
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auto-typer/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel_id: channelDisplay,
          messages: validMessages,
          typing_delay: typingDelay,
          message_delay: messageDelay
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to start session: ${response.status}`);
      }

      const sessionData = await response.json();
      setCurrentSessionId(sessionData.id);
      setSessionStartTime(Date.now());
      
      toast({
        title: "🚀 Session Started",
        description: `Browser automation started for channel: ${channelDisplay}`,
      });

    } catch (error) {
      console.error('Error starting session:', error);
      toast({
        title: "❌ Error",
        description: "Failed to start browser automation session",
        variant: "destructive"
      });
      setSessionStatus('idle');
    }
  };

  const pauseSession = async () => {
    if (!currentSessionId) return;

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auto-typer/${currentSessionId}/pause`, {
        method: 'POST'
      });

      if (response.ok) {
        toast({
          title: "⏸️ Session Paused",
          description: "Session has been paused. You can resume it later.",
        });
      }
    } catch (error) {
      console.error('Error pausing session:', error);
    }
  };

  const resumeSession = async () => {
    if (!currentSessionId) return;

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auto-typer/${currentSessionId}/resume`, {
        method: 'POST'
      });

      if (response.ok) {
        setSessionStartTime(Date.now());
        toast({
          title: "▶️ Session Resumed",
          description: "Session has been resumed from where it left off.",
        });
      }
    } catch (error) {
      console.error('Error resuming session:', error);
    }
  };

  const stopSession = async () => {
    if (!currentSessionId) return;
    
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auto-typer/${currentSessionId}/stop`, {
        method: 'POST'
      });

      // Reset state
      setSessionStatus('idle');
      setCurrentSessionId(null);
      setSessionStartTime(null);
      setIsTyping(false);
      setCanResume(false);
      setShowRetryPanel(false);
      
      setTimeout(() => {
        setSessionStats({ 
          sent: 0, 
          failed: 0, 
          uptime: '00:00:00',
          current_message: '',
          typing_progress: 0,
          current_message_index: 0,
          total_messages: 0
        });
      }, 2000);

      toast({
        title: "⏹️ Session Stopped",
        description: "Browser automation has been stopped.",
      });
    } catch (error) {
      console.error('Error stopping session:', error);
    }
  };

  const retryFailedMessages = async () => {
    if (!currentSessionId) return;

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auto-typer/${currentSessionId}/retry`, {
        method: 'POST'
      });

      if (response.ok) {
        setShowRetryPanel(false);
      }
    } catch (error) {
      console.error('Error retrying failed messages:', error);
    }
  };

  // Determine session controls availability
  const isRunning = sessionStatus === 'running';
  const isPaused = sessionStatus === 'paused';
  const canStart = sessionStatus === 'idle' || sessionStatus === 'stopped' || sessionStatus === 'completed';
  const canPause = isRunning;
  const canStop = isRunning || isPaused;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-white tracking-tight">
            Discord Auto-Typer ⚡
          </h1>
          <p className="text-slate-300 text-lg">
            Real-time browser automation dengan WebSocket support
          </p>
          
          {/* Connection Status */}
          <div className="flex items-center justify-center space-x-2">
            {connectionStatus === 'Connected' ? (
              <>
                <Wifi className="h-4 w-4 text-green-400" />
                <span className="text-green-400 text-sm">WebSocket Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-400" />
                <span className="text-red-400 text-sm">WebSocket {connectionStatus}</span>
              </>
            )}
          </div>
        </div>

        {/* Enhanced Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <MessageSquare className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-sm text-slate-400">Messages Sent</p>
                  <p className="text-2xl font-bold text-white">
                    {sessionStats.sent}
                    {sessionStats.total_messages > 0 && (
                      <span className="text-sm text-slate-400 ml-1">
                        / {sessionStats.total_messages}
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-red-400" />
                <div>
                  <p className="text-sm text-slate-400">Failed</p>
                  <p className="text-2xl font-bold text-white">
                    {sessionStats.failed}
                    {retryCount > 0 && (
                      <span className="text-xs text-yellow-400 ml-1">
                        (R:{retryCount})
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-blue-400" />
                <div>
                  <p className="text-sm text-slate-400">Uptime</p>
                  <p className="text-2xl font-bold text-white">{sessionStats.uptime}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <div className={`h-3 w-3 rounded-full ${
                  isRunning ? 'bg-green-400' : 
                  isPaused ? 'bg-yellow-400' :
                  sessionStatus === 'error' ? 'bg-red-400' : 'bg-gray-400'
                }`} />
                <div>
                  <p className="text-sm text-slate-400">Status</p>
                  <p className="text-lg font-semibold text-white capitalize">
                    {sessionStatus}
                    {isTyping && <Loader className="h-3 w-3 inline ml-1 animate-spin" />}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Current Activity Display */}
        {(sessionStatus === 'running' || sessionStatus === 'paused') && (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-medium">Current Activity</h3>
                  {isTyping && (
                    <Badge className="bg-blue-600">
                      <Loader className="h-3 w-3 mr-1 animate-spin" />
                      Typing...
                    </Badge>
                  )}
                </div>
                
                <div className="space-y-2">
                  <div className="text-sm text-slate-400">
                    Message {sessionStats.current_message_index + 1}: 
                  </div>
                  <div className="text-white p-2 bg-slate-700/50 rounded">
                    {sessionStats.current_message || 'Waiting...'}
                  </div>
                  
                  {isTyping && sessionStats.typing_progress > 0 && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-slate-400">
                        <span>Typing Progress</span>
                        <span>{Math.round(sessionStats.typing_progress)}%</span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-200"
                          style={{ width: `${sessionStats.typing_progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error Panel */}
        {lastError && (
          <Card className="bg-red-900/20 border-red-700">
            <CardContent className="p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-red-400 font-medium">Last Error</h3>
                  <p className="text-red-300 text-sm mt-1">{lastError}</p>
                </div>
                {canResume && (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setShowRetryPanel(true)}
                    className="bg-red-600/20 border-red-600 text-red-400 hover:bg-red-600/30"
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Retry Options
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Retry Panel */}
        {showRetryPanel && (
          <Card className="bg-yellow-900/20 border-yellow-700">
            <CardContent className="p-4">
              <div className="space-y-3">
                <h3 className="text-yellow-400 font-medium flex items-center">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry Options
                </h3>
                
                <div className="flex space-x-3">
                  <Button 
                    onClick={retryFailedMessages}
                    className="bg-yellow-600/20 border-yellow-600 text-yellow-400 hover:bg-yellow-600/30"
                    variant="outline"
                  >
                    Retry Failed Messages ({failedMessages.length})
                  </Button>
                  
                  {canResume && (
                    <Button 
                      onClick={resumeSession}
                      className="bg-green-600/20 border-green-600 text-green-400 hover:bg-green-600/30"
                      variant="outline"
                    >
                      Resume Session
                    </Button>
                  )}
                  
                  <Button 
                    onClick={() => setShowRetryPanel(false)}
                    variant="ghost"
                    className="text-slate-400 hover:text-white"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-2">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Settings className="h-5 w-5" />
                  <span>Configuration</span>
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Setup your auto-typing session
                  {(customChannelId || selectedChannel) && (
                    <div className="mt-2 p-2 bg-slate-700/50 rounded text-sm">
                      <span className="text-slate-300">Target Channel: </span>
                      <span className="text-white font-medium">
                        {customChannelId ? 
                          (extractChannelId(customChannelId) || customChannelId) : 
                          `#${mockData.channels.find(c => c.id === selectedChannel)?.name || selectedChannel}`
                        }
                      </span>
                    </div>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Messages Section */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-white">Messages to Send</Label>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={addMessage}
                      className="bg-slate-700 border-slate-600 text-white hover:bg-slate-600"
                      disabled={!canStart}
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Add Message
                    </Button>
                  </div>
                  
                  {messageList.map((message, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <Textarea
                        placeholder={`Message ${index + 1}...`}
                        value={message}
                        onChange={(e) => updateMessage(index, e.target.value)}
                        className="bg-slate-700 border-slate-600 text-white placeholder-slate-400"
                        rows={2}
                        disabled={!canStart}
                      />
                      {messageList.length > 1 && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeMessage(index)}
                          className="bg-red-900/50 border-red-700 text-red-400 hover:bg-red-800/50"
                          disabled={!canStart}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Channel Selection */}
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-white">Discord Channel (Sample Channels)</Label>
                    <select 
                      value={selectedChannel} 
                      onChange={(e) => setSelectedChannel(e.target.value)}
                      className="w-full bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2"
                      disabled={!canStart}
                    >
                      <option value="">Select a channel...</option>
                      
                      {/* Custom Channels */}
                      {customChannels.length > 0 && (
                        <optgroup label="📌 Your Custom Channels">
                          {customChannels.map((channel) => (
                            <option key={channel.id} value={channel.id}>
                              #{channel.name} - ID: {channel.id}
                            </option>
                          ))}
                        </optgroup>
                      )}
                      
                      {/* Sample Channels */}
                      <optgroup label="📋 Sample Channels">
                        {mockData.channels.map((channel) => (
                          <option key={channel.id} value={channel.id}>
                            #{channel.name} ({channel.server})
                          </option>
                        ))}
                      </optgroup>
                    </select>
                    <p className="text-xs text-slate-400">
                      Ini adalah contoh channel. Gunakan input di bawah untuk channel sesungguhnya.
                    </p>
                  </div>

                  <div className="border-t border-slate-600 pt-4">
                    <div className="space-y-2">
                      <Label className="text-white font-medium">🎯 Custom Discord Channel</Label>
                      <div className="flex space-x-2">
                        <Input
                          placeholder="Masukkan Channel ID atau URL Discord..."
                          value={customChannelId}
                          onChange={(e) => setCustomChannelId(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              addCustomChannel();
                            }
                          }}
                          className="bg-slate-700 border border-slate-600 text-white placeholder-slate-400 flex-1"
                          disabled={!canStart}
                        />
                        <Button
                          type="button"
                          onClick={addCustomChannel}
                          variant="outline"
                          className="bg-blue-600/20 border-blue-600 text-blue-400 hover:bg-blue-600/30"
                          disabled={!canStart}
                        >
                          Add
                        </Button>
                      </div>
                      <div className="bg-slate-700/30 border border-slate-600 rounded-lg p-3">
                        <h4 className="text-white font-medium mb-2">💡 Cara mendapatkan Channel ID:</h4>
                        <ul className="text-sm text-slate-300 space-y-1">
                          <li>• Buka Discord → Settings → Advanced → Enable "Developer Mode"</li>
                          <li>• Klik kanan pada channel → "Copy Channel ID"</li>
                          <li>• Atau salin URL channel: discord.com/channels/SERVER_ID/CHANNEL_ID</li>
                          <li>• Contoh ID: 123456789012345678</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Timing Settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-white">Typing Delay (ms)</Label>
                    <Input
                      type="number"
                      value={typingDelay}
                      onChange={(e) => setTypingDelay(Number(e.target.value))}
                      className="bg-slate-700 border-slate-600 text-white"
                      disabled={!canStart}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-white">Message Delay (ms)</Label>
                    <Input
                      type="number"
                      value={messageDelay}
                      onChange={(e) => setMessageDelay(Number(e.target.value))}
                      className="bg-slate-700 border-slate-600 text-white"
                      disabled={!canStart}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Enhanced Control Panel */}
          <div className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Control Panel</CardTitle>
                <CardDescription className="text-slate-400">
                  Real-time session control
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col space-y-2">
                  <Button 
                    onClick={startSession}
                    disabled={!canStart}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Start Session
                  </Button>
                  
                  <Button 
                    onClick={pauseSession}
                    disabled={!canPause}
                    variant="outline"
                    className="bg-yellow-600/20 border-yellow-600 text-yellow-400 hover:bg-yellow-600/30"
                  >
                    <Pause className="h-4 w-4 mr-2" />
                    Pause
                  </Button>
                  
                  <Button 
                    onClick={resumeSession}
                    disabled={!isPaused && !canResume}
                    variant="outline"
                    className="bg-blue-600/20 border-blue-600 text-blue-400 hover:bg-blue-600/30"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Resume
                  </Button>
                  
                  <Button 
                    onClick={stopSession}
                    disabled={!canStop}
                    variant="outline"
                    className="bg-red-600/20 border-red-600 text-red-400 hover:bg-red-600/30"
                  >
                    <Square className="h-4 w-4 mr-2" />
                    Stop
                  </Button>
                </div>
                
                {/* Session Progress */}
                {sessionStats.total_messages > 0 && (
                  <div className="space-y-2">
                    <Label className="text-white text-sm">Session Progress</Label>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-blue-600 to-green-600 h-2 rounded-full transition-all duration-300"
                        style={{ 
                          width: `${(sessionStats.sent / sessionStats.total_messages) * 100}%` 
                        }}
                      />
                    </div>
                    <p className="text-xs text-slate-400">
                      {sessionStats.sent} / {sessionStats.total_messages} messages
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Session Info */}
            {currentSessionId && (
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white text-sm">Session Info</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Session ID:</span>
                    <span className="text-white font-mono text-xs">{currentSessionId.slice(-8)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">WebSocket:</span>
                    <span className={`font-medium ${
                      connectionStatus === 'Connected' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {connectionStatus}
                    </span>
                  </div>
                  {retryCount > 0 && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">Retries:</span>
                      <span className="text-yellow-400">{retryCount}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Active Sessions (Mock) */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Recent Sessions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {mockData.sessions.map((session) => (
                    <div key={session.id} className="flex items-center justify-between p-2 bg-slate-700/50 rounded">
                      <div className="text-sm">
                        <p className="text-white font-medium">#{session.channel}</p>
                        <p className="text-slate-400">{session.messages} messages</p>
                      </div>
                      <Badge 
                        variant={session.status === 'running' ? 'default' : 'secondary'}
                        className={session.status === 'running' ? 'bg-green-600' : 'bg-slate-600'}
                      >
                        {session.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      <Toaster />
    </div>
  );
};

export default EnhancedDashboard;