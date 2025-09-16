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
import { 
  Plus, 
  Edit, 
  Trash2, 
  Coffee, 
  Calendar, 
  Clock, 
  User,
  AlertCircle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';
import { format } from 'date-fns';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BreakManager = ({ token, staff, onRefresh }) => {
  const [breaks, setBreaks] = useState([]);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingBreak, setEditingBreak] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filters, setFilters] = useState({
    staff_id: '',
    start_date: '',
    end_date: ''
  });
  const [newBreak, setNewBreak] = useState({
    staff_id: '',
    start_date: '',
    end_date: '',
    start_time: '12:00',
    end_time: '13:00',
    break_type: 'break',
    reason: '',
    is_recurring: false,
    recurring_days: []
  });

  const breakTypes = [
    { value: 'break', label: 'Break', icon: Coffee, color: 'bg-blue-500' },
    { value: 'lunch', label: 'Lunch', icon: Coffee, color: 'bg-green-500' },
    { value: 'meeting', label: 'Meeting', icon: User, color: 'bg-purple-500' },
    { value: 'vacation', label: 'Vacation', icon: Calendar, color: 'bg-orange-500' },
    { value: 'sick', label: 'Sick Leave', icon: AlertCircle, color: 'bg-red-500' },
    { value: 'other', label: 'Other', icon: Clock, color: 'bg-gray-500' }
  ];

  const weekDays = [
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
  ];

  useEffect(() => {
    fetchBreaks();
  }, []);

  const fetchBreaks = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.staff_id) params.append('staff_id', filters.staff_id);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      
      const response = await axios.get(`${API}/staff-breaks?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBreaks(response.data);
    } catch (error) {
      console.error('Error fetching breaks:', error);
      setError('Failed to fetch breaks');
    }
  };

  const handleAddBreak = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/staff-breaks`, newBreak, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNewBreak({
        staff_id: '',
        start_date: '',
        end_date: '',
        start_time: '12:00',
        end_time: '13:00',
        break_type: 'break',
        reason: '',
        is_recurring: false,
        recurring_days: []
      });
      setShowAddDialog(false);
      setSuccess('Break scheduled successfully');
      fetchBreaks();
      onRefresh();
    } catch (error) {
      console.error('Error adding break:', error);
      setError(error.response?.data?.detail || 'Failed to schedule break');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateBreak = async (breakId, updatedData) => {
    try {
      setLoading(true);
      await axios.put(`${API}/staff-breaks/${breakId}`, updatedData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEditingBreak(null);
      setSuccess('Break updated successfully');
      fetchBreaks();
      onRefresh();
    } catch (error) {
      console.error('Error updating break:', error);
      setError(error.response?.data?.detail || 'Failed to update break');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBreak = async (breakId) => {
    if (window.confirm('Are you sure you want to delete this break?')) {
      try {
        await axios.delete(`${API}/staff-breaks/${breakId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSuccess('Break deleted successfully');
        fetchBreaks();
        onRefresh();
      } catch (error) {
        console.error('Error deleting break:', error);
        setError(error.response?.data?.detail || 'Failed to delete break');
      }
    }
  };

  const getStaffName = (staffId) => {
    const staffMember = staff.find(s => s.id === staffId);
    return staffMember ? staffMember.name : 'Unknown';
  };

  const getBreakTypeBadge = (breakType) => {
    const type = breakTypes.find(t => t.value === breakType) || breakTypes[0];
    const IconComponent = type.icon;
    
    return (
      <Badge className={`${type.color} text-white flex items-center gap-1`}>
        <IconComponent className="h-3 w-3" />
        {type.label}
      </Badge>
    );
  };

  const formatDateRange = (startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (startDate === endDate) {
      return start.toLocaleDateString('da-DK');
    } else {
      return `${start.toLocaleDateString('da-DK')} - ${end.toLocaleDateString('da-DK')}`;
    }
  };

  const clearMessages = () => {
    setError('');
    setSuccess('');
  };

  const BreakForm = ({ breakData, setBreakData, onSubmit, onCancel, loading, title, isEditing = false }) => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gold">{title}</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-gold">Staff Member *</Label>
          <Select 
            value={breakData.staff_id} 
            onValueChange={(value) => setBreakData(prev => ({ ...prev, staff_id: value }))}
          >
            <SelectTrigger className="bg-black/50 border-gold/30 text-white">
              <SelectValue placeholder="Select staff member" />
            </SelectTrigger>
            <SelectContent className="bg-gray-900 border-gold/20">
              {staff.map(member => (
                <SelectItem key={member.id} value={member.id}>
                  {member.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label className="text-gold">Break Type</Label>
          <Select 
            value={breakData.break_type} 
            onValueChange={(value) => setBreakData(prev => ({ ...prev, break_type: value }))}
          >
            <SelectTrigger className="bg-black/50 border-gold/30 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-gray-900 border-gold/20">
              {breakTypes.map(type => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-gold">Start Date *</Label>
          <Input
            type="date"
            value={breakData.start_date}
            onChange={(e) => setBreakData(prev => ({ ...prev, start_date: e.target.value }))}
            className="bg-black/50 border-gold/30 text-white"
            min={new Date().toISOString().split('T')[0]}
          />
        </div>
        <div>
          <Label className="text-gold">End Date *</Label>
          <Input
            type="date"
            value={breakData.end_date}
            onChange={(e) => setBreakData(prev => ({ ...prev, end_date: e.target.value }))}
            className="bg-black/50 border-gold/30 text-white"
            min={breakData.start_date || new Date().toISOString().split('T')[0]}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-gold">Start Time *</Label>
          <Input
            type="time"
            value={breakData.start_time}
            onChange={(e) => setBreakData(prev => ({ ...prev, start_time: e.target.value }))}
            className="bg-black/50 border-gold/30 text-white"
          />
        </div>
        <div>
          <Label className="text-gold">End Time *</Label>
          <Input
            type="time"
            value={breakData.end_time}
            onChange={(e) => setBreakData(prev => ({ ...prev, end_time: e.target.value }))}
            className="bg-black/50 border-gold/30 text-white"
          />
        </div>
      </div>

      <div>
        <Label className="text-gold">Reason (optional)</Label>
        <Textarea
          value={breakData.reason}
          onChange={(e) => setBreakData(prev => ({ ...prev, reason: e.target.value }))}
          className="bg-black/50 border-gold/30 text-white"
          placeholder="Reason for break..."
          rows={3}
        />
      </div>

      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Checkbox
            checked={breakData.is_recurring}
            onCheckedChange={(checked) => setBreakData(prev => ({ ...prev, is_recurring: checked }))}
            className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
          />
          <Label className="text-gold">Recurring Break</Label>
        </div>

        {breakData.is_recurring && (
          <div>
            <Label className="text-gold">Recurring Days</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {weekDays.map(day => (
                <Badge
                  key={day}
                  variant={breakData.recurring_days.includes(day) ? "default" : "outline"}
                  className={`cursor-pointer ${
                    breakData.recurring_days.includes(day) 
                      ? "bg-gold text-black" 
                      : "border-gold/50 text-gold hover:bg-gold hover:text-black"
                  }`}
                  onClick={() => {
                    const days = breakData.recurring_days.includes(day)
                      ? breakData.recurring_days.filter(d => d !== day)
                      : [...breakData.recurring_days, day];
                    setBreakData(prev => ({ ...prev, recurring_days: days }));
                  }}
                >
                  {day.charAt(0).toUpperCase() + day.slice(1, 3)}
                </Badge>
              ))}
            </div>
          </div>
        )}
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
          disabled={loading || !breakData.staff_id || !breakData.start_date || !breakData.end_date}
          className="bg-gold text-black hover:bg-gold/90"
        >
          {loading ? 'Saving...' : 'Save Break'}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">Break Management</h2>
        <div className="flex space-x-2">
          <Button onClick={fetchBreaks} variant="outline" className="border-gold/50 text-gold">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button className="bg-gold text-black hover:bg-gold/90" onClick={clearMessages}>
                <Plus className="h-4 w-4 mr-2" />
                Schedule Break
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-gray-900 border-gold/20 max-w-2xl">
              <DialogHeader>
                <DialogTitle className="text-gold">Schedule New Break</DialogTitle>
              </DialogHeader>
              <BreakForm
                breakData={newBreak}
                setBreakData={setNewBreak}
                onSubmit={handleAddBreak}
                onCancel={() => setShowAddDialog(false)}
                loading={loading}
                title=""
                isEditing={false}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <Card className="bg-gray-900/50 border-gold/20">
        <CardHeader>
          <CardTitle className="text-gold">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label className="text-gold">Staff Member</Label>
              <Select value={filters.staff_id} onValueChange={(value) => setFilters(prev => ({ ...prev, staff_id: value }))}>
                <SelectTrigger className="bg-black/50 border-gold/30 text-white">
                  <SelectValue placeholder="All staff" />
                </SelectTrigger>
                <SelectContent className="bg-gray-900 border-gold/20">
                  <SelectItem value="">All Staff</SelectItem>
                  {staff.map(member => (
                    <SelectItem key={member.id} value={member.id}>
                      {member.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gold">Start Date</Label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
                className="bg-black/50 border-gold/30 text-white"
              />
            </div>
            <div>
              <Label className="text-gold">End Date</Label>
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value }))}
                className="bg-black/50 border-gold/30 text-white"
              />
            </div>
          </div>
          <div className="mt-4">
            <Button onClick={fetchBreaks} className="bg-gold text-black hover:bg-gold/90">
              Apply Filters
            </Button>
          </div>
        </CardContent>
      </Card>

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

      {/* Breaks List */}
      <div className="grid gap-4">
        {breaks.map((breakItem) => (
          <Card key={breakItem.id} className="bg-gray-900/50 border-gold/20">
            <CardContent className="p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gold">
                      {getStaffName(breakItem.staff_id)}
                    </h3>
                    {getBreakTypeBadge(breakItem.break_type)}
                    {breakItem.is_recurring && (
                      <Badge variant="outline" className="border-purple-500 text-purple-400">
                        Recurring
                      </Badge>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-gray-400">Date</p>
                      <p className="text-white font-medium">
                        {formatDateRange(breakItem.start_date, breakItem.end_date)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Time</p>
                      <p className="text-white font-medium">
                        {breakItem.start_time.substring(0, 5)} - {breakItem.end_time.substring(0, 5)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Duration</p>
                      <p className="text-white font-medium">
                        {(() => {
                          const start = new Date(`2000-01-01T${breakItem.start_time}`);
                          const end = new Date(`2000-01-01T${breakItem.end_time}`);
                          const diff = (end - start) / (1000 * 60);
                          return `${diff} min`;
                        })()}
                      </p>
                    </div>
                  </div>

                  {breakItem.reason && (
                    <div className="mt-3">
                      <p className="text-gray-400 text-sm">Reason</p>
                      <p className="text-gray-300 text-sm italic">"{breakItem.reason}"</p>
                    </div>
                  )}

                  {breakItem.is_recurring && breakItem.recurring_days.length > 0 && (
                    <div className="mt-3">
                      <p className="text-gray-400 text-sm">Recurring Days</p>
                      <div className="flex gap-1 mt-1">
                        {breakItem.recurring_days.map(day => (
                          <Badge key={day} variant="outline" className="border-purple-500 text-purple-400 text-xs">
                            {day.charAt(0).toUpperCase() + day.slice(1, 3)}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingBreak(breakItem)}
                    className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteBreak(breakItem.id)}
                    className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {breaks.length === 0 && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardContent className="text-center py-12">
              <Coffee className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-300 mb-2">No breaks scheduled</h3>
              <p className="text-gray-400">Schedule the first break to get started</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit Break Dialog */}
      {editingBreak && (
        <Dialog open={!!editingBreak} onOpenChange={() => setEditingBreak(null)}>
          <DialogContent className="bg-gray-900 border-gold/20 max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-gold">Edit Break</DialogTitle>
            </DialogHeader>
            <BreakForm
              breakData={editingBreak}
              setBreakData={setEditingBreak}
              onSubmit={() => handleUpdateBreak(editingBreak.id, editingBreak)}
              onCancel={() => setEditingBreak(null)}
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

export default BreakManager;