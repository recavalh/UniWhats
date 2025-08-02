import React, { useState, useEffect } from 'react';
import './App.css';
import Settings from './components/Settings';
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
  Settings as SettingsIcon
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentView, setCurrentView] = useState('inbox'); // 'inbox' or 'settings'
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

  useEffect(() => {
    initializeApp();
    setupWebSocket();
  }, []);

  const initializeApp = async () => {
    try {
      // Load initial data
      const [conversationsRes, departmentsRes, usersRes, currentUserRes] = await Promise.all([
        fetch(`${API_BASE}/api/conversations`),
        fetch(`${API_BASE}/api/departments`),
        fetch(`${API_BASE}/api/users`),
        fetch(`${API_BASE}/api/auth/me`)
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
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'new_message') {
          // Refresh conversations and messages
          loadConversations();
          if (selectedConversation && data.conversation_id === selectedConversation.id) {
            loadMessages(selectedConversation.id);
          }
        }
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/conversations`);
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
    await fetch(`${API_BASE}/api/conversations/${conversation.id}/mark-read`, {
      method: 'POST'
    });
  };

  const loadMessages = async (conversationId) => {
    try {
      const response = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages`);
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
          'Content-Type': 'application/json'
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
      await fetch(`${API_BASE}/api/conversations/${selectedConversation.id}/close`, {
        method: 'POST'
      });

      await loadConversations();
    } catch (error) {
      console.error('Error closing conversation:', error);
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

  const filteredConversations = conversations.filter(conv => {
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
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-900">{currentUser.name}</p>
                  <p className="text-xs text-slate-500">{currentUser.role}</p>
                </div>
                <Avatar className="w-8 h-8">
                  <img src={currentUser.avatar} alt={currentUser.name} className="rounded-full" />
                </Avatar>
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
              {departments.map(dept => (
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
              {filteredConversations.map((conversation) => (
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
                        <h2 className="font-semibold text-slate-900">
                          {selectedConversation.contact?.name || 'Contato Desconhecido'}
                        </h2>
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
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.direction === 'out' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                          message.direction === 'out'
                            ? 'bg-blue-600 text-white'
                            : 'bg-white border border-slate-200 text-slate-900'
                        }`}>
                          {message.type === 'image' && message.media_url && (
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

                {/* Message Input */}
                <div className="bg-white border-t border-slate-200 p-4">
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      <Paperclip className="w-4 h-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Smile className="w-4 h-4" />
                    </Button>
                    <Input
                      placeholder="Digite sua mensagem..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                      className="flex-1"
                    />
                    <Button onClick={sendMessage} disabled={!newMessage.trim()}>
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
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

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-700">Tags</label>
                      <div className="flex flex-wrap gap-1">
                        {selectedConversation.contact?.tags?.map(tag => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="actions" className="p-4 space-y-4">
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-slate-700 mb-2 block">
                          Atribuir para Usuário
                        </label>
                        <div className="space-y-2">
                          {users.filter(u => u.department_id === selectedConversation.department_id).map(user => (
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
                          {departments.filter(d => d.id !== selectedConversation.department_id).map(dept => (
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
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full"
                          onClick={closeConversation}
                          disabled={selectedConversation.status === 'closed'}
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Fechar Conversa
                        </Button>
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