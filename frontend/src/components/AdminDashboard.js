import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Calendar, Users, Settings, LogOut, User, Scissors, Clock, Mail, Phone, Plus, Edit, Trash2, Save, X, Upload, Image, FileText, CreditCard, Globe, TrendingUp, Coffee } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { Separator } from './ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { format } from 'date-fns';
import axios from 'axios';
import EnhancedBookingManager from './EnhancedBookingManager';
import ContentManager from './ContentManager';
import UserManager from './UserManager';
import GalleryManager from './GalleryManager';
import RevenueDashboard from './RevenueDashboard';
import BreakManager from './BreakManager';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminLogin = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/login`, credentials);
      
      if (response.data.user.is_admin) {
        localStorage.setItem('admin_token', response.data.access_token);
        localStorage.setItem('admin_user', JSON.stringify(response.data.user));
        onLogin(response.data.access_token, response.data.user);
      } else {
        setError('You do not have admin privileges');
      }
    } catch (error) {
      setError('Login failed. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-gray-900/50 border-gold/20">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Scissors className="h-8 w-8 text-gold mr-3" />
            <h1 className="text-2xl font-bold text-gold font-serif">Frisor LaFata</h1>
          </div>
          <CardTitle className="text-gold">Admin Login</CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert className="border-red-500 bg-red-500/10 mb-4">
              <AlertDescription className="text-red-400">{error}</AlertDescription>
            </Alert>
          )}
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-gold">Email</Label>
              <Input
                id="email"
                type="email"
                value={credentials.email}
                onChange={(e) => setCredentials(prev => ({ ...prev, email: e.target.value }))}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="admin@frisorlafata.dk"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password" className="text-gold">Password</Label>
              <Input
                id="password"
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="••••••••"
                required
              />
            </div>
            
            <Button 
              type="submit" 
              className="w-full bg-gold text-black hover:bg-gold/90"
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Log In'}
            </Button>
          </form>
          
          <div className="mt-4 p-3 bg-gold/10 rounded border border-gold/20">
            <p className="text-xs text-gray-300">
              <strong>Demo Admin:</strong><br/>
              Email: admin@frisorlafata.dk<br/>
              Password: admin123
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const ServiceManager = ({ token, onRefresh }) => {
  const [services, setServices] = useState([]);
  const [editingService, setEditingService] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [newService, setNewService] = useState({
    name: '',
    duration_minutes: 30,
    price: 0,
    description: '',
    category: 'general'
  });

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services`);
      setServices(response.data);
    } catch (error) {
      console.error('Error fetching services:', error);
    }
  };

  const handleAddService = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/services`, newService, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNewService({ name: '', duration_minutes: 30, price: 0, description: '', category: 'general' });
      setShowAddDialog(false);
      fetchServices();
      onRefresh();
    } catch (error) {
      console.error('Error adding service:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateService = async (serviceId, updatedData) => {
    try {
      await axios.put(`${API}/services/${serviceId}`, updatedData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEditingService(null);
      fetchServices();
      onRefresh();
    } catch (error) {
      console.error('Error updating service:', error);
    }
  };

  const handleDeleteService = async (serviceId) => {
    console.log('Delete service clicked:', serviceId);
    if (window.confirm('Are you sure you want to delete this service?')) {
      try {
        console.log('Deleting service with token:', token ? 'Token exists' : 'No token');
        const response = await axios.delete(`${API}/services/${serviceId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Delete response:', response);
        alert('Service deleted successfully!');
        
        // Force refresh the services list
        await fetchServices();
        if (onRefresh) onRefresh();
        
        // Force page refresh if needed
        window.location.reload();
      } catch (error) {
        console.error('Error deleting service:', error);
        console.error('Error response:', error.response?.data);
        alert(`Failed to delete service: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const handleNewServiceChange = (field, value) => {
    setNewService(prev => ({ ...prev, [field]: value }));
  };

  const handleEditServiceChange = (field, value) => {
    setEditingService(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">Service Management</h2>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-gold text-black hover:bg-gold/90">
              <Plus className="h-4 w-4 mr-2" />
              Add New Service
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 border-gold/20">
            <DialogHeader>
              <DialogTitle className="text-gold">Add New Service</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label className="text-gold">Service Name</Label>
                <Input
                  value={newService.name}
                  onChange={(e) => handleNewServiceChange('name', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="e.g., Classic Haircut"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gold">Duration (minutes)</Label>
                  <Input
                    type="number"
                    value={newService.duration_minutes}
                    onChange={(e) => handleNewServiceChange('duration_minutes', parseInt(e.target.value) || 0)}
                    className="bg-black/50 border-gold/30 text-white"
                  />
                </div>
                <div>
                  <Label className="text-gold">Price (DKK)</Label>
                  <Input
                    type="number"
                    value={newService.price}
                    onChange={(e) => handleNewServiceChange('price', parseFloat(e.target.value) || 0)}
                    className="bg-black/50 border-gold/30 text-white"
                  />
                </div>
              </div>
              <div>
                <Label className="text-gold">Category</Label>
                <Select 
                  value={newService.category} 
                  onValueChange={(value) => handleNewServiceChange('category', value)}
                >
                  <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-gold/20">
                    <SelectItem value="haircut">Haircut</SelectItem>
                    <SelectItem value="beard">Beard</SelectItem>
                    <SelectItem value="styling">Styling</SelectItem>
                    <SelectItem value="coloring">Coloring</SelectItem>
                    <SelectItem value="premium">Premium</SelectItem>
                    <SelectItem value="general">General</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-gold">Description</Label>
                <Textarea
                  value={newService.description}
                  onChange={(e) => handleNewServiceChange('description', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="Service description..."
                />
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
                  onClick={handleAddService}
                  disabled={loading}
                  className="bg-gold text-black hover:bg-gold/90"
                >
                  {loading ? 'Adding...' : 'Add Service'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((service) => (
          <Card key={service.id} className="bg-gray-900/50 border-gold/20">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-gold text-lg">{service.name}</CardTitle>
                  <Badge variant="outline" className="border-gold/50 text-gold mt-1">
                    {service.category}
                  </Badge>
                </div>
                <div className="flex space-x-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingService(service)}
                    className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteService(service.id)}
                    className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center text-gray-300">
                  <Clock className="h-4 w-4 mr-2" />
                  {service.duration_minutes} minutes
                </div>
                <div className="text-2xl font-bold text-gold">
                  {service.price} DKK
                </div>
                {service.description && (
                  <p className="text-gray-300 text-sm">{service.description}</p>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Edit Service Dialog */}
      {editingService && (
        <Dialog open={!!editingService} onOpenChange={() => setEditingService(null)}>
          <DialogContent className="bg-gray-900 border-gold/20">
            <DialogHeader>
              <DialogTitle className="text-gold">Edit Service</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label className="text-gold">Service Name</Label>
                <Input
                  value={editingService.name || ''}
                  onChange={(e) => handleEditServiceChange('name', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gold">Duration (minutes)</Label>
                  <Input
                    type="number"
                    value={editingService.duration_minutes || 0}
                    onChange={(e) => handleEditServiceChange('duration_minutes', parseInt(e.target.value) || 0)}
                    className="bg-black/50 border-gold/30 text-white"
                  />
                </div>
                <div>
                  <Label className="text-gold">Price (DKK)</Label>
                  <Input
                    type="number"
                    value={editingService.price || 0}
                    onChange={(e) => handleEditServiceChange('price', parseFloat(e.target.value) || 0)}
                    className="bg-black/50 border-gold/30 text-white"
                  />
                </div>
              </div>
              <div>
                <Label className="text-gold">Category</Label>
                <Select 
                  value={editingService.category || 'general'} 
                  onValueChange={(value) => handleEditServiceChange('category', value)}
                >
                  <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-gold/20">
                    <SelectItem value="haircut">Haircut</SelectItem>
                    <SelectItem value="beard">Beard</SelectItem>
                    <SelectItem value="styling">Styling</SelectItem>
                    <SelectItem value="coloring">Coloring</SelectItem>
                    <SelectItem value="premium">Premium</SelectItem>
                    <SelectItem value="general">General</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-gold">Description</Label>
                <Textarea
                  value={editingService.description || ''}
                  onChange={(e) => handleEditServiceChange('description', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setEditingService(null)}
                  className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={() => handleUpdateService(editingService.id, editingService)}
                  className="bg-gold text-black hover:bg-gold/90"
                >
                  Save Changes
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

const StaffManager = ({ token, onRefresh }) => {
  const [staff, setStaff] = useState([]);
  const [editingStaff, setEditingStaff] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(null);
  const [newStaff, setNewStaff] = useState({
    name: '',
    specialty: '',
    experience: '',
    avatar_url: '',
    available_hours: {
      monday: { start: '09:00', end: '18:00', enabled: true },
      tuesday: { start: '09:00', end: '18:00', enabled: true },
      wednesday: { start: '09:00', end: '18:00', enabled: true },
      thursday: { start: '09:00', end: '18:00', enabled: true },
      friday: { start: '09:00', end: '18:00', enabled: true },
      saturday: { start: '09:00', end: '16:00', enabled: true },
      sunday: { start: '09:00', end: '16:00', enabled: false }
    }
  });

  useEffect(() => {
    fetchStaff();
  }, []);

  const fetchStaff = async () => {
    try {
      const response = await axios.get(`${API}/staff`);
      setStaff(response.data);
    } catch (error) {
      console.error('Error fetching staff:', error);
    }
  };

  const handleAvatarUpload = async (file, isEditing = false) => {
    try {
      setUploadingAvatar(isEditing ? 'editing' : 'new');
      const formData = new FormData();
      formData.append('avatar', file);
      
      const response = await axios.post(`${API}/upload/avatar`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const avatarUrl = response.data.avatar_url;
      console.log('Avatar uploaded successfully:', avatarUrl);
      
      if (isEditing) {
        handleEditStaffChange('avatar_url', avatarUrl);
      } else {
        handleNewStaffChange('avatar_url', avatarUrl);
      }
      
      alert('Avatar uploaded successfully!');
    } catch (error) {
      console.error('Error uploading avatar:', error);
      alert(`Failed to upload avatar: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploadingAvatar(null);
    }
  };

  const handleAddStaff = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/staff`, newStaff, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNewStaff({
        name: '',
        specialty: '',
        experience: '',
        avatar_url: '',
        available_hours: {
          monday: { start: '09:00', end: '18:00', enabled: true },
          tuesday: { start: '09:00', end: '18:00', enabled: true },
          wednesday: { start: '09:00', end: '18:00', enabled: true },
          thursday: { start: '09:00', end: '18:00', enabled: true },
          friday: { start: '09:00', end: '18:00', enabled: true },
          saturday: { start: '09:00', end: '16:00', enabled: true },
          sunday: { start: '09:00', end: '16:00', enabled: false }
        }
      });
      setShowAddDialog(false);
      fetchStaff();
      onRefresh();
    } catch (error) {
      console.error('Error adding staff:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStaff = async (staffId, updatedData) => {
    try {
      await axios.put(`${API}/staff/${staffId}`, updatedData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEditingStaff(null);
      fetchStaff();
      onRefresh();
    } catch (error) {
      console.error('Error updating staff:', error);
    }
  };

  const handleDeleteStaff = async (staffId) => {
    console.log('Delete staff clicked:', staffId);
    if (window.confirm('Are you sure you want to delete this staff member?')) {
      try {
        console.log('Deleting staff with token:', token ? 'Token exists' : 'No token');
        const response = await axios.delete(`${API}/staff/${staffId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('Delete response:', response);
        alert('Staff member deleted successfully!');
        
        // Force refresh the staff list
        await fetchStaff();
        if (onRefresh) onRefresh();
        
        // Force page refresh if needed
        window.location.reload();
      } catch (error) {
        console.error('Error deleting staff:', error);
        console.error('Error response:', error.response?.data);
        alert(`Failed to delete staff member: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const handleNewStaffChange = (field, value) => {
    setNewStaff(prev => ({ ...prev, [field]: value }));
  };

  const handleEditStaffChange = (field, value) => {
    setEditingStaff(prev => ({ ...prev, [field]: value }));
  };

  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
  const dayLabels = {
    monday: 'Monday',
    tuesday: 'Tuesday', 
    wednesday: 'Wednesday',
    thursday: 'Thursday',
    friday: 'Friday',
    saturday: 'Saturday',
    sunday: 'Sunday'
  };

  const StaffForm = ({ staffData, onChange, onSubmit, onCancel, loading, title, isEditing = false }) => {
    const handleFieldChange = (field, value) => {
      onChange({ ...staffData, [field]: value });
    };

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gold">{title}</h3>
        
        {/* Avatar Upload */}
        <div>
          <Label className="text-gold">Avatar</Label>
          <div className="flex items-center space-x-4 mt-2">
            <div className="w-16 h-16 rounded-full border-2 border-gold/30 overflow-hidden bg-gray-800 flex items-center justify-center">
              {staffData.avatar_url ? (
                <img 
                  src={staffData.avatar_url} 
                  alt="Avatar" 
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    console.error('Avatar image failed to load:', staffData.avatar_url);
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : (
                <Users className="h-8 w-8 text-gold" />
              )}
              {staffData.avatar_url && (
                <div className="w-full h-full hidden items-center justify-center">
                  <Users className="h-8 w-8 text-gold" />
                </div>
              )}
            </div>
            <div>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files[0];
                  if (file) {
                    console.log('Avatar file selected:', file.name, file.type);
                    handleAvatarUpload(file, isEditing);
                  }
                }}
                className="hidden"
                id={`avatar-upload-${isEditing ? 'edit' : 'new'}`}
              />
              <label
                htmlFor={`avatar-upload-${isEditing ? 'edit' : 'new'}`}
                className="cursor-pointer inline-flex items-center px-3 py-2 border border-gold/50 rounded-md text-gold hover:bg-gold hover:text-black transition-colors"
              >
                {uploadingAvatar === (isEditing ? 'editing' : 'new') ? (
                  <>Uploading...</>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Avatar
                  </>
                )}
              </label>
              {staffData.avatar_url && (
                <p className="text-xs text-gray-400 mt-1">Current: {staffData.avatar_url.split('/').pop()}</p>
              )}
            </div>
          </div>
        </div>

        <div>
          <Label className="text-gold">Name</Label>
          <Input
            value={staffData.name || ''}
            onChange={(e) => handleFieldChange('name', e.target.value)}
            className="bg-black/50 border-gold/30 text-white"
            placeholder="Staff member name"
          />
        </div>
        <div>
          <Label className="text-gold">Specialty</Label>
          <Input
            value={staffData.specialty || ''}
            onChange={(e) => handleFieldChange('specialty', e.target.value)}
            className="bg-black/50 border-gold/30 text-white"
            placeholder="e.g., Classic haircuts"
          />
        </div>
        <div>
          <Label className="text-gold">Experience</Label>
          <Input
            value={staffData.experience || ''}
            onChange={(e) => handleFieldChange('experience', e.target.value)}
            className="bg-black/50 border-gold/30 text-white"
            placeholder="e.g., 5 years"
          />
        </div>
        
        <div>
          <Label className="text-gold mb-3 block">Working Hours</Label>
          <div className="space-y-3 max-h-60 overflow-y-auto">
            {days.map(day => (
              <div key={day} className="flex items-center space-x-3 p-2 rounded border border-gold/20">
                <Checkbox
                  checked={staffData.available_hours?.[day]?.enabled ?? false}
                  onCheckedChange={(checked) => {
                    const updatedHours = {
                      ...staffData.available_hours,
                      [day]: { 
                        ...staffData.available_hours?.[day], 
                        enabled: checked,
                        start: staffData.available_hours?.[day]?.start || '09:00',
                        end: staffData.available_hours?.[day]?.end || '18:00'
                      }
                    };
                    handleFieldChange('available_hours', updatedHours);
                  }}
                  className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                />
                <div className="w-20 text-gold text-sm">{dayLabels[day]}</div>
                {staffData.available_hours?.[day]?.enabled && (
                  <>
                    <Input
                      type="time"
                      value={staffData.available_hours[day].start}
                      onChange={(e) => {
                        const updatedHours = {
                          ...staffData.available_hours,
                          [day]: { ...staffData.available_hours[day], start: e.target.value }
                        };
                        handleFieldChange('available_hours', updatedHours);
                      }}
                      className="w-24 bg-black/50 border-gold/30 text-white text-sm"
                    />
                    <span className="text-gold">to</span>
                    <Input
                      type="time"
                      value={staffData.available_hours[day].end}
                      onChange={(e) => {
                        const updatedHours = {
                          ...staffData.available_hours,
                          [day]: { ...staffData.available_hours[day], end: e.target.value }
                        };
                        handleFieldChange('available_hours', updatedHours);
                      }}
                      className="w-24 bg-black/50 border-gold/30 text-white text-sm"
                    />
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex justify-end space-x-2">
          <Button 
            variant="outline" 
            onClick={onCancel}
            className="border-gold/50 text-gold hover:bg-gold hover:text-black"
          >
            Cancel
          </Button>
          <Button 
            onClick={onSubmit}
            disabled={loading}
            className="bg-gold text-black hover:bg-gold/90"
          >
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">Staff Management</h2>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-gold text-black hover:bg-gold/90">
              <Plus className="h-4 w-4 mr-2" />
              Add New Staff
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-gold">Add New Staff Member</DialogTitle>
            </DialogHeader>
            <StaffForm
              staffData={newStaff}
              onChange={handleNewStaffChange}
              onSubmit={handleAddStaff}
              onCancel={() => setShowAddDialog(false)}
              loading={loading}
              title=""
              isEditing={false}
            />
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {staff.map((member) => (
          <Card key={member.id} className="bg-gray-900/50 border-gold/20">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div className="flex items-center space-x-3">
                  {member.avatar_url ? (
                    <img 
                      src={member.avatar_url} 
                      alt={member.name}
                      className="w-12 h-12 rounded-full object-cover border-2 border-gold/30"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-gold/20 flex items-center justify-center">
                      <Users className="h-6 w-6 text-gold" />
                    </div>
                  )}
                  <div>
                    <CardTitle className="text-gold text-lg">{member.name}</CardTitle>
                    <p className="text-gray-300 text-sm">{member.specialty}</p>
                  </div>
                </div>
                <div className="flex space-x-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingStaff(member)}
                    className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteStaff(member.id)}
                    className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-gray-300">
                  <strong>Experience:</strong> {member.experience}
                </div>
                <div className="text-sm text-gray-400">
                  <strong>Working Days:</strong>
                  <div className="mt-1">
                    {member.available_hours && Object.entries(member.available_hours)
                      .filter(([_, hours]) => hours.enabled)
                      .map(([day, hours]) => (
                        <div key={day} className="flex justify-between">
                          <span className="capitalize">{day}:</span>
                          <span>{hours.start} - {hours.end}</span>
                        </div>
                      ))
                    }
                  </div>
                </div>
                <Badge variant="outline" className="border-gold/50 text-gold">
                  Active
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Edit Staff Dialog */}
      {editingStaff && (
        <Dialog open={!!editingStaff} onOpenChange={() => setEditingStaff(null)}>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-gold">Edit Staff Member</DialogTitle>
            </DialogHeader>
            <StaffForm
              staffData={editingStaff}
              onChange={handleEditStaffChange}
              onSubmit={() => handleUpdateStaff(editingStaff.id, editingStaff)}
              onCancel={() => setEditingStaff(null)}
              loading={loading}
              title=""
              isEditing={true}
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

const SettingsManager = ({ token, onRefresh }) => {
  const [settings, setSettings] = useState({
    site_title: 'Frisor LaFata',
    site_description: 'Klassisk barbering siden 2010',
    contact_phone: '+45 12 34 56 78',
    contact_email: 'info@frisorlafata.dk',
    address: 'Hovedgaden 123, 1000 København',
    hero_title: 'Klassisk Barbering',
    hero_subtitle: 'i Hjertet af Byen',
    hero_description: 'Oplev den autentiske barber-oplevelse hos Frisor LaFata. Vi kombinerer traditionel håndværk med moderne teknikker.',
    hero_image: '',
    paypal_client_id: '',
    paypal_client_secret: '',
    paypal_sandbox_mode: true,
    email_smtp_server: 'smtp.gmail.com',
    email_smtp_port: 587,
    email_user: '',
    email_password: '',
    email_subject_template: 'Booking Confirmation - {{business_name}}',
    email_body_template: `Dear {{customer_name}},

Thank you for booking with {{business_name}}!

Booking Details:
- Date: {{booking_date}}
- Time: {{booking_time}}
- Services: {{services}}
- Staff: {{staff_name}}
- Total Price: {{total_price}} DKK

Location:
{{business_address}}

Phone: {{business_phone}}
Email: {{business_email}}

We look forward to seeing you!

Best regards,
{{business_name}} Team`,
    email_confirmation_subject: 'Booking Confirmed - {{business_name}}',
    email_confirmation_body: `Dear {{customer_name}},

Great news! Your booking has been CONFIRMED.

Confirmed Booking Details:
- Date: {{booking_date}}
- Time: {{booking_time}}
- Services: {{services}}
- Staff: {{staff_name}}
- Total Price: {{total_price}} DKK

Location:
{{business_address}}

Phone: {{business_phone}}
Email: {{business_email}}

We look forward to seeing you at the confirmed time!

Best regards,
{{business_name}} Team`,
    email_change_subject: 'Booking Time Changed - {{business_name}}',
    email_change_body: `Dear {{customer_name}},

We need to inform you about a change to your booking.

UPDATED Booking Details:
- NEW Date: {{booking_date}}
- NEW Time: {{booking_time}}
- Services: {{services}} (unchanged)
- Staff: {{staff_name}}
- Total Price: {{total_price}} DKK (unchanged)

Reason for change: {{admin_notes}}

Location:
{{business_address}}

Phone: {{business_phone}}
Email: {{business_email}}

We apologize for any inconvenience and look forward to seeing you at the new time!

Best regards,
{{business_name}} Team`
  });
  const [loading, setLoading] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSettings(prev => ({ ...prev, ...response.data }));
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setLoading(true);
      await axios.put(`${API}/settings`, settings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      onRefresh();
      alert('Settings saved successfully!');
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Failed to save settings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (file) => {
    try {
      setUploadingImage(true);
      const formData = new FormData();
      formData.append('image', file);
      
      const response = await axios.post(`${API}/upload/image`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setSettings(prev => ({ ...prev, hero_image: response.data.image_url }));
    } catch (error) {
      console.error('Error uploading image:', error);
      alert('Failed to upload image. Please try again.');
    } finally {
      setUploadingImage(false);
    }
  };

  const handleSettingChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">Site Settings</h2>
        <Button 
          onClick={handleSaveSettings}
          disabled={loading}
          className="bg-gold text-black hover:bg-gold/90"
        >
          {loading ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="bg-gray-900/50 border border-gold/20">
          <TabsTrigger value="general" className="data-[state=active]:bg-gold data-[state=active]:text-black">
            <Globe className="h-4 w-4 mr-2" />
            General
          </TabsTrigger>
          <TabsTrigger value="content" className="data-[state=active]:bg-gold data-[state=active]:text-black">
            <FileText className="h-4 w-4 mr-2" />
            Homepage Content
          </TabsTrigger>
          <TabsTrigger value="payment" className="data-[state=active]:bg-gold data-[state=active]:text-black">
            <CreditCard className="h-4 w-4 mr-2" />
            Payment Settings
          </TabsTrigger>
          <TabsTrigger value="email" className="data-[state=active]:bg-gold data-[state=active]:text-black">
            <Mail className="h-4 w-4 mr-2" />
            Email Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6">
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold">General Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-gold">Site Title</Label>
                <Input
                  value={settings.site_title}
                  onChange={(e) => handleSettingChange('site_title', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div>
                <Label className="text-gold">Site Description</Label>
                <Input
                  value={settings.site_description}
                  onChange={(e) => handleSettingChange('site_description', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gold">Phone Number</Label>
                  <Input
                    value={settings.contact_phone}
                    onChange={(e) => handleSettingChange('contact_phone', e.target.value)}
                    className="bg-black/50 border-gold/30 text-white"
                  />
                </div>
                <div>
                  <Label className="text-gold">Email</Label>
                  <Input
                    value={settings.contact_email}
                    onChange={(e) => handleSettingChange('contact_email', e.target.value)}
                    className="bg-black/50 border-gold/30 text-white"
                  />
                </div>
              </div>
              <div>
                <Label className="text-gold">Address</Label>
                <Input
                  value={settings.address}
                  onChange={(e) => handleSettingChange('address', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="content" className="space-y-6">
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold">Homepage Content</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-gold">Hero Title</Label>
                <Input
                  value={settings.hero_title}
                  onChange={(e) => handleSettingChange('hero_title', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div>
                <Label className="text-gold">Hero Subtitle</Label>
                <Input
                  value={settings.hero_subtitle}
                  onChange={(e) => handleSettingChange('hero_subtitle', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div>
                <Label className="text-gold">Hero Description</Label>
                <Textarea
                  value={settings.hero_description}
                  onChange={(e) => handleSettingChange('hero_description', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div>
                <Label className="text-gold">Hero Background Image</Label>
                <div className="flex items-center space-x-4 mt-2">
                  {settings.hero_image && (
                    <img 
                      src={settings.hero_image} 
                      alt="Hero background" 
                      className="w-24 h-16 rounded object-cover border-2 border-gold/30"
                    />
                  )}
                  <div>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) handleImageUpload(file);
                      }}
                      className="hidden"
                      id="hero-image-upload"
                    />
                    <label
                      htmlFor="hero-image-upload"
                      className="cursor-pointer inline-flex items-center px-3 py-2 border border-gold/50 rounded-md text-gold hover:bg-gold hover:text-black transition-colors"
                    >
                      {uploadingImage ? (
                        <>Uploading...</>
                      ) : (
                        <>
                          <Upload className="h-4 w-4 mr-2" />
                          Upload Image
                        </>
                      )}
                    </label>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payment" className="space-y-6">
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold">PayPal Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gold">PayPal Client ID</Label>
                  <Input
                    type="password"
                    value={settings.paypal_client_id}
                    onChange={(e) => handleSettingChange('paypal_client_id', e.target.value)}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="Enter PayPal Client ID"
                  />
                </div>
                <div>
                  <Label className="text-gold">PayPal Client Secret</Label>
                  <Input
                    type="password"
                    value={settings.paypal_client_secret}
                    onChange={(e) => handleSettingChange('paypal_client_secret', e.target.value)}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="Enter PayPal Client Secret"
                  />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={settings.paypal_sandbox_mode}
                  onCheckedChange={(checked) => handleSettingChange('paypal_sandbox_mode', checked)}
                  className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                />
                <Label className="text-gold">Sandbox Mode (for testing)</Label>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="email" className="space-y-6">
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold">Email Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gold">SMTP Server</Label>
                  <Input
                    value={settings.email_smtp_server}
                    onChange={(e) => handleSettingChange('email_smtp_server', e.target.value)}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="smtp.gmail.com"
                  />
                </div>
                <div>
                  <Label className="text-gold">SMTP Port</Label>
                  <Input
                    type="number"
                    value={settings.email_smtp_port}
                    onChange={(e) => handleSettingChange('email_smtp_port', parseInt(e.target.value))}
                    className="bg-black/50 border-gold/30 text-white"
                  />
                </div>
              </div>
              <div>
                <Label className="text-gold">Email Username</Label>
                <Input
                  value={settings.email_user}
                  onChange={(e) => handleSettingChange('email_user', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="your-email@gmail.com"
                />
              </div>
              <div>
                <Label className="text-gold">Email Password</Label>
                <Input
                  type="password"
                  value={settings.email_password}
                  onChange={(e) => handleSettingChange('email_password', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="App password for Gmail"
                />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold">Email Templates</CardTitle>
              <p className="text-gray-300 text-sm">Customize the booking confirmation emails sent to customers</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Initial Booking Email */}
              <div>
                <h4 className="text-gold font-semibold mb-3">📧 Initial Booking Email (Pending Confirmation)</h4>
                <div className="space-y-4">
                  <div>
                    <Label className="text-gold">Email Subject Template</Label>
                    <Input
                      value={settings.email_subject_template || 'Booking Confirmation - {{business_name}}'}
                      onChange={(e) => handleSettingChange('email_subject_template', e.target.value)}
                      className="bg-black/50 border-gold/30 text-white"
                      placeholder="Booking Confirmation - {{business_name}}"
                    />
                  </div>
                  <div>
                    <Label className="text-gold">Email Body Template</Label>
                    <Textarea
                      value={settings.email_body_template || 'Dear {{customer_name}}, Your booking has been created.'}
                      onChange={(e) => handleSettingChange('email_body_template', e.target.value)}
                      className="bg-black/50 border-gold/30 text-white"
                      rows={8}
                      placeholder="Email body template..."
                    />
                  </div>
                </div>
              </div>

              <Separator className="bg-gold/20" />

              {/* Booking Confirmation Email */}
              <div>
                <h4 className="text-gold font-semibold mb-3">✅ Booking Confirmation Email (Admin Confirmed)</h4>
                <div className="space-y-4">
                  <div>
                    <Label className="text-gold">Confirmation Email Subject</Label>
                    <Input
                      value={settings.email_confirmation_subject || 'Booking Confirmed - {{business_name}}'}
                      onChange={(e) => handleSettingChange('email_confirmation_subject', e.target.value)}
                      className="bg-black/50 border-gold/30 text-white"
                      placeholder="Booking Confirmed - {{business_name}}"
                    />
                  </div>
                  <div>
                    <Label className="text-gold">Confirmation Email Body</Label>
                    <Textarea
                      value={settings.email_confirmation_body || 'Dear {{customer_name}}, Your booking has been confirmed.'}
                      onChange={(e) => handleSettingChange('email_confirmation_body', e.target.value)}
                      className="bg-black/50 border-gold/30 text-white"
                      rows={8}
                      placeholder="Confirmation email body..."
                    />
                  </div>
                </div>
              </div>

              <Separator className="bg-gold/20" />

              {/* Booking Change Email */}
              <div>
                <h4 className="text-gold font-semibold mb-3">🔄 Booking Change Email (Time/Date Changed)</h4>
                <div className="space-y-4">
                  <div>
                    <Label className="text-gold">Change Email Subject</Label>
                    <Input
                      value={settings.email_change_subject || 'Booking Time Changed - {{business_name}}'}
                      onChange={(e) => handleSettingChange('email_change_subject', e.target.value)}
                      className="bg-black/50 border-gold/30 text-white"
                      placeholder="Booking Time Changed - {{business_name}}"
                    />
                  </div>
                  <div>
                    <Label className="text-gold">Change Email Body</Label>
                    <Textarea
                      value={settings.email_change_body || 'Dear {{customer_name}}, Your booking time has been changed.'}
                      onChange={(e) => handleSettingChange('email_change_body', e.target.value)}
                      className="bg-black/50 border-gold/30 text-white"
                      rows={8}
                      placeholder="Change notification email body..."
                    />
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <p className="text-xs text-gray-400 mb-2">Available template variables:</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    '{{customer_name}}', '{{business_name}}', '{{booking_date}}', '{{booking_time}}',
                    '{{services}}', '{{staff_name}}', '{{total_price}}', '{{business_address}}',
                    '{{business_phone}}', '{{business_email}}', '{{admin_notes}}'
                  ].map(variable => (
                    <Badge key={variable} variant="outline" className="border-gold/30 text-gold text-xs cursor-pointer"
                      onClick={() => {
                        // For now, just copy to clipboard
                        navigator.clipboard.writeText(variable);
                      }}>
                      {variable}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="bg-blue-900/20 p-4 rounded-lg border border-blue-500/20">
                <h4 className="text-blue-400 font-semibold mb-2">Email Flow</h4>
                <div className="text-xs text-gray-300 space-y-1">
                  <p>📧 <strong>Initial Email:</strong> Sent when customer creates booking (status: pending)</p>
                  <p>✅ <strong>Confirmation Email:</strong> Sent when admin confirms booking</p>
                  <p>🔄 <strong>Change Email:</strong> Sent when admin changes booking time/date</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const AdminDashboard = ({ token, user, onLogout }) => {
  const [bookings, setBookings] = useState([]);
  const [staff, setStaff] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const headers = { Authorization: `Bearer ${token}` };
      
      const [bookingsRes, staffRes, servicesRes] = await Promise.all([
        axios.get(`${API}/bookings`, { headers }),
        axios.get(`${API}/staff`),
        axios.get(`${API}/services`)
      ]);
      
      setBookings(bookingsRes.data);
      setStaff(staffRes.data);
      setServices(servicesRes.data);
    } catch (error) {
      setError('Could not fetch data');
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    onLogout();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-gold">Loading admin dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="border-b border-gold/20 bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Scissors className="h-8 w-8 text-gold mr-3" />
              <h1 className="text-2xl font-bold text-gold font-serif">Frisor LaFata Admin</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-gray-300">
                <User className="h-4 w-4 mr-2" />
                <span>{user.name}</span>
              </div>
              <Button
                variant="outline"
                onClick={handleLogout}
                className="border-gold/50 text-gold hover:bg-gold hover:text-black"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Log Out
              </Button>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <Alert className="m-4 border-red-500 bg-red-500/10">
          <AlertDescription className="text-red-400">{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="bookings" className="space-y-6">
          <TabsList className="bg-gray-900/50 border border-gold/20">
            <TabsTrigger value="bookings" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Calendar className="h-4 w-4 mr-2" />
              Bookings
            </TabsTrigger>
            <TabsTrigger value="revenue" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <TrendingUp className="h-4 w-4 mr-2" />
              Revenue
            </TabsTrigger>
            <TabsTrigger value="staff" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Users className="h-4 w-4 mr-2" />
              Staff
            </TabsTrigger>
            <TabsTrigger value="breaks" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Coffee className="h-4 w-4 mr-2" />
              Breaks
            </TabsTrigger>
            <TabsTrigger value="services" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Scissors className="h-4 w-4 mr-2" />
              Services
            </TabsTrigger>
            <TabsTrigger value="content" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <FileText className="h-4 w-4 mr-2" />
              Pages
            </TabsTrigger>
            <TabsTrigger value="gallery" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Image className="h-4 w-4 mr-2" />
              Gallery
            </TabsTrigger>
            <TabsTrigger value="users" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <User className="h-4 w-4 mr-2" />
              Users
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="bookings">
            <EnhancedBookingManager 
              token={token} 
              staff={staff} 
              services={services} 
              onRefresh={fetchData} 
            />
          </TabsContent>

          <TabsContent value="staff">
            <StaffManager 
              token={token} 
              onRefresh={fetchData} 
            />
          </TabsContent>

          <TabsContent value="services">
            <ServiceManager 
              token={token} 
              onRefresh={fetchData} 
            />
          </TabsContent>

          <TabsContent value="content">
            <ContentManager 
              token={token} 
              onRefresh={fetchData} 
            />
          </TabsContent>

          <TabsContent value="gallery">
            <GalleryManager 
              token={token} 
              staff={staff}
              onRefresh={fetchData} 
            />
          </TabsContent>

          <TabsContent value="users">
            <UserManager 
              token={token} 
              onRefresh={fetchData} 
            />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsManager 
              token={token} 
              onRefresh={fetchData} 
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

const AdminApp = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if already logged in
    const savedToken = localStorage.getItem('admin_token');
    const savedUser = localStorage.getItem('admin_user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogin = (newToken, newUser) => {
    setToken(newToken);
    setUser(newUser);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return <AdminLogin onLogin={handleLogin} />;
  }

  return <AdminDashboard token={token} user={user} onLogout={handleLogout} />;
};

export default AdminApp;