import React, { useState, useEffect } from 'react';
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
  const [typingDelay, setTypingDelay] = useState(1000);
  const [messageDelay, setMessageDelay] = useState(5000);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stats, setStats] = useState({ sent: 0, failed: 0, uptime: '00:00:00' });

  useEffect(() => {
    setSelectedChannel(mockData.channels[0]?.id || '');
  }, []);

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

  const startSession = () => {
    if (!selectedChannel || messageList.every(msg => !msg.trim())) {
      toast({
        title: "Validation Error",
        description: "Please select a channel and add at least one message.",
        variant: "destructive"
      });
      return;
    }

    setIsRunning(true);
    setProgress(0);
    toast({
      title: "Session Started",
      description: "Discord auto-typer is now running...",
    });
  };

  const stopSession = () => {
    setIsRunning(false);
    setProgress(0);
    setStats({ sent: 0, failed: 0, uptime: '00:00:00' });
    toast({
      title: "Session Stopped",
      description: "Auto-typer has been stopped.",
    });
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
                <div className="space-y-2">
                  <Label className="text-white">Discord Channel</Label>
                  <select 
                    value={selectedChannel} 
                    onChange={(e) => setSelectedChannel(e.target.value)}
                    className="w-full bg-slate-700 border border-slate-600 text-white rounded-md px-3 py-2"
                  >
                    <option value="">Select a channel...</option>
                    {mockData.channels.map((channel) => (
                      <option key={channel.id} value={channel.id}>
                        #{channel.name} ({channel.server})
                      </option>
                    ))}
                  </select>
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