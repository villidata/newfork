import React, { useState, useEffect } from 'react';
import { Calendar } from './ui/calendar';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Clock, User, Calendar as CalendarIcon, CreditCard, MapPin, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { format } from 'date-fns';
import { da } from 'date-fns/locale';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BookingSystem = ({ onClose }) => {
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedStaff, setSelectedStaff] = useState('');
  const [selectedServices, setSelectedServices] = useState([]);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState('');
  const [currentStep, setCurrentStep] = useState(1);
  const [staff, setStaff] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  // Customer info
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: '',
    notes: ''
  });
  
  // Payment info
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [bookingConfirmed, setBookingConfirmed] = useState(false);

  useEffect(() => {
    fetchStaff();
    fetchServices();
  }, []);

  useEffect(() => {
    if (selectedDate && selectedStaff) {
      fetchAvailableSlots();
    }
  }, [selectedDate, selectedStaff]);

  const fetchStaff = async () => {
    try {
      const response = await axios.get(`${API}/staff`);
      setStaff(response.data);
    } catch (error) {
      console.error('Failed to fetch staff:', error);
      setError('Kunne ikke hente frisører');
    }
  };

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services`);
      setServices(response.data);
    } catch (error) {
      console.error('Failed to fetch services:', error);
      setError('Kunne ikke hente tjenester');
    }
  };

  const fetchAvailableSlots = async () => {
    try {
      setLoading(true);
      const dateStr = selectedDate.toISOString().split('T')[0];
      const response = await axios.get(`${API}/bookings/available-slots?staff_id=${selectedStaff}&date=${dateStr}`);
      setAvailableSlots(response.data.available_slots);
      setSelectedSlot('');
    } catch (error) {
      console.error('Failed to fetch available slots:', error);
      setError('Kunne ikke hente ledige tider');
    } finally {
      setLoading(false);
    }
  };

  const handleServiceToggle = (serviceId) => {
    setSelectedServices(prev => {
      if (prev.includes(serviceId)) {
        return prev.filter(id => id !== serviceId);
      } else {
        return [...prev, serviceId];
      }
    });
  };

  const getTotalPrice = () => {
    return selectedServices.reduce((total, serviceId) => {
      const service = services.find(s => s.id === serviceId);
      return total + (service ? service.price : 0);
    }, 0);
  };

  const getTotalDuration = () => {
    return selectedServices.reduce((total, serviceId) => {
      const service = services.find(s => s.id === serviceId);
      return total + (service ? service.duration_minutes : 0);
    }, 0);
  };

  const handleNextStep = () => {
    if (currentStep === 1 && (!selectedDate || !selectedStaff)) {
      setError('Vælg venligst dato og frisør');
      return;
    }
    if (currentStep === 2 && selectedServices.length === 0) {
      setError('Vælg venligst mindst én tjeneste');
      return;
    }
    if (currentStep === 3 && !selectedSlot) {
      setError('Vælg venligst et tidspunkt');
      return;
    }
    if (currentStep === 4 && (!customerInfo.name || !customerInfo.email || !customerInfo.phone)) {
      setError('Udfyld venligst alle påkrævede felter');
      return;
    }
    
    setError('');
    setCurrentStep(prev => prev + 1);
  };

  const handleBooking = async () => {
    try {
      setLoading(true);
      setError('');

      // First register/login the customer
      let customerId;
      try {
        const registerResponse = await axios.post(`${API}/auth/register`, {
          ...customerInfo,
          password: 'temp_password_' + Date.now() // Temporary password
        });
        customerId = registerResponse.data.user.id;
      } catch (error) {
        if (error.response?.status === 400) {
          // User exists, try to login (simplified for MVP)
          customerId = 'existing_user_' + customerInfo.email;
        } else {
          throw error;
        }
      }

      // Create booking
      const bookingData = {
        customer_id: customerId,
        staff_id: selectedStaff,
        services: selectedServices,
        booking_date: selectedDate.toISOString().split('T')[0],
        booking_time: selectedSlot + ':00',
        payment_method: paymentMethod,
        notes: customerInfo.notes
      };

      const response = await axios.post(`${API}/bookings`, bookingData);
      
      if (paymentMethod === 'paypal') {
        // Redirect to PayPal (placeholder)
        const paypalResponse = await axios.post(`${API}/payments/paypal/create`, {
          booking_id: response.data.id
        });
        console.log('PayPal payment created:', paypalResponse.data);
      }

      setBookingConfirmed(true);
      setSuccess(true);
      setCurrentStep(6);
      
    } catch (error) {
      console.error('Booking failed:', error);
      setError('Booking mislykkedes. Prøv igen.');
    } finally {
      setLoading(false);
    }
  };

  const selectedStaffMember = staff.find(s => s.id === selectedStaff);

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-black border-gold/30">
        <DialogHeader>
          <DialogTitle className="text-2xl text-gold font-serif flex items-center">
            <CalendarIcon className="mr-2" />
            Book din tid hos Frisor LaFata
          </DialogTitle>
          <DialogDescription className="text-gray-300">
            Trin {currentStep} af 5 - {currentStep === 1 ? 'Vælg dato og frisør' : 
                                      currentStep === 2 ? 'Vælg tjenester' :
                                      currentStep === 3 ? 'Vælg tidspunkt' :
                                      currentStep === 4 ? 'Dine oplysninger' :
                                      currentStep === 5 ? 'Bekræft booking' : 'Booking bekræftet'}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <Alert className="border-red-500 bg-red-500/10">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <AlertDescription className="text-red-400">{error}</AlertDescription>
          </Alert>
        )}

        {success && currentStep === 6 && (
          <div className="text-center py-8">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-gold mb-2">Booking bekræftet!</h3>
            <p className="text-gray-300 mb-4">
              Din booking er blevet bekræftet. Du vil modtage en bekræftelse på email.
            </p>
            <Button onClick={onClose} className="bg-gold text-black hover:bg-gold/90">
              Luk
            </Button>
          </div>
        )}

        {currentStep === 1 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-gray-900/50 border-gold/20">
              <CardHeader>
                <CardTitle className="text-gold flex items-center">
                  <CalendarIcon className="mr-2 h-5 w-5" />
                  Vælg dato
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={setSelectedDate}
                  disabled={(date) => date < new Date() || date.getDay() === 0} // Disable past dates and Sundays
                  locale={da}
                  className="rounded-md border border-gold/20"
                />
              </CardContent>
            </Card>

            <Card className="bg-gray-900/50 border-gold/20">
              <CardHeader>
                <CardTitle className="text-gold flex items-center">
                  <User className="mr-2 h-5 w-5" />
                  Vælg frisør
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {staff.map((member) => (
                  <div
                    key={member.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedStaff === member.id
                        ? 'border-gold bg-gold/10'
                        : 'border-gold/20 hover:border-gold/50'
                    }`}
                    onClick={() => setSelectedStaff(member.id)}
                  >
                    <h4 className="font-semibold text-gold">{member.name}</h4>
                    <p className="text-gray-300 text-sm">{member.specialty}</p>
                    <Badge variant="outline" className="border-gold/50 text-gold text-xs mt-1">
                      {member.experience} erfaring
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        )}

        {currentStep === 2 && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold">Vælg tjenester</CardTitle>
              <p className="text-gray-300">Du kan vælge flere tjenester</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {services.map((service) => (
                  <div
                    key={service.id}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      selectedServices.includes(service.id)
                        ? 'border-gold bg-gold/10'
                        : 'border-gold/20 hover:border-gold/50'
                    }`}
                    onClick={() => handleServiceToggle(service.id)}
                  >
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        checked={selectedServices.includes(service.id)}
                        className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                      />
                      <div className="flex-1">
                        <h4 className="font-semibold text-gold">{service.name}</h4>
                        <div className="flex items-center text-gray-300 text-sm mt-1">
                          <Clock className="h-3 w-3 mr-1" />
                          {service.duration_minutes} min
                        </div>
                        <p className="text-gold font-bold">{service.price} DKK</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {selectedServices.length > 0 && (
                <div className="mt-6 p-4 bg-gold/10 rounded-lg border border-gold/30">
                  <h4 className="font-semibold text-gold mb-2">Valgte tjenester:</h4>
                  <div className="space-y-2">
                    {selectedServices.map(serviceId => {
                      const service = services.find(s => s.id === serviceId);
                      return service ? (
                        <div key={serviceId} className="flex justify-between text-gray-300">
                          <span>{service.name}</span>
                          <span>{service.price} DKK</span>
                        </div>
                      ) : null;
                    })}
                  </div>
                  <Separator className="my-2 bg-gold/20" />
                  <div className="flex justify-between font-bold text-gold">
                    <span>Total: {getTotalDuration()} min</span>
                    <span>{getTotalPrice()} DKK</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {currentStep === 3 && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold flex items-center">
                <Clock className="mr-2 h-5 w-5" />
                Vælg tidspunkt
              </CardTitle>
              <p className="text-gray-300">
                {selectedDate && format(selectedDate, 'EEEE d. MMMM yyyy', { locale: da })} hos {selectedStaffMember?.name}
              </p>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-gray-300">Indlæser ledige tider...</p>
              ) : availableSlots.length > 0 ? (
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  {availableSlots.map((slot) => (
                    <Button
                      key={slot}
                      variant={selectedSlot === slot ? "default" : "outline"}
                      className={`${
                        selectedSlot === slot
                          ? 'bg-gold text-black'
                          : 'border-gold/50 text-gold hover:bg-gold hover:text-black'
                      }`}
                      onClick={() => setSelectedSlot(slot)}
                    >
                      {slot}
                    </Button>
                  ))}
                </div>
              ) : (
                <p className="text-gray-300">Ingen ledige tider på denne dag. Vælg venligst en anden dato.</p>
              )}
            </CardContent>
          </Card>
        )}

        {currentStep === 4 && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold">Dine oplysninger</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name" className="text-gold">Navn *</Label>
                  <Input
                    id="name"
                    value={customerInfo.name}
                    onChange={(e) => setCustomerInfo(prev => ({ ...prev, name: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="Dit fulde navn"
                  />
                </div>
                <div>
                  <Label htmlFor="phone" className="text-gold">Telefon *</Label>
                  <Input
                    id="phone"
                    value={customerInfo.phone}
                    onChange={(e) => setCustomerInfo(prev => ({ ...prev, phone: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="+45 12 34 56 78"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="email" className="text-gold">Email *</Label>
                <Input
                  id="email"
                  type="email"
                  value={customerInfo.email}
                  onChange={(e) => setCustomerInfo(prev => ({ ...prev, email: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="din@email.dk"
                />
              </div>
              <div>
                <Label htmlFor="notes" className="text-gold">Bemærkninger (valgfrit)</Label>
                <Textarea
                  id="notes"
                  value={customerInfo.notes}
                  onChange={(e) => setCustomerInfo(prev => ({ ...prev, notes: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="Særlige ønsker eller bemærkninger..."
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {currentStep === 5 && (
          <div className="space-y-6">
            <Card className="bg-gray-900/50 border-gold/20">
              <CardHeader>
                <CardTitle className="text-gold">Bekræft din booking</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div>
                      <Label className="text-gold">Dato & Tid:</Label>
                      <p className="text-white">
                        {selectedDate && format(selectedDate, 'EEEE d. MMMM yyyy', { locale: da })} kl. {selectedSlot}
                      </p>
                    </div>
                    <div>
                      <Label className="text-gold">Frisør:</Label>
                      <p className="text-white">{selectedStaffMember?.name}</p>
                    </div>
                    <div>
                      <Label className="text-gold">Kunde:</Label>
                      <p className="text-white">{customerInfo.name}</p>
                      <p className="text-gray-300 text-sm">{customerInfo.email}</p>
                      <p className="text-gray-300 text-sm">{customerInfo.phone}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <Label className="text-gold">Tjenester:</Label>
                      {selectedServices.map(serviceId => {
                        const service = services.find(s => s.id === serviceId);
                        return service ? (
                          <div key={serviceId} className="flex justify-between text-white">
                            <span>{service.name}</span>
                            <span>{service.price} DKK</span>
                          </div>
                        ) : null;
                      })}
                      <Separator className="my-2 bg-gold/20" />
                      <div className="flex justify-between font-bold text-gold">
                        <span>I alt ({getTotalDuration()} min):</span>
                        <span>{getTotalPrice()} DKK</span>
                      </div>
                    </div>
                  </div>
                </div>

                <Separator className="bg-gold/20" />

                <div>
                  <Label className="text-gold mb-3 block">Betalingsmetode:</Label>
                  <div className="space-y-3">
                    <div
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        paymentMethod === 'cash'
                          ? 'border-gold bg-gold/10'
                          : 'border-gold/20 hover:border-gold/50'
                      }`}
                      onClick={() => setPaymentMethod('cash')}
                    >
                      <div className="flex items-center space-x-3">
                        <MapPin className="h-5 w-5 text-gold" />
                        <div>
                          <h4 className="font-semibold text-gold">Betal i salonen</h4>
                          <p className="text-gray-300 text-sm">Kontant eller kort ved ankomst</p>
                        </div>
                      </div>
                    </div>
                    
                    <div
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        paymentMethod === 'paypal'
                          ? 'border-gold bg-gold/10'
                          : 'border-gold/20 hover:border-gold/50'
                      }`}
                      onClick={() => setPaymentMethod('paypal')}
                    >
                      <div className="flex items-center space-x-3">
                        <CreditCard className="h-5 w-5 text-gold" />
                        <div>
                          <h4 className="font-semibold text-gold">PayPal</h4>
                          <p className="text-gray-300 text-sm">Betal online med PayPal</p>
                          <Badge variant="outline" className="border-blue-500 text-blue-400 text-xs mt-1">
                            Sandbox Mode
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {currentStep < 6 && (
          <div className="flex justify-between pt-4 border-t border-gold/20">
            <Button
              variant="outline"
              onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))}
              disabled={currentStep === 1}
              className="border-gold/50 text-gold hover:bg-gold hover:text-black"
            >
              Tilbage
            </Button>
            
            {currentStep < 5 ? (
              <Button
                onClick={handleNextStep}
                disabled={loading}
                className="bg-gold text-black hover:bg-gold/90"
              >
                Næste
              </Button>
            ) : (
              <Button
                onClick={handleBooking}
                disabled={loading}
                className="bg-gold text-black hover:bg-gold/90"
              >
                {loading ? 'Booker...' : 'Bekræft booking'}
              </Button>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default BookingSystem;