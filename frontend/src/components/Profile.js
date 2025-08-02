import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Avatar } from './ui/avatar';
import { 
  User, 
  Mail, 
  Save, 
  X, 
  Camera, 
  Edit,
  CheckCircle
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const Profile = ({ currentUser, users = [], onBack, onUserUpdate }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    avatar: ''
  });
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState('');

  useEffect(() => {
    if (currentUser) {
      setFormData({
        name: currentUser.name || '',
        email: currentUser.email || '',
        avatar: currentUser.avatar || ''
      });
    }
  }, [currentUser]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    console.log('📝 Profile update - form data:', formData);

    try {
      const token = localStorage.getItem('auth_token');
      console.log('🔑 Profile update - token:', token ? 'Present' : 'Missing');
      
      const response = await fetch(`${API_BASE}/api/users/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      console.log('📡 Profile update - response status:', response.status);

      if (response.ok) {
        const updatedUser = await response.json();
        console.log('✅ Profile update - response data:', updatedUser);
        
        // Update local storage
        localStorage.setItem('user_data', JSON.stringify(updatedUser));
        
        // Update parent component
        if (onUserUpdate) {
          onUserUpdate(updatedUser);
        }
        
        // Update form data with response to ensure sync
        setFormData({
          name: updatedUser.name || '',
          email: updatedUser.email || '',
          avatar: updatedUser.avatar || ''
        });
        
        setNotification('✅ Perfil atualizado com sucesso!');
        setTimeout(() => setNotification(''), 3000);
      } else {
        const error = await response.json();
        console.error('❌ Profile update error:', error);
        setNotification(`❌ Erro: ${error.detail || 'Erro ao atualizar perfil'}`);
        setTimeout(() => setNotification(''), 5000);
      }
    } catch (error) {
      console.error('❌ Profile update exception:', error);
      setNotification('❌ Erro de conexão. Tente novamente.');
      setTimeout(() => setNotification(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // For demo purposes, we'll use a placeholder URL
      // In production, you'd upload to a cloud service
      const reader = new FileReader();
      reader.onload = (event) => {
        setFormData({ ...formData, avatar: event.target.result });
      };
      reader.readAsDataURL(file);
    }
  };

  const predefinedAvatars = [
    "https://images.unsplash.com/photo-1494790108755-2616b7b6ca85?w=150&h=150&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&h=150&fit=crop&crop=face",
    "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&h=150&fit=crop&crop=face"
  ];

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="outline" onClick={onBack}>
              <X className="w-4 h-4 mr-2" />
              Voltar
            </Button>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Meu Perfil</h1>
                <p className="text-sm text-slate-500">Editar informações pessoais</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 flex items-center justify-center">
        <Card className="w-full max-w-2xl p-8">
          {/* Notification */}
          {notification && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6 flex items-center space-x-2 text-blue-700">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              <span className="text-sm">{notification}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Avatar Section */}
            <div className="text-center">
              <div className="relative inline-block">
                <Avatar className="w-24 h-24 mx-auto mb-4">
                  <img 
                    src={formData.avatar || currentUser?.avatar} 
                    alt={formData.name || currentUser?.name} 
                    className="rounded-full w-full h-full object-cover"
                  />
                </Avatar>
                <label className="absolute bottom-0 right-0 bg-blue-600 text-white p-2 rounded-full cursor-pointer hover:bg-blue-700 transition-colors">
                  <Camera className="w-4 h-4" />
                  <input
                    type="file"
                    className="hidden"
                    accept="image/*"
                    onChange={handleAvatarChange}
                  />
                </label>
              </div>
              <h3 className="text-lg font-medium text-slate-900 mb-2">Foto do Perfil</h3>
              <p className="text-sm text-slate-500 mb-4">Clique no ícone da câmera para alterar</p>
              
              {/* Predefined Avatars */}
              <div className="flex justify-center space-x-2 mb-6">
                {predefinedAvatars.map((avatar, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => setFormData({ ...formData, avatar })}
                    className={`w-12 h-12 rounded-full border-2 transition-all ${
                      formData.avatar === avatar 
                        ? 'border-blue-500 ring-2 ring-blue-200' 
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <img 
                      src={avatar} 
                      alt={`Avatar ${index + 1}`} 
                      className="w-full h-full rounded-full object-cover"
                    />
                  </button>
                ))}
              </div>
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  <User className="w-4 h-4 inline mr-2" />
                  Nome Completo
                </label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Digite seu nome completo"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  <Mail className="w-4 h-4 inline mr-2" />
                  Email
                </label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="Digite seu email"
                  required
                />
              </div>
            </div>

            {/* User Info Display */}
            <div className="bg-slate-50 rounded-lg p-4">
              <h4 className="font-medium text-slate-900 mb-3">Informações da Conta</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Cargo:</span>
                  <span className="ml-2 font-medium text-slate-900">{currentUser?.role}</span>
                </div>
                <div>
                  <span className="text-slate-500">Departamento:</span>
                  <span className="ml-2 font-medium text-slate-900">
                    {users.find(u => u.id === currentUser?.id)?.department?.name || 'Nenhum'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">ID do Usuário:</span>
                  <span className="ml-2 font-mono text-xs text-slate-600">{currentUser?.id}</span>
                </div>
                <div>
                  <span className="text-slate-500">Último Login:</span>
                  <span className="ml-2 text-slate-600">Agora</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between pt-6">
              <Button
                type="button"
                variant="outline"
                onClick={onBack}
              >
                <X className="w-4 h-4 mr-2" />
                Cancelar
              </Button>

              <Button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Salvando...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Save className="w-4 h-4" />
                    <span>Salvar Alterações</span>
                  </div>
                )}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default Profile;