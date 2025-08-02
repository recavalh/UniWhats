import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Settings from './components/Settings';
import Profile from './components/Profile';
import MessageComposer from './components/MessageComposer';
import TagManager from './components/TagManager';
import { Card } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Avatar } from './components/ui/avatar';
import { ScrollArea } from './components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Separator } from './components/ui/separator';
import { 
  MessageCircle, 
  User, 
  Phone, 
  Clock, 
  Send, 
  Search,
  Filter,
  Users,
  Tag,
  MoreVertical,
  CheckCircle,
  ArrowRight,
  Paperclip,
  Smile,
  Settings as SettingsIcon,
  LogOut,
  ChevronDown,
  FileText,
  X,
  CheckSquare
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  
  // App state
  const [currentView, setCurrentView] = useState('inbox'); // 'inbox', 'settings', or 'profile'
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [users, setUsers] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  // WebSocket and notifications
  const [wsConnection, setWsConnection] = useState(null);
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  useEffect(() => {
    // Check for existing authentication
    checkExistingAuth();
  }, []);

  useEffect(() => {
    if (isAuthenticated && currentUser) {
      initializeApp();
      setupWebSocket();
    }
  }, [isAuthenticated, currentUser]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showUserDropdown && !event.target.closest('.user-dropdown')) {
        setShowUserDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showUserDropdown]);

  const checkExistingAuth = () => {
    const token = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
      try {
        const user = JSON.parse(userData);
        setAuthToken(token);
        setCurrentUser(user);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
      }
    }
    setAuthLoading(false);
  };

  const handleLogin = (user, token) => {
    setCurrentUser(user);
    setAuthToken(token);
    setIsAuthenticated(true);
    setAuthLoading(false);
  };

  const handleLogout = async () => {
    try {
      // Call logout endpoint
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage and state
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      setIsAuthenticated(false);
      setAuthToken(null);
      setCurrentUser(null);
      setCurrentView('inbox');
      
      // Close WebSocket connection
      if (wsConnection) {
        wsConnection.close();
        setWsConnection(null);
      }
      
      // Reset all app state
      setConversations([]);
      setSelectedConversation(null);
      setMessages([]);
      setUsers([]);
      setDepartments([]);
      setLoading(true);
    }
  };

  const initializeApp = async () => {
    try {
      // Get auth token for API calls
      const token = localStorage.getItem('auth_token');
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Load initial data
      const [conversationsRes, departmentsRes, usersRes, currentUserRes] = await Promise.all([
        fetch(`${API_BASE}/api/conversations`, { headers }),
        fetch(`${API_BASE}/api/departments`, { headers }),
        fetch(`${API_BASE}/api/users`, { headers }),
        fetch(`${API_BASE}/api/auth/me`, { headers })
      ]);

      const [convData, deptData, usersData, userData] = await Promise.all([
        conversationsRes.json(),
        departmentsRes.json(),
        usersRes.json(),
        currentUserRes.json()
      ]);

      setConversations(convData);
      setDepartments(deptData);
      setUsers(usersData);
      setCurrentUser(userData);
      setLoading(false);

      // Select first conversation if exists
      if (convData.length > 0) {
        selectConversation(convData[0]);
      }
    } catch (error) {
      console.error('Error initializing app:', error);
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    // Close existing connection
    if (wsConnection) {
      wsConnection.close();
    }

    // Use backend URL for WebSocket connection
    const backendUrl = new URL(API_BASE);
    const protocol = backendUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${backendUrl.host}/ws`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        setWsConnection(ws);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', data);
          
          if (data.type === 'new_message') {
            // Refresh conversations and messages immediately
            loadConversations();
            if (selectedConversation && data.conversation_id === selectedConversation.id) {
              loadMessages(selectedConversation.id);
            }
            
            // Show notification for incoming messages
            if (data.message?.direction === 'in') {
              showNotification('Nova mensagem recebida!', data.message.body);
            }
          } else if (data.type === 'conversation_updated') {
            // Refresh conversations for assignment/transfer updates
            loadConversations();
          } else if (data.type === 'messages_read') {
            // Update conversation read status
            loadConversations();
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
        }
      };
      
      ws.onclose = (event) => {
        console.log('❌ WebSocket disconnected:', event.code, event.reason);
        setWsConnection(null);
        
        // Attempt to reconnect after 3 seconds if not intentional
        if (event.code !== 1000 && isAuthenticated) {
          setTimeout(() => {
            console.log('🔄 Attempting WebSocket reconnection...');
            setupWebSocket();
          }, 3000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('WebSocket setup failed:', error);
    }
  };

  const showNotification = (title, body) => {
    // Browser notification (if permission granted)
    if (Notification.permission === 'granted') {
      new Notification(title, {
        body: body,
        icon: '/favicon.ico'
      });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          new Notification(title, {
            body: body,
            icon: '/favicon.ico'
          });
        }
      });
    }
  };

  const loadConversations = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/conversations`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      const data = await response.json();
      setConversations(data);
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const selectConversation = async (conversation) => {
    setSelectedConversation(conversation);
    await loadMessages(conversation.id);
    
    // Mark messages as read
    try {
      await fetch(`${API_BASE}/api/conversations/${conversation.id}/mark-read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
    } catch (error) {
      console.error('Error marking messages as read:', error);
    }
  };

  const loadMessages = async (conversationId) => {
    try {
      const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;

    try {
      const response = await fetch(`${API_BASE}/api/conversations/${selectedConversation.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          conversation_id: selectedConversation.id,
          body: newMessage,
          type: 'text'
        })
      });

      if (response.ok) {
        setNewMessage('');
        await loadMessages(selectedConversation.id);
        await loadConversations();
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleSendMessage = async (messageData) => {
    if (!selectedConversation) return;

    try {
      let response;
      
      if (messageData.file) {
        // Handle file upload (image, document, audio)
        const formData = new FormData();
        
        if (messageData.type === 'audio') {
          // Convert audio blob to file
          const file = new File([messageData.file], 'audio.wav', { type: 'audio/wav' });
          formData.append('file', file);
        } else {
          formData.append('file', messageData.file);
        }
        
        formData.append('conversation_id', selectedConversation.id);
        formData.append('body', messageData.body);
        formData.append('type', messageData.type);

        response = await fetch(`${API_BASE}/api/conversations/${selectedConversation.id}/messages/media`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`
          },
          body: formData
        });
      } else {
        // Handle text message
        response = await fetch(`${API_BASE}/api/conversations/${selectedConversation.id}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            conversation_id: selectedConversation.id,
            body: messageData.body,
            type: messageData.type
          })
        });
      }

      if (response.ok) {
        await loadMessages(selectedConversation.id);
        await loadConversations();
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Erro ao enviar mensagem. Tente novamente.');
    }
  };

  const assignConversation = async (assigneeId, departmentId = null) => {
    if (!selectedConversation) return;

    try {
      await fetch(`${API_BASE}/api/conversations/${selectedConversation.id}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          assignee_user_id: assigneeId,
          department_id: departmentId
        })
      });

      await loadConversations();
      // Update selected conversation 
      const updatedConv = conversations.find(c => c.id === selectedConversation.id);
      if (updatedConv) {
        setSelectedConversation(updatedConv);
      }
    } catch (error) {
      console.error('Error assigning conversation:', error);
    }
  };

  const closeConversation = async () => {
    if (!selectedConversation) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/conversations/${selectedConversation.id}/close`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        // Update local state
        setSelectedConversation(prev => prev ? {...prev, status: 'closed'} : null);
        await loadConversations();
        
        // Show success message
        alert('Conversa fechada com sucesso!');
      } else {
        throw new Error('Failed to close conversation');
      }
    } catch (error) {
      console.error('Error closing conversation:', error);
      alert('Erro ao fechar conversa. Tente novamente.');
    }
  };

  const reopenConversation = async () => {
    if (!selectedConversation) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/conversations/${selectedConversation.id}/reopen`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      if (response.ok) {
        // Update local state
        setSelectedConversation(prev => prev ? {...prev, status: 'open'} : null);
        await loadConversations();
        
        // Show success message
        alert('Conversa reaberta com sucesso!');
      } else {
        throw new Error('Failed to reopen conversation');
      }
    } catch (error) {
      console.error('Error reopening conversation:', error);
      alert('Erro ao reabrir conversa. Tente novamente.');
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'agora';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}min`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`;
    return date.toLocaleDateString('pt-BR');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-green-100 text-green-800';
      case 'closed': return 'bg-gray-100 text-gray-800';
      default: return 'bg-blue-100 text-blue-800';
    }
  };

  const getDepartmentColor = (deptId) => {
    const colors = {
      'dept_reception': 'bg-blue-100 text-blue-800',
      'dept_coordination': 'bg-purple-100 text-purple-800',
      'dept_sales': 'bg-green-100 text-green-800',
      'dept_management': 'bg-red-100 text-red-800'
    };
    return colors[deptId] || 'bg-gray-100 text-gray-800';
  };

  const filteredConversations = (conversations || []).filter(conv => {
    if (filter === 'unassigned' && conv.assignee_user_id) return false;
    if (filter === 'mine' && conv.assignee_user_id !== currentUser?.id) return false;
    if (filter !== 'all' && filter !== 'unassigned' && filter !== 'mine' && conv.department_id !== filter) return false;
    
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return conv.contact?.name?.toLowerCase().includes(searchLower) ||
             conv.contact?.phone?.includes(searchTerm) ||
             conv.last_message?.body?.toLowerCase().includes(searchLower);
    }
    
    return true;
  });

  // Show login screen if not authenticated
  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Verificando autenticação...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Carregando UniWhats Desk...</p>
        </div>
      </div>
    );
  }

  const handleUserUpdate = (updatedUser) => {
    setCurrentUser(updatedUser);
  };

  // Show Settings page if selected
  if (currentView === 'settings') {
    return (
      <Settings 
        currentUser={currentUser} 
        onBack={() => setCurrentView('inbox')} 
      />
    );
  }

  // Show Profile page if selected
  if (currentView === 'profile') {
    return (
      <Profile 
        currentUser={currentUser}
        users={users}
        onBack={() => setCurrentView('inbox')}
        onUserUpdate={handleUserUpdate}
      />
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">UniWhats Desk</h1>
                <p className="text-sm text-slate-500">Team Inbox for Schools</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-slate-600">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Online</span>
            </div>
            
            {currentUser && (
              <div className="flex items-center space-x-3">
                {/* WebSocket connection status */}
                <div className="flex items-center space-x-2 text-sm text-slate-600">
                  <div className={`w-2 h-2 rounded-full ${wsConnection ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span>{wsConnection ? 'Conectado' : 'Desconectado'}</span>
                </div>
                
                {/* Settings button for Admin users */}
                {currentUser.role === 'Manager' && (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setCurrentView('settings')}
                    className="flex items-center space-x-2"
                  >
                    <SettingsIcon className="w-4 h-4" />
                    <span>Configurações</span>
                  </Button>
                )}
                
                {/* User dropdown */}
                <div className="relative user-dropdown">
                  <button
                    onClick={() => setShowUserDropdown(!showUserDropdown)}
                    className="flex items-center space-x-3 p-2 rounded-lg hover:bg-slate-100 transition-colors"
                  >
                    <div className="text-right">
                      <p className="text-sm font-medium text-slate-900">{currentUser.name}</p>
                      <p className="text-xs text-slate-500">{currentUser.role}</p>
                    </div>
                    <Avatar className="w-8 h-8">
                      <img src={currentUser.avatar} alt={currentUser.name} className="rounded-full" />
                    </Avatar>
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  </button>
                  
                  {/* Dropdown menu */}
                  {showUserDropdown && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50">
                      <div className="px-4 py-2 border-b border-slate-200">
                        <p className="font-medium text-slate-900">{currentUser.name}</p>
                        <p className="text-sm text-slate-500">{currentUser.email}</p>
                      </div>
                      
                      <button
                        onClick={() => {
                          setShowUserDropdown(false);
                          setCurrentView('profile');
                        }}
                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 flex items-center space-x-2"
                      >
                        <User className="w-4 h-4" />
                        <span>Perfil</span>
                      </button>
                      
                      <div className="border-t border-slate-200 mt-1 pt-1">
                        <button
                          onClick={() => {
                            setShowUserDropdown(false);
                            handleLogout();
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
                        >
                          <LogOut className="w-4 h-4" />
                          <span>Sair</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Conversations Sidebar */}
        <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
          {/* Search and Filters */}
          <div className="p-4 border-b border-slate-200">
            <div className="relative mb-3">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Buscar conversas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex space-x-2 overflow-x-auto pb-2">
              <Button 
                variant={filter === 'all' ? 'default' : 'outline'} 
                size="sm"
                onClick={() => setFilter('all')}
              >
                Todas
              </Button>
              <Button 
                variant={filter === 'unassigned' ? 'default' : 'outline'} 
                size="sm"
                onClick={() => setFilter('unassigned')}
              >
                Não Atribuídas
              </Button>
              <Button 
                variant={filter === 'mine' ? 'default' : 'outline'} 
                size="sm"
                onClick={() => setFilter('mine')}
              >
                Minhas
              </Button>
              {(departments || []).map(dept => (
                <Button 
                  key={dept.id}
                  variant={filter === dept.id ? 'default' : 'outline'} 
                  size="sm"
                  onClick={() => setFilter(dept.id)}
                >
                  {dept.name}
                </Button>
              ))}
            </div>
          </div>

          {/* Conversations List */}
          <ScrollArea className="flex-1">
            <div className="p-2">
              {(filteredConversations || []).map((conversation) => (
                <Card 
                  key={conversation.id}
                  className={`p-3 mb-2 cursor-pointer transition-all hover:shadow-md ${
                    selectedConversation?.id === conversation.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                  onClick={() => selectConversation(conversation)}
                >
                  <div className="flex items-start space-x-3">
                    <Avatar className="w-10 h-10 flex-shrink-0">
                      <div className="w-full h-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-medium">
                        {conversation.contact?.name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                    </Avatar>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium text-slate-900 truncate">
                          {conversation.contact?.name || 'Contato Desconhecido'}
                        </h4>
                        <span className="text-xs text-slate-500 flex-shrink-0">
                          {formatTime(conversation.last_message_at)}
                        </span>
                      </div>
                      
                      <p className="text-sm text-slate-600 truncate mb-2">
                        {conversation.last_message?.body || 'Nenhuma mensagem'}
                      </p>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1">
                          <Badge 
                            variant="secondary" 
                            className={`text-xs ${getDepartmentColor(conversation.department_id)}`}
                          >
                            {conversation.department?.name || 'Departamento'}
                          </Badge>
                          
                          {conversation.unread_count > 0 && (
                            <Badge variant="destructive" className="text-xs">
                              {conversation.unread_count}
                            </Badge>
                          )}
                        </div>
                        
                        {conversation.assignee && (
                          <div className="flex items-center space-x-1">
                            <Avatar className="w-5 h-5">
                              <img src={conversation.assignee.avatar} alt="" className="rounded-full" />
                            </Avatar>
                          </div>
                        )}
                      </div>
                      
                      {conversation.tags?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {conversation.tags.map(tag => (
                            <Badge key={tag} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex">
          {selectedConversation ? (
            <>
              {/* Messages Area */}
              <div className="flex-1 flex flex-col">
                {/* Conversation Header */}
                <div className="bg-white border-b border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Avatar className="w-10 h-10">
                        <div className="w-full h-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-medium">
                          {selectedConversation.contact?.name?.charAt(0)?.toUpperCase() || '?'}
                        </div>
                      </Avatar>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h2 className="font-semibold text-slate-900">
                            {selectedConversation.contact?.name || 'Contato Desconhecido'}
                          </h2>
                          {selectedConversation.status === 'closed' && (
                            <Badge variant="outline" className="text-xs bg-red-50 text-red-700 border-red-200">
                              Fechada
                            </Badge>
                          )}
                          {selectedConversation.status === 'open' && (
                            <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                              Aberta
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-500">
                          {selectedConversation.contact?.phone}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Badge className={`${getStatusColor(selectedConversation.status)}`}>
                        {selectedConversation.status === 'open' ? 'Aberto' : 'Fechado'}
                      </Badge>
                      <Badge className={`${getDepartmentColor(selectedConversation.department_id)}`}>
                        {selectedConversation.department?.name}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <ScrollArea className="flex-1 p-4">
                  <div className="space-y-4">
                    {(messages || []).map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.direction === 'out' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                          message.direction === 'out'
                            ? 'bg-blue-600 text-white'
                            : 'bg-white border border-slate-200 text-slate-900'
                        }`}>
                          {/* Image Message */}
                          {message.type === 'image' && message.media && (
                            <img 
                              src={`data:${message.media.content_type};base64,${message.media.data}`} 
                              alt={message.media.filename || "Imagem"} 
                              className="rounded-lg mb-2 max-w-full cursor-pointer hover:opacity-90"
                              onClick={() => window.open(`data:${message.media.content_type};base64,${message.media.data}`, '_blank')}
                            />
                          )}
                          
                          {/* Audio Message */}
                          {message.type === 'audio' && message.media && (
                            <div className="mb-2">
                              <audio 
                                controls 
                                className="w-full"
                                src={`data:${message.media.content_type};base64,${message.media.data}`}
                              >
                                Seu navegador não suporta o elemento de áudio.
                              </audio>
                            </div>
                          )}
                          
                          {/* Document Message */}
                          {message.type === 'document' && message.media && (
                            <div className="flex items-center mb-2 p-2 bg-slate-100 rounded-lg">
                              <FileText className="w-6 h-6 text-blue-600 mr-3" />
                              <div className="flex-1">
                                <p className="text-sm font-medium">{message.media.filename}</p>
                                <p className="text-xs text-slate-500">
                                  {(message.media.size / 1024 / 1024).toFixed(2)} MB
                                </p>
                              </div>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  const link = document.createElement('a');
                                  link.href = `data:${message.media.content_type};base64,${message.media.data}`;
                                  link.download = message.media.filename;
                                  link.click();
                                }}
                              >
                                Download
                              </Button>
                            </div>
                          )}
                          
                          {/* Legacy image support */}
                          {message.type === 'image' && message.media_url && !message.media && (
                            <img 
                              src={message.media_url} 
                              alt="Imagem" 
                              className="rounded-lg mb-2 max-w-full"
                            />
                          )}
                          
                          <p className="text-sm">{message.body}</p>
                          <div className={`flex items-center justify-between mt-1 text-xs ${
                            message.direction === 'out' ? 'text-blue-100' : 'text-slate-500'
                          }`}>
                            <span>{formatTime(message.timestamp)}</span>
                            {message.sender && (
                              <span className="ml-2">{message.sender.name}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>

                {/* Message Composer */}
                <MessageComposer 
                  onSendMessage={handleSendMessage}
                  disabled={!selectedConversation}
                />
              </div>

              {/* Right Sidebar - Contact Info */}
              <div className="w-80 bg-white border-l border-slate-200">
                <Tabs defaultValue="contact" className="h-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="contact">Contato</TabsTrigger>
                    <TabsTrigger value="actions">Ações</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="contact" className="p-4 space-y-4">
                    <div className="text-center">
                      <Avatar className="w-20 h-20 mx-auto mb-4">
                        <div className="w-full h-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-2xl font-medium">
                          {selectedConversation.contact?.name?.charAt(0)?.toUpperCase() || '?'}
                        </div>
                      </Avatar>
                      <h3 className="font-semibold text-slate-900">
                        {selectedConversation.contact?.name || 'Contato Desconhecido'}
                      </h3>
                      <p className="text-sm text-slate-500">
                        {selectedConversation.contact?.phone}
                      </p>
                    </div>

                    <Separator />

                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-slate-700">WhatsApp ID</label>
                        <p className="text-sm text-slate-600">{selectedConversation.contact?.wa_id}</p>
                      </div>
                      
                      {selectedConversation.contact?.student_id && (
                        <div>
                          <label className="text-sm font-medium text-slate-700">ID do Estudante</label>
                          <p className="text-sm text-slate-600">{selectedConversation.contact.student_id}</p>
                        </div>
                      )}
                      
                      {selectedConversation.contact?.custom_fields?.student_name && (
                        <div>
                          <label className="text-sm font-medium text-slate-700">Nome do Estudante</label>
                          <p className="text-sm text-slate-600">{selectedConversation.contact.custom_fields.student_name}</p>
                        </div>
                      )}
                      
                      {selectedConversation.contact?.custom_fields?.grade && (
                        <div>
                          <label className="text-sm font-medium text-slate-700">Série</label>
                          <p className="text-sm text-slate-600">{selectedConversation.contact.custom_fields.grade}</p>
                        </div>
                      )}
                    </div>

                    <Separator />

                    {/* Tag Manager */}
                    <TagManager 
                      conversationId={selectedConversation?.id}
                      currentTags={selectedConversation?.tags || []}
                      onTagsUpdate={(newTags) => {
                        // Update local state
                        setSelectedConversation(prev => prev ? {...prev, tags: newTags} : null);
                        // Refresh conversations list
                        loadConversations();
                      }}
                    />
                  </TabsContent>
                  
                  <TabsContent value="actions" className="p-4 space-y-4">
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-slate-700 mb-2 block">
                          Atribuir para Usuário
                        </label>
                        <div className="space-y-2">
                          {(users || []).filter(u => u.department_id === selectedConversation.department_id).map(user => (
                            <Button
                              key={user.id}
                              variant="outline"
                              size="sm"
                              className="w-full justify-start"
                              onClick={() => assignConversation(user.id)}
                            >
                              <Avatar className="w-5 h-5 mr-2">
                                <img src={user.avatar} alt="" className="rounded-full" />
                              </Avatar>
                              {user.name}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <Separator />

                      <div>
                        <label className="text-sm font-medium text-slate-700 mb-2 block">
                          Transferir para Departamento
                        </label>
                        <div className="space-y-2">
                          {(departments || []).filter(d => d.id !== selectedConversation.department_id).map(dept => (
                            <Button
                              key={dept.id}
                              variant="outline"
                              size="sm"
                              className="w-full justify-start"
                              onClick={() => assignConversation(null, dept.id)}
                            >
                              <ArrowRight className="w-4 h-4 mr-2" />
                              {dept.name}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <Separator />

                      <div className="space-y-2">
                        {selectedConversation.status === 'closed' ? (
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full border-green-200 text-green-700 hover:bg-green-50"
                            onClick={reopenConversation}
                          >
                            <CheckSquare className="w-4 h-4 mr-2" />
                            Reabrir Conversa
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full border-red-200 text-red-700 hover:bg-red-50"
                            onClick={closeConversation}
                          >
                            <X className="w-4 h-4 mr-2" />
                            Fechar Conversa
                          </Button>
                        )}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </>
          ) : (
            /* No Conversation Selected */
            <div className="flex-1 flex items-center justify-center bg-slate-50">
              <div className="text-center">
                <MessageCircle className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  Selecione uma conversa
                </h3>
                <p className="text-slate-500">
                  Escolha uma conversa na barra lateral para começar
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;