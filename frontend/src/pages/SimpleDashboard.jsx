import React, { useState, useEffect, useRef } from 'react';
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
  Trash2
} from 'lucide-react';
import { mockData } from '../utils/mock';

const SimpleDashboard = () => {
  const [messageList, setMessageList] = useState(['']);
  const [selectedChannel, setSelectedChannel] = useState('');
  const [customChannelId, setCustomChannelId] = useState('');
  const [typingDelay, setTypingDelay] = useState(1000);
  const [messageDelay, setMessageDelay] = useState(5000);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stats, setStats] = useState({ sent: 0, failed: 0, uptime: '00:00:00' });
  const [customChannels, setCustomChannels] = useState([]);
  const [sessionStartTime, setSessionStartTime] = useState(null);
  const messageIntervalRef = useRef(null);
  const uptimeIntervalRef = useRef(null);

  useEffect(() => {
    console.log('SimpleDashboard component mounted');
    setSelectedChannel(mockData.channels[0]?.id || '');
    
    // Cleanup intervals on unmount
    return () => {
      if (messageIntervalRef.current) {
        clearInterval(messageIntervalRef.current);
      }
      if (uptimeIntervalRef.current) {
        clearInterval(uptimeIntervalRef.current);
      }
    };
  }, []);

  console.log('SimpleDashboard render - customChannels:', customChannels.length, 'selectedChannel:', selectedChannel);

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

    // Check if already exists
    const exists = customChannels.some(c => c.id === extractedId);
    if (!exists) {
      console.log('Adding custom channel:', newChannel);
      setCustomChannels(prev => {
        const updated = [...prev, newChannel];
        console.log('Updated customChannels:', updated);
        return updated;
      });
      toast({
        title: "Channel Added",
        description: `Custom channel ${extractedId} added to list.`,
      });
    }
    
    setSelectedChannel(extractedId);
    setCustomChannelId('');
  };

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

  // Helper function to extract channel ID from URL
  const extractChannelId = (input) => {
    if (!input) return null;
    
    // If it's already a channel ID (numbers only)
    if (/^\d{17,19}$/.test(input.trim())) {
      return input.trim();
    }
    
    // Extract from Discord URL
    const urlMatch = input.match(/discord\.com\/channels\/\d+\/(\d+)/);
    if (urlMatch) {
      return urlMatch[1];
    }
    
    return null;
  };

  const startSession = async () => {
    const channelId = customChannelId || selectedChannel;
    const extractedId = extractChannelId(channelId);
    
    if (!channelId || messageList.every(msg => !msg.trim())) {
      toast({
        title: "Validation Error",
        description: "Please select a channel/input Channel ID and add at least one message.",
        variant: "destructive"
      });
      return;
    }

    if (customChannelId && !extractedId) {
      toast({
        title: "Invalid Channel ID",
        description: "Please enter a valid Discord Channel ID or URL.",
        variant: "destructive"
      });
      return;
    }

    try {
      // Start real browser automation session
      setIsRunning(true);
      setProgress(0);
      setSessionStartTime(Date.now());
      setStats({ sent: 0, failed: 0, uptime: '00:00:00' });
      
      const channelDisplay = extractedId || selectedChannel;
      
      // Call backend API to start browser automation
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auto-typer/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          channel_id: channelDisplay,
          messages: messageList.filter(msg => msg.trim()),
          typing_delay: typingDelay,
          message_delay: messageDelay
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to start session: ${response.status}`);
      }

      const sessionData = await response.json();
      setSessionStartTime(sessionData.id);  // Store session ID in sessionStartTime for now
      
      toast({
        title: "Browser Session Started",
        description: `Opening Discord in browser for channel: ${channelDisplay}`,
      });

      // Start status polling
      const startTime = Date.now();
      uptimeIntervalRef.current = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        setStats(prev => ({
          ...prev,
          uptime: `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
        }));
      }, 1000);

      // Poll session status from backend
      messageIntervalRef.current = setInterval(async () => {
        try {
          const statusResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auto-typer/${sessionData.id}/status`);
          if (statusResponse.ok) {
            const status = await statusResponse.json();
            setStats(prev => ({
              ...prev,
              sent: status.messages_sent || 0,
              failed: status.messages_failed || 0
            }));
            
            // Update progress based on messages sent
            const totalMessages = messageList.filter(msg => msg.trim()).length;
            if (totalMessages > 0) {
              setProgress((status.messages_sent || 0) * 10); // Show progress
            }
            
            // Handle status changes
            if (status.status === 'error') {
              toast({
                title: "Session Error",
                description: status.error || "An error occurred during automation",
                variant: "destructive"
              });
              stopSession();
            }
          }
        } catch (error) {
          console.error('Error polling session status:', error);
        }
      }, 2000); // Poll every 2 seconds

    } catch (error) {
      console.error('Error starting session:', error);
      toast({
        title: "Error",
        description: "Failed to start browser automation session",
        variant: "destructive"
      });
      setIsRunning(false);
    }
  };

  const stopSession = async () => {
    setIsRunning(false);
    setProgress(0);
    
    // Clear intervals
    if (messageIntervalRef.current) {
      clearInterval(messageIntervalRef.current);
      messageIntervalRef.current = null;
    }
    if (uptimeIntervalRef.current) {
      clearInterval(uptimeIntervalRef.current);
      uptimeIntervalRef.current = null;
    }
    
    // Stop backend session if we have a session ID
    if (sessionStartTime && typeof sessionStartTime === 'string') {
      try {
        await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auto-typer/${sessionStartTime}/stop`, {
          method: 'POST'
        });
      } catch (error) {
        console.error('Error stopping backend session:', error);
      }
    }
    
    setSessionStartTime(null);
    
    toast({
      title: "Session Stopped",
      description: "Browser automation has been stopped.",
    });
    
    // Reset stats after a brief delay to show final count
    setTimeout(() => {
      setStats({ sent: 0, failed: 0, uptime: '00:00:00' });
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-white tracking-tight">
            Discord Auto-Typer
          </h1>
          <p className="text-slate-300 text-lg">
            Browser automation untuk mengirim pesan otomatis di Discord
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <MessageSquare className="h-5 w-5 text-green-400" />
                <div>
                  <p className="text-sm text-slate-400">Messages Sent</p>
                  <p className="text-2xl font-bold text-white">{stats.sent}</p>
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
                  <p className="text-2xl font-bold text-white">{stats.failed}</p>
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
                  <p className="text-2xl font-bold text-white">{stats.uptime}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <div className={`h-3 w-3 rounded-full ${isRunning ? 'bg-green-400' : 'bg-red-400'}`} />
                <div>
                  <p className="text-sm text-slate-400">Status</p>
                  <p className="text-lg font-semibold text-white">
                    {isRunning ? 'Running' : 'Stopped'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

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
                      />
                      {messageList.length > 1 && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeMessage(index)}
                          className="bg-red-900/50 border-red-700 text-red-400 hover:bg-red-800/50"
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
                    >
                      <option value="">Select a channel...</option>
                      
                      {/* Custom Channels */}
                      {(() => {
                        console.log('Rendering dropdown, customChannels:', customChannels);
                        return customChannels.length > 0 && (
                          <optgroup label="📌 Your Custom Channels">
                            {customChannels.map((channel) => (
                              <option key={channel.id} value={channel.id}>
                                #{channel.name} - ID: {channel.id}
                              </option>
                            ))}
                          </optgroup>
                        );
                      })()}
                      
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
                            console.log('Input key pressed:', e.key);
                            if (e.key === 'Enter') {
                              console.log('Enter pressed on input!');
                              e.preventDefault();
                              addCustomChannel();
                            }
                          }}
                          className="bg-slate-700 border border-slate-600 text-white placeholder-slate-400 flex-1"
                        />
                        <Button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            console.log('Add button clicked! customChannelId:', customChannelId);
                            addCustomChannel();
                          }}
                          variant="outline"
                          className="bg-blue-600/20 border-blue-600 text-blue-400 hover:bg-blue-600/30"
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
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-white">Message Delay (ms)</Label>
                    <Input
                      type="number"
                      value={messageDelay}
                      onChange={(e) => setMessageDelay(Number(e.target.value))}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Control Panel */}
          <div className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Control Panel</CardTitle>
                <CardDescription className="text-slate-400">
                  Start or stop your session
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col space-y-2">
                  <Button 
                    onClick={startSession}
                    disabled={isRunning}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Start Session
                  </Button>
                  
                  <Button 
                    onClick={stopSession}
                    disabled={!isRunning && progress === 0}
                    variant="outline"
                    className="bg-red-600/20 border-red-600 text-red-400 hover:bg-red-600/30"
                  >
                    <Square className="h-4 w-4 mr-2" />
                    Stop
                  </Button>
                </div>
                
                {progress > 0 && (
                  <div className="space-y-2">
                    <Label className="text-white text-sm">Session Progress</Label>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-slate-400">{progress}% completed</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Active Sessions */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Active Sessions</CardTitle>
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

export default SimpleDashboard;