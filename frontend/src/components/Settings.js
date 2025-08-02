import React, { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Avatar } from './ui/avatar';
import { ScrollArea } from './ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Separator } from './ui/separator';
import { 
  Users, 
  Building, 
  Plus, 
  Search,
  Edit,
  Trash2,
  Key,
  Save,
  X,
  UserPlus,
  Settings as SettingsIcon,
  Shield,
  Mail
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const Settings = ({ currentUser, onBack }) => {
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showUserForm, setShowUserForm] = useState(false);
  const [showDeptForm, setShowDeptForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingDept, setEditingDept] = useState(null);
  const [formData, setFormData] = useState({});

  // Check if current user is admin
  const isAdmin = currentUser?.role === 'Manager';

  useEffect(() => {
    if (isAdmin) {
      loadData();
    }
  }, [isAdmin]);

  const loadData = async () => {
    try {
      const [usersRes, departmentsRes] = await Promise.all([
        fetch(`${API_BASE}/api/admin/users`),
        fetch(`${API_BASE}/api/departments`)
      ]);

      const usersData = await usersRes.json();
      const departmentsData = await departmentsRes.json();

      setUsers(usersData);
      setDepartments(departmentsData);
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  };

  const handleUserSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingUser 
        ? `${API_BASE}/api/admin/users/${editingUser.id}`
        : `${API_BASE}/api/admin/users`;
      
      const method = editingUser ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        await loadData();
        setShowUserForm(false);
        setEditingUser(null);
        setFormData({});
      } else {
        const error = await response.json();
        alert(error.detail || 'Error saving user');
      }
    } catch (error) {
      console.error('Error saving user:', error);
      alert('Error saving user');
    }
  };

  const handleDeptSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const url = editingDept 
        ? `${API_BASE}/api/admin/departments/${editingDept.id}`
        : `${API_BASE}/api/admin/departments`;
      
      const method = editingDept ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        await loadData();
        setShowDeptForm(false);
        setEditingDept(null);
        setFormData({});
      } else {
        const error = await response.json();
        alert(error.detail || 'Error saving department');
      }
    } catch (error) {
      console.error('Error saving department:', error);
      alert('Error saving department');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Tem certeza que deseja excluir este usuário?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadData();
      } else {
        const error = await response.json();
        alert(error.detail || 'Error deleting user');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Error deleting user');
    }
  };

  const handleToggleDept = async (deptId) => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/departments/${deptId}/toggle`, {
        method: 'POST'
      });

      if (response.ok) {
        await loadData();
      } else {
        const error = await response.json();
        alert(error.detail || 'Error toggling department status');
      }
    } catch (error) {
      console.error('Error toggling department:', error);
      alert('Error toggling department status');
    }
  };

  const handleDeleteDept = async (deptId) => {
    if (!confirm('Tem certeza que deseja excluir este departamento?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/admin/departments/${deptId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadData();
      } else {
        const error = await response.json();
        alert(error.detail || 'Error deleting department');
      }
    } catch (error) {
      console.error('Error deleting department:', error);
      alert('Error deleting department');
    }
  };

  const handleResetPassword = async (userId) => {
    if (!confirm('Tem certeza que deseja resetar a senha deste usuário?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/admin/users/${userId}/reset-password`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Senha resetada! Nova senha temporária: ${result.temp_password}`);
      } else {
        const error = await response.json();
        alert(error.detail || 'Error resetting password');
      }
    } catch (error) {
      console.error('Error resetting password:', error);
      alert('Error resetting password');
    }
  };

  const startEditUser = (user = null) => {
    setEditingUser(user);
    setFormData(user ? {
      name: user.name,
      email: user.email,
      role: user.role,
      department_id: user.department_id || '',
      password: ''
    } : {
      name: '',
      email: '',
      role: 'Agent',
      department_id: '',
      password: ''
    });
    setShowUserForm(true);
  };

  const startEditDept = (dept = null) => {
    setEditingDept(dept);
    setFormData(dept ? {
      name: dept.name,
      description: dept.description,
      active: dept.active,
      business_hours: dept.business_hours || { start: '09:00', end: '17:00' }
    } : {
      name: '',
      description: '',
      active: true,
      business_hours: { start: '09:00', end: '17:00' }
    });
    setShowDeptForm(true);
  };

  const getRoleColor = (role) => {
    const colors = {
      'Manager': 'bg-red-100 text-red-800',
      'Coordinator': 'bg-purple-100 text-purple-800',
      'Sales Rep': 'bg-green-100 text-green-800',
      'Receptionist': 'bg-blue-100 text-blue-800',
      'Agent': 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  const filteredUsers = users.filter(user => 
    user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.role?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Shield className="w-16 h-16 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">Acesso Negado</h3>
          <p className="text-slate-500">Você precisa de permissões de administrador para acessar as configurações.</p>
          <Button onClick={onBack} className="mt-4">
            Voltar ao Inbox
          </Button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Carregando configurações...</p>
        </div>
      </div>
    );
  }

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
              <div className="w-10 h-10 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
                <SettingsIcon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Configurações</h1>
                <p className="text-sm text-slate-500">Gerenciar usuários e departamentos</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-900">{currentUser.name}</p>
              <p className="text-xs text-slate-500">Administrador</p>
            </div>
            <Avatar className="w-8 h-8">
              <img src={currentUser.avatar} alt={currentUser.name} className="rounded-full" />
            </Avatar>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6">
        <Tabs defaultValue="users" className="h-full">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="users" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Usuários</span>
            </TabsTrigger>
            <TabsTrigger value="departments" className="flex items-center space-x-2">
              <Building className="w-4 h-4" />
              <span>Departamentos</span>
            </TabsTrigger>
          </TabsList>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Buscar usuários..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button onClick={() => startEditUser()} className="bg-blue-600 hover:bg-blue-700">
                <UserPlus className="w-4 h-4 mr-2" />
                Novo Usuário
              </Button>
            </div>

            <Card className="overflow-hidden">
              <ScrollArea className="h-96">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-50 border-b">
                      <tr>
                        <th className="text-left p-4 text-sm font-medium text-slate-700">Usuário</th>
                        <th className="text-left p-4 text-sm font-medium text-slate-700">Email</th>
                        <th className="text-left p-4 text-sm font-medium text-slate-700">Cargo</th>
                        <th className="text-left p-4 text-sm font-medium text-slate-700">Departamento</th>
                        <th className="text-left p-4 text-sm font-medium text-slate-700">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredUsers.map((user) => (
                        <tr key={user.id} className="border-b hover:bg-slate-50">
                          <td className="p-4">
                            <div className="flex items-center space-x-3">
                              <Avatar className="w-8 h-8">
                                <img src={user.avatar} alt={user.name} className="rounded-full" />
                              </Avatar>
                              <div>
                                <p className="font-medium text-slate-900">{user.name}</p>
                              </div>
                            </div>
                          </td>
                          <td className="p-4 text-slate-600">{user.email}</td>
                          <td className="p-4">
                            <Badge className={getRoleColor(user.role)}>
                              {user.role}
                            </Badge>
                          </td>
                          <td className="p-4 text-slate-600">
                            {user.department?.name || 'Nenhum'}
                          </td>
                          <td className="p-4">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => startEditUser(user)}
                              >
                                <Edit className="w-3 h-3" />
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleResetPassword(user.id)}
                              >
                                <Key className="w-3 h-3" />
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDeleteUser(user.id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </ScrollArea>
            </Card>
          </TabsContent>

          {/* Departments Tab */}
          <TabsContent value="departments" className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-slate-900">Departamentos</h3>
              <Button onClick={() => startEditDept()} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Novo Departamento
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {departments.map((dept) => (
                <Card key={dept.id} className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-medium text-slate-900">{dept.name}</h4>
                      <p className="text-sm text-slate-500 mt-1">{dept.description}</p>
                    </div>
                    <Badge variant={dept.active ? "default" : "secondary"}>
                      {dept.active ? 'Ativo' : 'Inativo'}
                    </Badge>
                  </div>
                  
                  <div className="text-xs text-slate-500 mb-3">
                    Horário: {dept.business_hours?.start || '09:00'} - {dept.business_hours?.end || '17:00'}
                  </div>

                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => startEditDept(dept)}
                      className="flex-1"
                    >
                      <Edit className="w-3 h-3 mr-1" />
                      Editar
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteDept(dept.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* User Form Modal */}
      {showUserForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md p-6 m-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">
                {editingUser ? 'Editar Usuário' : 'Novo Usuário'}
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowUserForm(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            <form onSubmit={handleUserSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Nome
                </label>
                <Input
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email
                </label>
                <Input
                  type="email"
                  value={formData.email || ''}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Senha {editingUser && '(deixe em branco para manter a atual)'}
                </label>
                <Input
                  type="password"
                  value={formData.password || ''}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required={!editingUser}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Cargo
                </label>
                <select
                  className="w-full p-2 border border-slate-300 rounded-md"
                  value={formData.role || 'Agent'}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  required
                >
                  <option value="Agent">Agente</option>
                  <option value="Receptionist">Recepcionista</option>
                  <option value="Sales Rep">Vendedor</option>
                  <option value="Coordinator">Coordenador</option>
                  <option value="Manager">Gerente</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Departamento
                </label>
                <select
                  className="w-full p-2 border border-slate-300 rounded-md"
                  value={formData.department_id || ''}
                  onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                >
                  <option value="">Nenhum departamento</option>
                  {departments.map(dept => (
                    <option key={dept.id} value={dept.id}>{dept.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex space-x-3 pt-4">
                <Button type="submit" className="flex-1">
                  <Save className="w-4 h-4 mr-2" />
                  {editingUser ? 'Atualizar' : 'Criar'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowUserForm(false)}
                  className="flex-1"
                >
                  <X className="w-4 h-4 mr-2" />
                  Cancelar
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Department Form Modal */}
      {showDeptForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md p-6 m-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">
                {editingDept ? 'Editar Departamento' : 'Novo Departamento'}
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDeptForm(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            <form onSubmit={handleDeptSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Nome
                </label>
                <Input
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Descrição
                </label>
                <Input
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Início
                  </label>
                  <Input
                    type="time"
                    value={formData.business_hours?.start || '09:00'}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      business_hours: { 
                        ...formData.business_hours, 
                        start: e.target.value 
                      }
                    })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Fim
                  </label>
                  <Input
                    type="time"
                    value={formData.business_hours?.end || '17:00'}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      business_hours: { 
                        ...formData.business_hours, 
                        end: e.target.value 
                      }
                    })}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="active"
                  checked={formData.active !== false}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="active" className="text-sm font-medium text-slate-700">
                  Departamento ativo
                </label>
              </div>

              <div className="flex space-x-3 pt-4">
                <Button type="submit" className="flex-1">
                  <Save className="w-4 h-4 mr-2" />
                  {editingDept ? 'Atualizar' : 'Criar'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowDeptForm(false)}
                  className="flex-1"
                >
                  <X className="w-4 h-4 mr-2" />
                  Cancelar
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Settings;