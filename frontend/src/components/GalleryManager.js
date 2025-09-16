import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { Checkbox } from './ui/checkbox';
import { Plus, Edit, Trash2, Upload, Star, Image as ImageIcon, AlertCircle, CheckCircle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GalleryManager = ({ token, staff, onRefresh }) => {
  const [galleryItems, setGalleryItems] = useState([]);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [newItem, setNewItem] = useState({
    title: '',
    description: '',
    before_image: '',
    after_image: '',
    service_type: '',
    staff_id: '',
    is_featured: false
  });

  const serviceTypes = [
    'haircut', 'beard', 'styling', 'coloring', 'wedding', 'special_occasion', 'other'
  ];

  useEffect(() => {
    fetchGalleryItems();
  }, []);

  const fetchGalleryItems = async () => {
    try {
      const response = await axios.get(`${API}/admin/gallery`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGalleryItems(response.data);
    } catch (error) {
      console.error('Error fetching gallery items:', error);
      setError('Failed to fetch gallery items');
    }
  };

  const handleImageUpload = async (file, imageType) => {
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
      
      if (editingItem) {
        setEditingItem(prev => ({ ...prev, [imageType]: response.data.image_url }));
      } else {
        setNewItem(prev => ({ ...prev, [imageType]: response.data.image_url }));
      }
      
      setSuccess(`${imageType === 'before_image' ? 'Before' : 'After'} image uploaded successfully`);
    } catch (error) {
      console.error('Error uploading image:', error);
      setError('Failed to upload image. Please try again.');
    } finally {
      setUploadingImage(false);
    }
  };

  const handleAddItem = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/gallery`, newItem, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNewItem({
        title: '',
        description: '',
        before_image: '',
        after_image: '',
        service_type: '',
        staff_id: '',
        is_featured: false
      });
      setShowAddDialog(false);
      setSuccess('Gallery item created successfully');
      fetchGalleryItems();
      onRefresh();
    } catch (error) {
      console.error('Error adding gallery item:', error);
      setError(error.response?.data?.detail || 'Failed to create gallery item');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateItem = async (itemId, updatedData) => {
    try {
      setLoading(true);
      await axios.put(`${API}/gallery/${itemId}`, updatedData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEditingItem(null);
      setSuccess('Gallery item updated successfully');
      fetchGalleryItems();
      onRefresh();
    } catch (error) {
      console.error('Error updating gallery item:', error);
      setError(error.response?.data?.detail || 'Failed to update gallery item');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (window.confirm('Are you sure you want to delete this gallery item?')) {
      try {
        await axios.delete(`${API}/gallery/${itemId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSuccess('Gallery item deleted successfully');
        fetchGalleryItems();
        onRefresh();
      } catch (error) {
        console.error('Error deleting gallery item:', error);
        setError(error.response?.data?.detail || 'Failed to delete gallery item');
      }
    }
  };

  const getStaffName = (staffId) => {
    if (!staffId) return 'No staff assigned';
    const staffMember = staff.find(s => s.id === staffId);
    return staffMember ? staffMember.name : 'Unknown staff';
  };

  const clearMessages = () => {
    setError('');
    setSuccess('');
  };

  const ImageUploadField = ({ label, imageType, currentImage, isEditing = false }) => (
    <div>
      <Label className="text-gold">{label}</Label>
      <div className="space-y-2">
        {currentImage && (
          <div className="relative">
            <img 
              src={currentImage} 
              alt={label}
              className="w-32 h-24 rounded object-cover border-2 border-gold/30"
            />
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                if (isEditing) {
                  setEditingItem(prev => ({ ...prev, [imageType]: '' }));
                } else {
                  setNewItem(prev => ({ ...prev, [imageType]: '' }));
                }
              }}
              className="absolute top-1 right-1 h-6 w-6 p-0 border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
            >
              ×
            </Button>
          </div>
        )}
        <div>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              const file = e.target.files[0];
              if (file) handleImageUpload(file, imageType);
            }}
            className="hidden"
            id={`${imageType}-upload-${isEditing ? 'edit' : 'new'}`}
          />
          <label
            htmlFor={`${imageType}-upload-${isEditing ? 'edit' : 'new'}`}
            className="cursor-pointer inline-flex items-center px-3 py-2 border border-gold/50 rounded-md text-gold hover:bg-gold hover:text-black transition-colors"
          >
            {uploadingImage ? (
              <>Uploading...</>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload {label}
              </>
            )}
          </label>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">Before/After Gallery</h2>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-gold text-black hover:bg-gold/90" onClick={clearMessages}>
              <Plus className="h-4 w-4 mr-2" />
              Add Gallery Item
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-gold">Create Gallery Item</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label className="text-gold">Title *</Label>
                <Input
                  value={newItem.title}
                  onChange={(e) => setNewItem(prev => ({ ...prev, title: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="e.g., Classic Gentleman's Cut"
                />
              </div>
              <div>
                <Label className="text-gold">Description</Label>
                <Textarea
                  value={newItem.description}
                  onChange={(e) => setNewItem(prev => ({ ...prev, description: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="Describe the transformation..."
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <ImageUploadField 
                  label="Before Image *" 
                  imageType="before_image" 
                  currentImage={newItem.before_image}
                  isEditing={false}
                />
                <ImageUploadField 
                  label="After Image *" 
                  imageType="after_image" 
                  currentImage={newItem.after_image}
                  isEditing={false}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gold">Service Type</Label>
                  <Select value={newItem.service_type} onValueChange={(value) => setNewItem(prev => ({ ...prev, service_type: value }))}>
                    <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                      <SelectValue placeholder="Select service type" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-gold/20">
                      {serviceTypes.map(type => (
                        <SelectItem key={type} value={type}>
                          {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-gold">Staff Member</Label>
                  <Select value={newItem.staff_id} onValueChange={(value) => setNewItem(prev => ({ ...prev, staff_id: value }))}>
                    <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                      <SelectValue placeholder="Select staff member" />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-gold/20">
                      <SelectItem value="none">No staff assigned</SelectItem>
                      {staff.map(member => (
                        <SelectItem key={member.id} value={member.id}>
                          {member.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={newItem.is_featured}
                  onCheckedChange={(checked) => setNewItem(prev => ({ ...prev, is_featured: checked }))}
                  className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                />
                <Label className="text-gold">Featured (show on homepage)</Label>
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
                  onClick={handleAddItem}
                  disabled={loading || !newItem.title || !newItem.before_image || !newItem.after_image}
                  className="bg-gold text-black hover:bg-gold/90"
                >
                  {loading ? 'Creating...' : 'Create Gallery Item'}
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {galleryItems.map((item) => (
          <Card key={item.id} className="bg-gray-900/50 border-gold/20">
            <CardContent className="p-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gold">{item.title}</h3>
                  {item.is_featured && (
                    <Badge className="bg-yellow-500 text-black flex items-center gap-1">
                      <Star className="h-3 w-3" />
                      Featured
                    </Badge>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <p className="text-xs text-gray-400 mb-1">Before</p>
                    <img 
                      src={item.before_image} 
                      alt="Before"
                      className="w-full h-24 rounded object-cover border border-gold/30"
                    />
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">After</p>
                    <img 
                      src={item.after_image} 
                      alt="After"
                      className="w-full h-24 rounded object-cover border border-gold/30"
                    />
                  </div>
                </div>

                {item.description && (
                  <p className="text-gray-300 text-sm">{item.description}</p>
                )}

                <div className="space-y-2 text-sm">
                  {item.service_type && (
                    <Badge variant="outline" className="border-gold/50 text-gold">
                      {item.service_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Badge>
                  )}
                  <p className="text-gray-400">
                    <span className="font-medium">Staff:</span> {getStaffName(item.staff_id)}
                  </p>
                </div>

                <div className="flex justify-end space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingItem(item)}
                    className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteItem(item.id)}
                    className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {galleryItems.length === 0 && (
          <div className="col-span-full">
            <Card className="bg-gray-900/50 border-gold/20">
              <CardContent className="text-center py-12">
                <ImageIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-300 mb-2">No gallery items yet</h3>
                <p className="text-gray-400">Create your first before/after transformation</p>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Edit Gallery Item Dialog */}
      {editingItem && (
        <Dialog open={!!editingItem} onOpenChange={() => setEditingItem(null)}>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-gold">Edit Gallery Item</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label className="text-gold">Title</Label>
                <Input
                  value={editingItem.title}
                  onChange={(e) => setEditingItem(prev => ({ ...prev, title: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                />
              </div>
              <div>
                <Label className="text-gold">Description</Label>
                <Textarea
                  value={editingItem.description}
                  onChange={(e) => setEditingItem(prev => ({ ...prev, description: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <ImageUploadField 
                  label="Before Image" 
                  imageType="before_image" 
                  currentImage={editingItem.before_image}
                  isEditing={true}
                />
                <ImageUploadField 
                  label="After Image" 
                  imageType="after_image" 
                  currentImage={editingItem.after_image}
                  isEditing={true}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gold">Service Type</Label>
                  <Select 
                    value={editingItem.service_type} 
                    onValueChange={(value) => setEditingItem(prev => ({ ...prev, service_type: value }))}
                  >
                    <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-gold/20">
                      {serviceTypes.map(type => (
                        <SelectItem key={type} value={type}>
                          {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-gold">Staff Member</Label>
                  <Select 
                    value={editingItem.staff_id || ''} 
                    onValueChange={(value) => setEditingItem(prev => ({ ...prev, staff_id: value }))}
                  >
                    <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-gold/20">
                      <SelectItem value="">No staff assigned</SelectItem>
                      {staff.map(member => (
                        <SelectItem key={member.id} value={member.id}>
                          {member.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={editingItem.is_featured}
                  onCheckedChange={(checked) => setEditingItem(prev => ({ ...prev, is_featured: checked }))}
                  className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                />
                <Label className="text-gold">Featured (show on homepage)</Label>
              </div>
              <div className="flex justify-end space-x-2">
                <Button 
                  variant="outline" 
                  onClick={() => setEditingItem(null)}
                  className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={() => handleUpdateItem(editingItem.id, editingItem)}
                  disabled={loading}
                  className="bg-gold text-black hover:bg-gold/90"
                >
                  {loading ? 'Updating...' : 'Update Gallery Item'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default GalleryManager;