import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { Checkbox } from './ui/checkbox';
import { Plus, Edit, Trash2, User, Shield, UserCheck, AlertCircle, CheckCircle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const UserManager = ({ token, onRefresh }) => {
  const [users, setUsers] = useState([]);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    name: '',
    is_admin: false,
    role: 'staff'
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      setError('Failed to fetch users');
    }
  };

  const handleAddUser = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/users`, newUser, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNewUser({
        email: '',
        password: '',
        name: '',
        is_admin: false,
        role: 'staff'
      });
      setShowAddDialog(false);
      setSuccess('User created successfully');
      fetchUsers();
      onRefresh();
    } catch (error) {
      console.error('Error adding user:', error);
      setError(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateUser = async (userId, updatedData) => {
    try {
      setLoading(true);
      await axios.put(`${API}/users/${userId}`, updatedData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEditingUser(null);
      setSuccess('User updated successfully');
      fetchUsers();
      onRefresh();
    } catch (error) {
      console.error('Error updating user:', error);
      setError(error.response?.data?.detail || 'Failed to update user');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await axios.delete(`${API}/users/${userId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSuccess('User deleted successfully');
        fetchUsers();
        onRefresh();
      } catch (error) {
        console.error('Error deleting user:', error);
        setError(error.response?.data?.detail || 'Failed to delete user');
      }
    }
  };

  const getRoleBadge = (role, isAdmin) => {
    if (isAdmin) {
      return (
        <Badge className="bg-red-500 text-white flex items-center gap-1">
          <Shield className="h-3 w-3" />
          Admin
        </Badge>
      );
    }
    
    const roleConfig = {
      'staff': { color: 'bg-blue-500', text: 'Staff', icon: User },
      'manager': { color: 'bg-purple-500', text: 'Manager', icon: UserCheck }
    };
    
    const config = roleConfig[role] || { color: 'bg-gray-500', text: role, icon: User };
    const IconComponent = config.icon;
    
    return (
      <Badge className={`${config.color} text-white flex items-center gap-1`}>
        <IconComponent className="h-3 w-3" />
        {config.text}
      </Badge>
    );
  };

  const clearMessages = () => {
    setError('');
    setSuccess('');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">User Management</h2>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-gold text-black hover:bg-gold/90" onClick={clearMessages}>
              <Plus className="h-4 w-4 mr-2" />
              Add New User
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-gold">Create New User</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label className="text-gold">Email *</Label>
                <Input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="user@example.com"
                />
              </div>
              <div>
                <Label className="text-gold">Password *</Label>
                <Input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser(prev => ({ ...prev, password: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="Enter password"
                />
              </div>
              <div>
                <Label className="text-gold">Full Name</Label>
                <Input
                  value={newUser.name}
                  onChange={(e) => setNewUser(prev => ({ ...prev, name: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="Enter full name"
                />
              </div>
              <div>
                <Label className="text-gold">Role</Label>
                <Select value={newUser.role} onValueChange={(value) => setNewUser(prev => ({ ...prev, role: value }))}>
                  <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-gold/20">
                    <SelectItem value="staff">Staff</SelectItem>
                    <SelectItem value="manager">Manager</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={newUser.is_admin}
                  onCheckedChange={(checked) => setNewUser(prev => ({ ...prev, is_admin: checked }))}
                  className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                />
                <Label className="text-gold">Admin Access</Label>
              </div>
              <div className="flex justify-end space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setShowAddDialog(false)}
                  className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleAddUser}
                  disabled={loading || !newUser.email || !newUser.password}
                  className="bg-gold text-black hover:bg-gold/90"
                >
                  {loading ? 'Creating...' : 'Create User'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <Alert className="border-red-500 bg-red-500/10">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <AlertDescription className="text-red-400">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-500 bg-green-500/10">
          <CheckCircle className="h-4 w-4 text-green-500" />
          <AlertDescription className="text-green-400">{success}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4">
        {users.map((user) => (
          <Card key={user.id} className="bg-gray-900/50 border-gold/20">
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gold">{user.name || 'No Name'}</h3>
                    {getRoleBadge(user.role, user.is_admin)}
                  </div>
                  <p className="text-gray-300">{user.email}</p>
                  <p className="text-gray-400 text-sm">ID: {user.id.substring(0, 8)}...</p>
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingUser(user)}
                    className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteUser(user.id)}
                    className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {users.length === 0 && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardContent className="text-center py-12">
              <User className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-300 mb-2">No users found</h3>
              <p className="text-gray-400">Create the first user to get started</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit User Dialog */}
      {editingUser && (
        <Dialog open={!!editingUser} onOpenChange={() => setEditingUser(null)}>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-md">
            <DialogHeader>
              <DialogTitle className="text-gold">Edit User</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label className="text-gold">Email</Label>
                <Input
                  type="email"
                  value={editingUser.email}
                  onChange={(e) => setEditingUser(prev => ({ ...prev, email: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div>
                <Label className="text-gold">Full Name</Label>
                <Input
                  value={editingUser.name || ''}
                  onChange={(e) => setEditingUser(prev => ({ ...prev, name: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div>
                <Label className="text-gold">New Password (leave blank to keep current)</Label>
                <Input
                  type="password"
                  placeholder="Enter new password"
                  onChange={(e) => setEditingUser(prev => ({ ...prev, password: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div>
                <Label className="text-gold">Role</Label>
                <Select 
                  value={editingUser.role} 
                  onValueChange={(value) => setEditingUser(prev => ({ ...prev, role: value }))}
                >
                  <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-gold/20">
                    <SelectItem value="staff">Staff</SelectItem>
                    <SelectItem value="manager">Manager</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={editingUser.is_admin}
                  onCheckedChange={(checked) => setEditingUser(prev => ({ ...prev, is_admin: checked }))}
                  className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                />
                <Label className="text-gold">Admin Access</Label>
              </div>
              <div className="flex justify-end space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setEditingUser(null)}
                  className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={() => handleUpdateUser(editingUser.id, {
                    email: editingUser.email,
                    name: editingUser.name,
                    role: editingUser.role,
                    is_admin: editingUser.is_admin,
                    ...(editingUser.password && { password: editingUser.password })
                  })}
                  disabled={loading}
                  className="bg-gold text-black hover:bg-gold/90"
                >
                  {loading ? 'Updating...' : 'Update User'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default UserManager;