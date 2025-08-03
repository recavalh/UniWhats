import React, { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { 
  MessageCircle, 
  Mail, 
  Lock, 
  Eye, 
  EyeOff,
  LogIn,
  AlertCircle
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const Login = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        // Store token and user data
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('user_data', JSON.stringify(data.user));
        
        // Call parent component's login handler
        onLogin(data.user, data.token);
      } else {
        setError(data.detail || 'Credenciais inválidas');
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Erro de conexão. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!formData.email) {
      setError('Digite seu email para resetar a senha');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: formData.email })
      });

      if (response.ok) {
        alert('Email de recuperação enviado! Verifique sua caixa de entrada.');
      } else {
        const data = await response.json();
        setError(data.detail || 'Erro ao enviar email de recuperação');
      }
    } catch (error) {
      console.error('Forgot password error:', error);
      setError('Erro de conexão. Tente novamente.');
    }
  };

  // Quick login buttons for demo purposes
  const quickLogin = (email, role) => {
    setFormData({ email, password: 'admin123' });
    // Auto-submit after setting data
    setTimeout(() => {
      document.getElementById('login-form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }, 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">UniWhats Desk</h1>
              <p className="text-sm text-slate-500">Team Inbox for Schools</p>
            </div>
          </div>
          <p className="text-slate-600">Entre na sua conta para continuar</p>
        </div>

        {/* Login Form */}
        <Card className="p-6 shadow-lg">
          <form id="login-form" onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center space-x-2 text-red-700">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <Input
                  type="email"
                  placeholder="seu@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-10 pr-10"
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-slate-600">Lembrar-me</span>
              </label>

              <button
                type="button"
                onClick={handleForgotPassword}
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                Esqueceu a senha?
              </button>
            </div>

            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Entrando...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <LogIn className="w-4 h-4" />
                  <span>Entrar</span>
                </div>
              )}
            </Button>
          </form>
        </Card>

        {/* Demo Login Buttons */}
        <div className="mt-6 space-y-2">
          <p className="text-center text-sm text-slate-500 mb-3">Demo - Login rápido:</p>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => quickLogin('admin@school.com', 'Manager')}
              className="text-xs"
            >
              👨‍💼 Gerente
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => quickLogin('maria@school.com', 'Receptionist')}
              className="text-xs"
            >
              📞 Recepção
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => quickLogin('carlos@school.com', 'Coordinator')}
              className="text-xs"
            >
              📚 Coordenador
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => quickLogin('ana@school.com', 'Sales Rep')}
              className="text-xs"
            >
              💼 Vendas
            </Button>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-slate-500">
          <p>© 2025 UniWhats Desk. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;