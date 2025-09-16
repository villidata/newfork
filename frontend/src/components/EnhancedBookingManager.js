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
import { Calendar, Edit, Trash2, CheckCircle, Clock, User, AlertCircle, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EnhancedBookingManager = ({ token, staff, services, onRefresh }) => {
  const [bookings, setBookings] = useState([]);
  const [editingBooking, setEditingBooking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const response = await axios.get(`${API}/bookings`, { headers });
      setBookings(response.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
    } catch (error) {
      console.error('Error fetching bookings:', error);
      setError('Failed to fetch bookings');
    }
  };

  const handleConfirmBooking = async (bookingId) => {
    try {
      setLoading(true);
      await axios.put(`${API}/bookings/${bookingId}/confirm`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Booking confirmed and customer notified!');
      fetchBookings();
      onRefresh();
    } catch (error) {
      console.error('Error confirming booking:', error);
      setError('Failed to confirm booking');
    } finally {
      setLoading(false);
    }
  };

  const handleRescheduleBooking = async (bookingId, newDate, newTime, adminNotes) => {
    try {
      setLoading(true);
      await axios.put(`${API}/bookings/${bookingId}`, {
        booking_date: newDate,
        booking_time: newTime,
        admin_notes: adminNotes
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Booking rescheduled and customer notified!');
      setEditingBooking(null);
      fetchBookings();
      onRefresh();
    } catch (error) {
      console.error('Error rescheduling booking:', error);
      setError(error.response?.data?.detail || 'Failed to reschedule booking');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateBookingStatus = async (bookingId, status) => {
    try {
      setLoading(true);
      await axios.put(`${API}/bookings/${bookingId}`, { status }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess(`Booking status updated to ${status}`);
      fetchBookings();
      onRefresh();
    } catch (error) {
      console.error('Error updating booking status:', error);
      setError('Failed to update booking status');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBooking = async (bookingId) => {
    if (window.confirm('Are you sure you want to delete this booking?')) {
      try {
        await axios.delete(`${API}/bookings/${bookingId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSuccess('Booking deleted successfully');
        fetchBookings();
        onRefresh();
      } catch (error) {
        console.error('Error deleting booking:', error);
        setError('Failed to delete booking');
      }
    }
  };

  const getStaffName = (staffId) => {
    const staffMember = staff.find(s => s.id === staffId);
    return staffMember ? staffMember.name : 'Unknown';
  };

  const getServiceNames = (serviceIds) => {
    return serviceIds.map(id => {
      const service = services.find(s => s.id === id);
      return service ? service.name : 'Unknown service';
    }).join(', ');
  };

  const formatDate = (dateStr) => {
    try {
      return format(new Date(dateStr), 'dd/MM/yyyy');
    } catch {
      return dateStr;
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'pending': { color: 'bg-yellow-500', text: 'Pending', icon: Clock },
      'confirmed': { color: 'bg-green-500', text: 'Confirmed', icon: CheckCircle },
      'cancelled': { color: 'bg-red-500', text: 'Cancelled', icon: AlertCircle },
      'completed': { color: 'bg-blue-500', text: 'Completed', icon: CheckCircle },
      'rescheduled': { color: 'bg-purple-500', text: 'Rescheduled', icon: RefreshCw }
    };
    const config = statusConfig[status] || { color: 'bg-gray-500', text: status, icon: Clock };
    const IconComponent = config.icon;
    
    return (
      <Badge className={`${config.color} text-white flex items-center gap-1`}>
        <IconComponent className="h-3 w-3" />
        {config.text}
      </Badge>
    );
  };

  const getPaymentStatusBadge = (status) => {
    const statusConfig = {
      'paid': { color: 'bg-green-500', text: 'Paid' },
      'pending': { color: 'bg-yellow-500', text: 'Pending' },
      'cancelled': { color: 'bg-red-500', text: 'Cancelled' }
    };
    const config = statusConfig[status] || { color: 'bg-gray-500', text: status };
    return (
      <Badge className={`${config.color} text-white`}>
        {config.text}
      </Badge>
    );
  };

  const RescheduleDialog = ({ booking, onClose, onReschedule }) => {
    const [newDate, setNewDate] = useState(booking.booking_date);
    const [newTime, setNewTime] = useState(booking.booking_time.substring(0, 5));
    const [adminNotes, setAdminNotes] = useState('');

    const handleSubmit = () => {
      if (!newDate || !newTime) {
        setError('Please select both date and time');
        return;
      }
      onReschedule(booking.id, newDate, newTime + ':00', adminNotes);
    };

    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="bg-gray-900 border-gold/20 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-gold">Reschedule Booking</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-gold">Customer: {booking.customer_name}</Label>
              <p className="text-gray-300 text-sm">Current: {formatDate(booking.booking_date)} at {booking.booking_time.substring(0, 5)}</p>
            </div>
            <div>
              <Label className="text-gold">New Date</Label>
              <Input
                type="date"
                value={newDate}
                onChange={(e) => setNewDate(e.target.value)}
                className="bg-black/50 border-gold/30 text-white"
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div>
              <Label className="text-gold">New Time</Label>
              <Input
                type="time"
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                className="bg-black/50 border-gold/30 text-white"
              />
            </div>
            <div>
              <Label className="text-gold">Reason for Change (will be sent to customer)</Label>
              <Textarea
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                className="bg-black/50 border-gold/30 text-white"
                placeholder="e.g., Staff availability change, emergency..."
                rows={3}
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={onClose} className="border-gold/50 text-gold">
                Cancel
              </Button>
              <Button onClick={handleSubmit} className="bg-gold text-black hover:bg-gold/90">
                Reschedule & Notify Customer
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gold">Enhanced Booking Management</h2>
        <Button onClick={fetchBookings} className="bg-gold text-black hover:bg-gold/90">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
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
        {bookings.map((booking) => (
          <Card key={booking.id} className="bg-gray-900/50 border-gold/20">
            <CardContent className="p-6">
              <div className="flex flex-wrap justify-between items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gold">{booking.customer_name}</h3>
                    {getStatusBadge(booking.status)}
                    {getPaymentStatusBadge(booking.payment_status)}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-gray-400">Date & Time</p>
                      <p className="text-white font-medium">
                        {formatDate(booking.booking_date)} at {booking.booking_time.substring(0, 5)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Customer</p>
                      <p className="text-white">{booking.customer_email}</p>
                      <p className="text-gray-300">{booking.customer_phone}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Staff</p>
                      <p className="text-white">{getStaffName(booking.staff_id)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Services</p>
                      <p className="text-white">{getServiceNames(booking.services)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Price</p>
                      <p className="text-white font-semibold">{booking.total_price} DKK</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Duration</p>
                      <p className="text-white">{booking.total_duration} min</p>
                    </div>
                  </div>

                  {booking.notes && (
                    <div className="mt-3">
                      <p className="text-gray-400 text-sm">Customer Notes</p>
                      <p className="text-gray-300 text-sm italic">"{booking.notes}"</p>
                    </div>
                  )}

                  {booking.admin_notes && (
                    <div className="mt-2">
                      <p className="text-gray-400 text-sm">Admin Notes</p>
                      <p className="text-gold text-sm">"{booking.admin_notes}"</p>
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2">
                  {booking.status === 'pending' && (
                    <Button
                      size="sm"
                      onClick={() => handleConfirmBooking(booking.id)}
                      disabled={loading}
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Confirm
                    </Button>
                  )}

                  {(booking.status === 'pending' || booking.status === 'confirmed') && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingBooking(booking)}
                      className="border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white"
                    >
                      <RefreshCw className="h-3 w-3 mr-1" />
                      Reschedule
                    </Button>
                  )}

                  <Select onValueChange={(status) => handleUpdateBookingStatus(booking.id, status)} defaultValue={booking.status}>
                    <SelectTrigger className="w-32 bg-black/50 border-gold/30 text-white text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-gray-900 border-gold/20">
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="confirmed">Confirmed</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="cancelled">Cancelled</SelectItem>
                    </SelectContent>
                  </Select>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteBooking(booking.id)}
                    className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {bookings.length === 0 && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardContent className="text-center py-12">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-300 mb-2">No bookings yet</h3>
              <p className="text-gray-400">Bookings will appear here when customers make reservations</p>
            </CardContent>
          </Card>
        )}
      </div>

      {editingBooking && (
        <RescheduleDialog
          booking={editingBooking}
          onClose={() => setEditingBooking(null)}
          onReschedule={handleRescheduleBooking}
        />
      )}
    </div>
  );
};

export default EnhancedBookingManager;