import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Checkbox } from './ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  DragDropContext, 
  Droppable, 
  Draggable 
} from 'react-beautiful-dnd';
import { 
  GripVertical, 
  Eye, 
  EyeOff, 
  Edit, 
  Save, 
  X, 
  Plus,
  Home,
  Users,
  Scissors,
  Image,
  MessageSquare,
  Phone
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const HomepageEditor = ({ token }) => {
  const [sections, setSections] = useState([]);
  const [editingSection, setEditingSection] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const sectionIcons = {
    hero: <Home className="h-5 w-5" />,
    services: <Scissors className="h-5 w-5" />,
    staff: <Users className="h-5 w-5" />,
    gallery: <Image className="h-5 w-5" />,
    social: <MessageSquare className="h-5 w-5" />,
    contact: <Phone className="h-5 w-5" />
  };

  const sectionTypes = [
    { value: 'hero', label: 'Hero Section', description: 'Main header with title and call-to-action' },
    { value: 'services', label: 'Services', description: 'Display available services' },
    { value: 'staff', label: 'Staff', description: 'Show team members' },
    { value: 'gallery', label: 'Gallery', description: 'Before/after photos' },
    { value: 'social', label: 'Social Media', description: 'Social media feeds' },
    { value: 'contact', label: 'Contact', description: 'Contact information and booking' }
  ];

  const buttonActions = [
    { value: 'open_booking', label: 'Open Booking System' },
    { value: 'scroll_to_services', label: 'Scroll to Services' },
    { value: 'scroll_to_contact', label: 'Scroll to Contact' },
    { value: 'external_link', label: 'External Link' },
    { value: 'none', label: 'No Action' }
  ];

  useEffect(() => {
    fetchSections();
  }, []);

  const fetchSections = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/homepage/sections`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSections(response.data);
    } catch (error) {
      console.error('Failed to fetch homepage sections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDragEnd = async (result) => {
    if (!result.destination) return;

    const items = Array.from(sections);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    // Update section orders
    const updatedItems = items.map((item, index) => ({
      ...item,
      section_order: index + 1
    }));

    setSections(updatedItems);

    // Save reorder to backend
    try {
      await axios.put(`${API}/homepage/sections/reorder`, 
        updatedItems.map(item => ({ id: item.id, section_order: item.section_order })),
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error('Failed to reorder sections:', error);
      // Revert on error
      fetchSections();
    }
  };

  const handleSectionUpdate = async (sectionId, updates) => {
    setSaving(true);
    try {
      await axios.put(`${API}/homepage/sections/${sectionId}`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update local state
      setSections(prevSections => 
        prevSections.map(section => 
          section.id === sectionId ? { ...section, ...updates } : section
        )
      );
      setEditingSection(null);
    } catch (error) {
      console.error('Failed to update section:', error);
    } finally {
      setSaving(false);
    }
  };

  const toggleSectionVisibility = async (sectionId, isEnabled) => {
    await handleSectionUpdate(sectionId, { is_enabled: !isEnabled });
  };

  const getSectionTypeInfo = (type) => {
    return sectionTypes.find(st => st.value === type) || { label: type, description: '' };
  };

  const SectionEditForm = ({ section, onSave, onCancel }) => {
    const [formData, setFormData] = useState({
      title: section.title || '',
      subtitle: section.subtitle || '',
      description: section.description || '',
      button_text: section.button_text || '',
      button_action: section.button_action || 'none',
      background_color: section.background_color || '#000000',
      text_color: section.text_color || '#D4AF37',
      is_enabled: section.is_enabled || false
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      onSave(formData);
    };

    return (
      <Card className="bg-gray-900/80 border-gold/30">
        <CardHeader>
          <CardTitle className="text-gold flex items-center gap-2">
            {sectionIcons[section.section_type]}
            Edit {getSectionTypeInfo(section.section_type).label}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                checked={formData.is_enabled}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_enabled: checked }))}
                className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
              />
              <Label className="text-gold">Section Enabled</Label>
            </div>

            <div>
              <Label className="text-gold">Title</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="Section title"
              />
            </div>

            <div>
              <Label className="text-gold">Subtitle</Label>
              <Input
                value={formData.subtitle}
                onChange={(e) => setFormData(prev => ({ ...prev, subtitle: e.target.value }))}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="Section subtitle"
              />
            </div>

            <div>
              <Label className="text-gold">Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="Section description"
                rows={3}
              />
            </div>

            {(section.section_type === 'hero' || section.section_type === 'contact') && (
              <>
                <div>
                  <Label className="text-gold">Button Text</Label>
                  <Input
                    value={formData.button_text}
                    onChange={(e) => setFormData(prev => ({ ...prev, button_text: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="Button text"
                  />
                </div>

                <div>
                  <Label className="text-gold">Button Action</Label>
                  <Select value={formData.button_action} onValueChange={(value) => setFormData(prev => ({ ...prev, button_action: value }))}>
                    <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-gold/20">
                      {buttonActions.map(action => (
                        <SelectItem key={action.value} value={action.value}>
                          {action.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gold">Background Color</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="color"
                    value={formData.background_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, background_color: e.target.value }))}
                    className="w-12 h-8 rounded border border-gold/30"
                  />
                  <Input
                    value={formData.background_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, background_color: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="#000000"
                  />
                </div>
              </div>

              <div>
                <Label className="text-gold">Text Color</Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="color"
                    value={formData.text_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, text_color: e.target.value }))}
                    className="w-12 h-8 rounded border border-gold/30"
                  />
                  <Input
                    value={formData.text_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, text_color: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="#D4AF37"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button 
                type="button"
                variant="outline" 
                onClick={onCancel}
                className="border-gold/50 text-gold hover:bg-gold hover:text-black"
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
              <Button 
                type="submit"
                disabled={saving}
                className="bg-gold text-black hover:bg-gold/90"
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gold">Loading homepage sections...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gold">Homepage Editor</h2>
          <p className="text-gray-300">Customize your homepage layout and content</p>
        </div>
        <Button
          onClick={fetchSections}
          variant="outline"
          className="border-gold/50 text-gold hover:bg-gold hover:text-black"
        >
          Refresh
        </Button>
      </div>

      {editingSection && (
        <SectionEditForm
          section={editingSection}
          onSave={(updates) => handleSectionUpdate(editingSection.id, updates)}
          onCancel={() => setEditingSection(null)}
        />
      )}

      <Card className="bg-gray-900/50 border-gold/20">
        <CardHeader>
          <CardTitle className="text-gold">Homepage Sections</CardTitle>
          <p className="text-gray-300 text-sm">
            Drag and drop to reorder sections. Use the visibility toggle to show/hide sections.
          </p>
        </CardHeader>
        <CardContent>
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="homepage-sections">
              {(provided) => (
                <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-3">
                  {sections.map((section, index) => (
                    <Draggable key={section.id} draggableId={section.id} index={index}>
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          className={`p-4 bg-black/30 border border-gold/20 rounded-lg transition-all ${
                            snapshot.isDragging ? 'shadow-lg ring-2 ring-gold/50' : ''
                          } ${!section.is_enabled ? 'opacity-50' : ''}`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div
                                {...provided.dragHandleProps}
                                className="text-gold cursor-grab active:cursor-grabbing"
                              >
                                <GripVertical className="h-5 w-5" />
                              </div>
                              
                              <div className="flex items-center gap-2">
                                {sectionIcons[section.section_type]}
                                <div>
                                  <h3 className="text-gold font-semibold">
                                    {getSectionTypeInfo(section.section_type).label}
                                  </h3>
                                  <p className="text-gray-400 text-sm">
                                    {section.title || getSectionTypeInfo(section.section_type).description}
                                  </p>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-2">
                              <Badge 
                                variant="outline" 
                                className={`border-gold/50 ${section.is_enabled ? 'text-green-400' : 'text-red-400'}`}
                              >
                                Order: {section.section_order}
                              </Badge>
                              
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => toggleSectionVisibility(section.id, section.is_enabled)}
                                className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                              >
                                {section.is_enabled ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                              </Button>

                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setEditingSection(section)}
                                className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>

                          {section.description && (
                            <p className="text-gray-300 text-sm mt-2 ml-8 pl-3">
                              {section.description}
                            </p>
                          )}
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </CardContent>
      </Card>

      <div className="bg-gray-800/50 p-4 rounded-lg">
        <h4 className="text-gold font-semibold mb-2">💡 Homepage Editor Tips:</h4>
        <div className="space-y-1 text-sm text-gray-300">
          <p>🔄 <strong>Reorder:</strong> Drag sections up or down to change their position on the homepage</p>
          <p>👁️ <strong>Visibility:</strong> Use the eye icon to show/hide sections without deleting them</p>
          <p>✏️ <strong>Edit:</strong> Click the edit icon to customize titles, descriptions, and styling</p>
          <p>🎨 <strong>Colors:</strong> Customize background and text colors for each section</p>
          <p>🔘 <strong>Buttons:</strong> Configure button text and actions for hero and contact sections</p>
        </div>
      </div>
    </div>
  );
};

export default HomepageEditor;