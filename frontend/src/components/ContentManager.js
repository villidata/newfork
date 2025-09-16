import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Checkbox } from './ui/checkbox';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Plus, Edit, Trash2, Upload, Eye, Globe, FileText, Image } from 'lucide-react';
import RichTextEditor from './RichTextEditor';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ContentManager = ({ token, onRefresh }) => {
  const [pages, setPages] = useState([]);
  const [editingPage, setEditingPage] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [newPage, setNewPage] = useState({
    title: '',
    slug: '',
    content: '',
    meta_description: '',
    excerpt: '',
    is_published: true,
    show_in_navigation: true,
    navigation_order: 0,
    page_type: 'page',
    featured_image: '',
    categories: [],
    tags: []
  });

  // Predefined categories and page types
  const pageTypes = [
    { value: 'page', label: 'Standard Page' },
    { value: 'blog', label: 'Blog Post' },
    { value: 'about', label: 'About Page' },
    { value: 'service', label: 'Service Page' }
  ];

  const commonCategories = [
    'Services', 'About', 'News', 'Tips', 'Hair Care', 'Beard Care', 'Styling', 'Products'
  ];

  useEffect(() => {
    fetchPages();
  }, []);

  const fetchPages = async () => {
    try {
      const response = await axios.get(`${API}/pages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPages(response.data);
    } catch (error) {
      console.error('Error fetching pages:', error);
    }
  };

  const handleAddPage = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/pages`, newPage, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNewPage({
        title: '',
        slug: '',
        content: '',
        meta_description: '',
        excerpt: '',
        is_published: true,
        show_in_navigation: true,
        navigation_order: 0,
        page_type: 'page',
        featured_image: '',
        categories: [],
        tags: []
      });
      setShowAddDialog(false);
      fetchPages();
      onRefresh();
    } catch (error) {
      console.error('Error adding page:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePage = async (pageId, updatedData) => {
    try {
      await axios.put(`${API}/pages/${pageId}`, updatedData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEditingPage(null);
      fetchPages();
      onRefresh();
    } catch (error) {
      console.error('Error updating page:', error);
    }
  };

  const handleDeletePage = async (pageId) => {
    if (window.confirm('Are you sure you want to delete this page?')) {
      try {
        await axios.delete(`${API}/pages/${pageId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        fetchPages();
        onRefresh();
      } catch (error) {
        console.error('Error deleting page:', error);
        alert('Failed to delete page. Please try again.');
      }
    }
  };

  const handleImageUpload = async (file, pageData, setPageData) => {
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
      
      setPageData(prev => ({ ...prev, featured_image: response.data.image_url }));
    } catch (error) {
      console.error('Error uploading image:', error);
      alert('Failed to upload image. Please try again.');
    } finally {
      setUploadingImage(false);
    }
  };

  const generateSlug = (title) => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  };

  const handleNewPageChange = (field, value) => {
    setNewPage(prev => {
      const updated = { ...prev, [field]: value };
      // Auto-generate slug when title changes
      if (field === 'title' && !prev.slug) {
        updated.slug = generateSlug(value);
      }
      return updated;
    });
  };

  const handleEditPageChange = (field, value) => {
    setEditingPage(prev => ({ ...prev, [field]: value }));
  };

  const addCategory = (category, pageData, setPageData) => {
    if (category && !pageData.categories.includes(category)) {
      setPageData(prev => ({
        ...prev,
        categories: [...prev.categories, category]
      }));
    }
  };

  const removeCategory = (category, pageData, setPageData) => {
    setPageData(prev => ({
      ...prev,
      categories: prev.categories.filter(c => c !== category)
    }));
  };

  const handleTagsChange = (tagsString, pageData, setPageData) => {
    const tags = tagsString.split(',').map(tag => tag.trim()).filter(tag => tag);
    setPageData(prev => ({ ...prev, tags }));
  };

  const PageForm = ({ pageData, setPageData, onSubmit, onCancel, loading, title, isEditing = false }) => {
    const [newCategory, setNewCategory] = useState('');

    return (
      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-gold">{title}</h3>
        
        <Tabs defaultValue="content" className="space-y-6">
          <TabsList className="bg-gray-900/50 border border-gold/20">
            <TabsTrigger value="content" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <FileText className="h-4 w-4 mr-2" />
              Content
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Globe className="h-4 w-4 mr-2" />
              Settings
            </TabsTrigger>
            <TabsTrigger value="media" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Image className="h-4 w-4 mr-2" />
              Media
            </TabsTrigger>
          </TabsList>

          <TabsContent value="content" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gold">Page Title *</Label>
                <Input
                  value={pageData.title}
                  onChange={(e) => setPageData('title', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="e.g., About Us"
                />
              </div>
              <div>
                <Label className="text-gold">URL Slug *</Label>
                <Input
                  value={pageData.slug}
                  onChange={(e) => setPageData('slug', e.target.value)}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="e.g., about-us"
                />
              </div>
            </div>

            <div>
              <Label className="text-gold">Excerpt (Short Description)</Label>
              <Textarea
                value={pageData.excerpt}
                onChange={(e) => setPageData('excerpt', e.target.value)}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="A brief description of this page..."
                rows={2}
              />
            </div>

            <div>
              <Label className="text-gold">Content *</Label>
              <div className="mt-2">
                <RichTextEditor
                  value={pageData.content}
                  onChange={(content) => setPageData('content', content)}
                  token={token}
                  height={400}
                />
              </div>
            </div>

            <div>
              <Label className="text-gold">Meta Description (SEO)</Label>
              <Textarea
                value={pageData.meta_description}
                onChange={(e) => setPageData('meta_description', e.target.value)}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="SEO meta description (max 160 characters)"
                maxLength={160}
                rows={2}
              />
              <p className="text-xs text-gray-400 mt-1">
                {pageData.meta_description.length}/160 characters
              </p>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gold">Page Type</Label>
                <Select value={pageData.page_type} onValueChange={(value) => setPageData('page_type', value)}>
                  <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-gold/20">
                    {pageTypes.map(type => (
                      <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-gold">Navigation Order</Label>
                <Input
                  type="number"
                  value={pageData.navigation_order}
                  onChange={(e) => setPageData('navigation_order', parseInt(e.target.value) || 0)}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="0"
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={pageData.is_published}
                  onCheckedChange={(checked) => setPageData('is_published', checked)}
                  className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                />
                <Label className="text-gold">Published</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={pageData.show_in_navigation}
                  onCheckedChange={(checked) => setPageData('show_in_navigation', checked)}
                  className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                />
                <Label className="text-gold">Show in Navigation Menu</Label>
              </div>
            </div>

            <div>
              <Label className="text-gold">Categories</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {pageData.categories.map((category, index) => (
                  <Badge 
                    key={index} 
                    variant="outline" 
                    className="border-gold/50 text-gold cursor-pointer"
                    onClick={() => removeCategory(category, pageData, setPageData)}
                  >
                    {category} ×
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  placeholder="Add new category..."
                  className="bg-black/50 border-gold/30 text-white"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addCategory(newCategory, pageData, setPageData);
                      setNewCategory('');
                    }
                  }}
                />
                <Button
                  type="button"
                  onClick={() => {
                    addCategory(newCategory, pageData, setPageData);
                    setNewCategory('');
                  }}
                  className="bg-gold text-black hover:bg-gold/90"
                >
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {commonCategories.map(category => (
                  <Badge
                    key={category}
                    variant="outline"
                    className="border-gold/30 text-gold cursor-pointer hover:bg-gold hover:text-black"
                    onClick={() => addCategory(category, pageData, setPageData)}
                  >
                    + {category}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-gold">Tags (comma-separated)</Label>
              <Input
                value={pageData.tags.join(', ')}
                onChange={(e) => handleTagsChange(e.target.value, pageData, setPageData)}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="hair, beard, styling, tips..."
              />
            </div>
          </TabsContent>

          <TabsContent value="media" className="space-y-4">
            <div>
              <Label className="text-gold">Featured Image</Label>
              <div className="flex items-center space-x-4 mt-2">
                {pageData.featured_image && (
                  <img 
                    src={pageData.featured_image} 
                    alt="Featured" 
                    className="w-24 h-16 rounded object-cover border-2 border-gold/30"
                  />
                )}
                <div>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      if (file) handleImageUpload(file, pageData, setPageData);
                    }}
                    className="hidden"
                    id={`featured-image-upload-${isEditing ? 'edit' : 'new'}`}
                  />
                  <label
                    htmlFor={`featured-image-upload-${isEditing ? 'edit' : 'new'}`}
                    className="cursor-pointer inline-flex items-center px-3 py-2 border border-gold/50 rounded-md text-gold hover:bg-gold hover:text-black transition-colors"
                  >
                    {uploadingImage ? (
                      <>Uploading...</>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Featured Image
                      </>
                    )}
                  </label>
                  {pageData.featured_image && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setPageData('featured_image', '')}
                      className="ml-2 border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                    >
                      Remove
                    </Button>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-gray-900/30 p-4 rounded-lg">
              <h4 className="text-gold font-semibold mb-2">Media Tips:</h4>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• Use the rich text editor to add images and videos directly to content</li>
                <li>• Featured image will be displayed at the top of the page</li>
                <li>• Supported video formats: MP4, WebM, OGG, AVI, MOV</li>
                <li>• You can also embed YouTube and Vimeo videos using the media button in the editor</li>
              </ul>
            </div>
          </TabsContent>
        </Tabs>

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
            disabled={loading || !pageData.title || !pageData.slug}
            className="bg-gold text-black hover:bg-gold/90"
          >
            {loading ? 'Saving...' : 'Save Page'}
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">Content Management</h2>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button className="bg-gold text-black hover:bg-gold/90">
              <Plus className="h-4 w-4 mr-2" />
              Add New Page
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-6xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-gold">Create New Page</DialogTitle>
            </DialogHeader>
            <PageForm
              pageData={newPage}
              setPageData={handleNewPageChange}
              onSubmit={handleAddPage}
              onCancel={() => setShowAddDialog(false)}
              loading={loading}
              title=""
              isEditing={false}
            />
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {pages.map((page) => (
          <Card key={page.id} className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant={page.page_type === 'blog' ? 'default' : 'secondary'} className="text-xs">
                      {pageTypes.find(t => t.value === page.page_type)?.label || page.page_type}
                    </Badge>
                    <Badge variant={page.is_published ? "default" : "secondary"} className={page.is_published ? "bg-green-500" : "bg-gray-500"}>
                      {page.is_published ? 'Published' : 'Draft'}
                    </Badge>
                    {page.show_in_navigation && (
                      <Badge variant="outline" className="border-blue-500 text-blue-400">
                        In Menu
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-gold text-lg">{page.title}</CardTitle>
                  <p className="text-gray-300 text-sm">/{page.slug}</p>
                  {page.excerpt && (
                    <p className="text-gray-400 text-sm mt-1">{page.excerpt}</p>
                  )}
                  {page.categories.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {page.categories.map((category, index) => (
                        <Badge key={index} variant="outline" className="border-gold/50 text-gold text-xs">
                          {category}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {page.featured_image && (
                    <img 
                      src={page.featured_image} 
                      alt={page.title}
                      className="w-16 h-12 rounded object-cover border border-gold/30"
                    />
                  )}
                  <div className="flex space-x-1">
                    {page.is_published && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(`/page/${page.slug}`, '_blank')}
                        className="border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white"
                      >
                        <Eye className="h-3 w-3" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingPage(page)}
                      className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                    >
                      <Edit className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDeletePage(page.id)}
                      className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-gray-300 text-sm">
                <div dangerouslySetInnerHTML={{ 
                  __html: page.content.replace(/<[^>]*>/g, '').substring(0, 200) + (page.content.replace(/<[^>]*>/g, '').length > 200 ? '...' : '')
                }} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {pages.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No pages yet</h3>
          <p className="text-gray-400 mb-6">Create your first page to get started</p>
          <Button onClick={() => setShowAddDialog(true)} className="bg-gold text-black hover:bg-gold/90">
            <Plus className="h-4 w-4 mr-2" />
            Create First Page
          </Button>
        </div>
      )}

      {/* Edit Page Dialog */}
      {editingPage && (
        <Dialog open={!!editingPage} onOpenChange={() => setEditingPage(null)}>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-6xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-gold">Edit Page</DialogTitle>
            </DialogHeader>
            <PageForm
              pageData={editingPage}
              setPageData={handleEditPageChange}
              onSubmit={() => handleUpdatePage(editingPage.id, editingPage)}
              onCancel={() => setEditingPage(null)}
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

export default ContentManager;