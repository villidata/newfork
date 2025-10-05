import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
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
  const [bookingType, setBookingType] = useState('individual'); // 'individual' or 'corporate'
  
  // Customer info
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: '',
    notes: ''
  });
  
  // Home service info
  const [isHomeService, setIsHomeService] = useState(false);
  const [homeServiceInfo, setHomeServiceInfo] = useState({
    address: '',
    city: '',
    postalCode: '',
    specialInstructions: ''
  });

  // Corporate booking info
  const [corporateInfo, setCorporateInfo] = useState({
    companyName: '',
    contactPerson: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    postalCode: '',
    specialRequirements: '',
    travelFee: 500 // Default travel fee for corporate bookings
  });

  const [employees, setEmployees] = useState([
    { name: '', selectedServices: [], notes: '' }
  ]);
  
  // Payment info
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [bookingConfirmed, setBookingConfirmed] = useState(false);
  const [settings, setSettings] = useState({});

  useEffect(() => {
    fetchStaff();
    fetchServices();
    fetchSettings();
  }, []);

  useEffect(() => {
    if (selectedDate && selectedStaff) {
      fetchAvailableSlots();
    }
  }, [selectedDate, selectedStaff]);

  const fetchStaff = async () => {
    try {
      const response = await axios.get(`${API}/staff`);
      // Ensure response.data is always an array
      setStaff(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Failed to fetch staff:', error);
      setError('Kunne ikke hente frisører');
      setStaff([]); // Set empty array on error
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

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/public/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const fetchAvailableSlots = async () => {
    try {
      setLoading(true);
      const dateStr = selectedDate.toISOString().split('T')[0];
      const response = await axios.get(`${API}/bookings/available-slots?staff_id=${selectedStaff}&date_param=${dateStr}`);
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
    const servicesTotal = selectedServices.reduce((total, serviceId) => {
      const service = services.find(s => s.id === serviceId);
      return total + (service ? service.price : 0);
    }, 0);
    
    const homeServiceFee = isHomeService ? (settings.home_service_fee || 150) : 0;
    return servicesTotal + homeServiceFee;
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
    if (currentStep === 2) {
      if (bookingType === 'individual' && selectedServices.length === 0) {
        setError('Vælg venligst mindst én tjeneste');
        return;
      }
      if (bookingType === 'corporate') {
        const hasValidEmployees = employees.some(emp => emp.name && emp.selectedServices.length > 0);
        if (!hasValidEmployees) {
          setError('Tilføj mindst én medarbejder med navn og tjeneste');
          return;
        }
      }
    }
    if (currentStep === 3 && !selectedSlot) {
      setError('Vælg venligst et tidspunkt');
      return;
    }
    if (currentStep === 4) {
      if (bookingType === 'individual' && (!customerInfo.name || !customerInfo.email || !customerInfo.phone)) {
        setError('Udfyld venligst alle påkrævede felter');
        return;
      }
      if (bookingType === 'corporate' && (!corporateInfo.companyName || !corporateInfo.contactPerson || !corporateInfo.email || !corporateInfo.phone || !corporateInfo.address || !corporateInfo.city || !corporateInfo.postalCode)) {
        setError('Udfyld venligst alle påkrævede felter');
        return;
      }
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
        customer_name: customerInfo.name,
        customer_email: customerInfo.email,
        customer_phone: customerInfo.phone,
        staff_id: selectedStaff,
        services: selectedServices,
        booking_date: selectedDate.toISOString().split('T')[0],
        booking_time: selectedSlot + ':00',
        payment_method: paymentMethod,
        notes: customerInfo.notes,
        is_home_service: isHomeService,
        service_address: isHomeService ? homeServiceInfo.address : '',
        service_city: isHomeService ? homeServiceInfo.city : '',
        service_postal_code: isHomeService ? homeServiceInfo.postalCode : '',
        special_instructions: isHomeService ? homeServiceInfo.specialInstructions : ''
      };

      const response = await axios.post(`${API}/bookings`, bookingData);
      
      if (paymentMethod === 'paypal') {
        // Create PayPal payment
        const paypalResponse = await axios.post(`${API}/payments/paypal/create`, null, {
          params: {
            booking_id: response.data.id,
            amount: getTotalPrice()
          }
        });
        
        if (paypalResponse.data.approval_url && !paypalResponse.data.error) {
          // Redirect to PayPal for payment
          window.location.href = paypalResponse.data.approval_url;
          return; // Don't show success message yet
        } else {
          console.log('PayPal demo mode:', paypalResponse.data);
          // Continue with success flow for demo mode
        }
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

  const handleCorporateBooking = async () => {
    try {
      setLoading(true);
      setError('');

      // Prepare employee services data
      const employeeServices = employees.map(emp => ({
        employee_name: emp.name,
        service_ids: emp.selectedServices,
        notes: emp.notes || ''
      }));

      // Create corporate booking
      const corporateBookingData = {
        company_name: corporateInfo.companyName,
        company_contact_person: corporateInfo.contactPerson,
        company_email: corporateInfo.email,
        company_phone: corporateInfo.phone,
        company_address: corporateInfo.address,
        company_city: corporateInfo.city,
        company_postal_code: corporateInfo.postalCode,
        staff_id: selectedStaff,
        booking_date: selectedDate.toISOString().split('T')[0],
        booking_time: selectedSlot + ':00',
        employees: employeeServices,
        company_travel_fee: parseFloat(corporateInfo.travelFee) || 0,
        payment_method: paymentMethod,
        special_requirements: corporateInfo.specialRequirements
      };

      const response = await axios.post(`${API}/corporate-bookings`, corporateBookingData);
      
      setBookingConfirmed(true);
      setSuccess(true);
      setCurrentStep(6);
      
    } catch (error) {
      console.error('Corporate booking failed:', error);
      setError('Corporate booking mislykkedes. Prøv igen.');
    } finally {
      setLoading(false);
    }
  };

  const addEmployee = () => {
    setEmployees([...employees, { name: '', selectedServices: [], notes: '' }]);
  };

  const removeEmployee = (index) => {
    if (employees.length > 1) {
      setEmployees(employees.filter((_, i) => i !== index));
    }
  };

  const updateEmployee = (index, field, value) => {
    const updated = [...employees];
    updated[index] = { ...updated[index], [field]: value };
    setEmployees(updated);
  };

  const updateEmployeeServices = (index, serviceId, checked) => {
    const updated = [...employees];
    if (checked) {
      updated[index].selectedServices = [...updated[index].selectedServices, serviceId];
    } else {
      updated[index].selectedServices = updated[index].selectedServices.filter(id => id !== serviceId);
    }
    setEmployees(updated);
  };

  const getCorporateTotalPrice = () => {
    const serviceIds = employees.flatMap(emp => emp.selectedServices);
    const servicesPrice = serviceIds.reduce((total, serviceId) => {
      const service = services.find(s => s.id === serviceId);
      return total + (service ? service.price : 0);
    }, 0);
    return servicesPrice + parseFloat(corporateInfo.travelFee || 0);
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
            {bookingType === 'individual' ? (
              `Trin ${currentStep} af 5 - ${currentStep === 1 ? 'Vælg dato og frisør' : 
                                        currentStep === 2 ? 'Vælg tjenester' :
                                        currentStep === 3 ? 'Vælg tidspunkt' :
                                        currentStep === 4 ? 'Dine oplysninger' :
                                        currentStep === 5 ? 'Bekræft booking' : 'Booking bekræftet'}`
            ) : (
              `Corporate Booking - Trin ${currentStep} af 5 - ${currentStep === 1 ? 'Vælg dato og frisør' : 
                                        currentStep === 2 ? 'Medarbejdere og tjenester' :
                                        currentStep === 3 ? 'Vælg tidspunkt' :
                                        currentStep === 4 ? 'Virksomhedsoplysninger' :
                                        currentStep === 5 ? 'Bekræft corporate booking' : 'Booking bekræftet'}`
            )}
          </DialogDescription>
        </DialogHeader>

        {/* Booking Type Selection */}
        {currentStep === 1 && (
          <div className="mb-6">
            <Tabs value={bookingType} onValueChange={setBookingType} className="w-full">
              <TabsList className="grid w-full grid-cols-2 bg-black/70 border border-gold/30 rounded-lg p-1">
                <TabsTrigger 
                  value="individual" 
                  className="data-[state=active]:bg-gold data-[state=active]:text-black data-[state=active]:font-bold text-gold font-semibold border-0 hover:bg-gold/20 transition-all duration-200"
                >
                  👤 Privat Booking
                </TabsTrigger>
                <TabsTrigger 
                  value="corporate" 
                  className="data-[state=active]:bg-gold data-[state=active]:text-black data-[state=active]:font-bold text-gold font-semibold border-0 hover:bg-gold/20 transition-all duration-200"
                >
                  🏢 Corporate Booking
                </TabsTrigger>
              </TabsList>
            </Tabs>
            
            {/* Visual indicator of selected booking type */}
            <div className="mt-4 p-3 rounded-lg border border-gold/30 bg-gold/10">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">
                  {bookingType === 'individual' ? '👤' : '🏢'}
                </span>
                <div>
                  <h3 className="text-gold font-bold">
                    {bookingType === 'individual' ? 'Privat Booking' : 'Corporate Booking'}
                  </h3>
                  <p className="text-gray-300 text-sm">
                    {bookingType === 'individual' 
                      ? 'Book en personlig frisørtime til dig selv'
                      : 'Book frisørbesøg til virksomheden for flere medarbejdere'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <Alert className="border-red-500 bg-red-500/10">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <AlertDescription className="text-red-400">{error}</AlertDescription>
          </Alert>
        )}

        {success && currentStep === 6 && (
          <div className="text-center py-8">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-gold mb-2">
              {bookingType === 'corporate' ? 'Corporate Booking bekræftet!' : 'Booking bekræftet!'}
            </h3>
            <p className="text-gray-300 mb-4">
              {bookingType === 'corporate' 
                ? 'Jeres corporate booking er blevet bekræftet. I vil modtage en bekræftelse på email.'
                : 'Din booking er blevet bekræftet. Du vil modtage en bekræftelse på email.'
              }
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

        {currentStep === 2 && bookingType === 'individual' && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold flex items-center">
                <span className="mr-2">👤</span>
                Vælg tjenester - Privat Booking
              </CardTitle>
              <p className="text-gray-300">Du kan vælge flere tjenester for din personlige booking</p>
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

        {currentStep === 2 && bookingType === 'corporate' && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold flex items-center">
                <span className="mr-2">🏢</span>
                Medarbejdere og tjenester - Corporate Booking
              </CardTitle>
              <p className="text-gray-300">Tilføj medarbejdere og vælg tjenester for hver person</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {employees.map((employee, index) => (
                <div key={index} className="p-4 bg-black/40 rounded-lg border-2 border-gold/30">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-gold font-semibold flex items-center">
                      <span className="mr-2">👤</span>
                      Medarbejder {index + 1}
                      {employee.name && (
                        <span className="ml-2 text-sm font-normal text-gray-300">({employee.name})</span>
                      )}
                    </h4>
                    {employees.length > 1 && (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => removeEmployee(index)}
                        className="border-red-500 text-red-400 hover:bg-red-500/10"
                      >
                        Fjern
                      </Button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <Label className="text-gold">Navn</Label>
                      <Input
                        value={employee.name}
                        onChange={(e) => updateEmployee(index, 'name', e.target.value)}
                        placeholder="Medarbejderens navn"
                        className="bg-black/50 border-gold/30 text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-gold">Noter (valgfrit)</Label>
                      <Input
                        value={employee.notes}
                        onChange={(e) => updateEmployee(index, 'notes', e.target.value)}
                        placeholder="Særlige ønsker"
                        className="bg-black/50 border-gold/30 text-white"
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-gold mb-2 block flex items-center">
                      <span className="mr-2">🛍️</span>
                      Vælg tjenester for {employee.name || `Medarbejder ${index + 1}`}
                    </Label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {services.map((service) => {
                        const isSelected = employee.selectedServices.includes(service.id);
                        return (
                          <div
                            key={service.id}
                            className={`p-3 rounded border-2 cursor-pointer transition-all ${
                              isSelected
                                ? 'border-gold bg-gold/20 shadow-lg transform scale-105'
                                : 'border-gold/30 hover:border-gold/60 hover:bg-gold/5'
                            }`}
                            onClick={() => updateEmployeeServices(index, service.id, !isSelected)}
                          >
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                checked={isSelected}
                                className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                              />
                              <div className="flex-1">
                                <p className={`text-sm font-medium ${isSelected ? 'text-gold font-bold' : 'text-gray-300'}`}>
                                  {service.name}
                                </p>
                                <p className={`text-xs ${isSelected ? 'text-gold/80' : 'text-gray-400'}`}>
                                  {service.duration_minutes} min - {service.price} DKK
                                </p>
                              </div>
                              {isSelected && (
                                <span className="text-gold text-lg">✓</span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ))}

              <Button 
                onClick={addEmployee}
                variant="outline"
                className="w-full border-gold/50 text-gold hover:bg-gold/10"
              >
                + Tilføj medarbejder
              </Button>

              {employees.some(emp => emp.selectedServices.length > 0) && (
                <div className="mt-6 p-4 bg-gold/10 rounded-lg border border-gold/30">
                  <h4 className="font-semibold text-gold mb-3">Oversigt:</h4>
                  <div className="space-y-3">
                    {employees.map((employee, index) => (
                      employee.selectedServices.length > 0 && (
                        <div key={index}>
                          <p className="text-gold font-medium">{employee.name || `Medarbejder ${index + 1}`}:</p>
                          <div className="ml-4 space-y-1">
                            {employee.selectedServices.map(serviceId => {
                              const service = services.find(s => s.id === serviceId);
                              return service ? (
                                <div key={serviceId} className="flex justify-between text-gray-300 text-sm">
                                  <span>{service.name}</span>
                                  <span>{service.price} DKK</span>
                                </div>
                              ) : null;
                            })}
                          </div>
                        </div>
                      )
                    ))}
                  </div>
                  <Separator className="my-3 bg-gold/20" />
                  <div className="flex justify-between font-bold text-gold">
                    <span>Total for services:</span>
                    <span>{getCorporateTotalPrice() - parseFloat(corporateInfo.travelFee || 0)} DKK</span>
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

        {currentStep === 4 && bookingType === 'individual' && (
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
              
              {/* Home Service Option */}
              {settings.home_service_enabled && (
                <div className="border-t border-gold/20 pt-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <Checkbox
                      checked={isHomeService}
                      onCheckedChange={setIsHomeService}
                      className="border-gold data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                    />
                    <Label className="text-gold font-semibold">
                      🏠 Hjemmebesøg (+{settings.home_service_fee || 150} DKK)
                    </Label>
                  </div>
                  
                  {settings.home_service_description && (
                    <p className="text-gray-300 text-sm mb-4">{settings.home_service_description}</p>
                  )}
                  
                  {isHomeService && (
                    <div className="space-y-4 mt-4 p-4 bg-black/30 rounded-lg border border-gold/20">
                      <h4 className="text-gold font-semibold">Hjemmeservice adresse</h4>
                      <div>
                        <Label htmlFor="service-address" className="text-gold">Adresse *</Label>
                        <Input
                          id="service-address"
                          value={homeServiceInfo.address}
                          onChange={(e) => setHomeServiceInfo(prev => ({ ...prev, address: e.target.value }))}
                          className="bg-black/50 border-gold/30 text-white"
                          placeholder="Gadenavn og husnummer"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="service-city" className="text-gold">By *</Label>
                          <Input
                            id="service-city"
                            value={homeServiceInfo.city}
                            onChange={(e) => setHomeServiceInfo(prev => ({ ...prev, city: e.target.value }))}
                            className="bg-black/50 border-gold/30 text-white"
                            placeholder="København"
                          />
                        </div>
                        <div>
                          <Label htmlFor="service-postal" className="text-gold">Postnummer *</Label>
                          <Input
                            id="service-postal"
                            value={homeServiceInfo.postalCode}
                            onChange={(e) => setHomeServiceInfo(prev => ({ ...prev, postalCode: e.target.value }))}
                            className="bg-black/50 border-gold/30 text-white"
                            placeholder="2100"
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="special-instructions" className="text-gold">Særlige instruktioner</Label>
                        <Textarea
                          id="special-instructions"
                          value={homeServiceInfo.specialInstructions}
                          onChange={(e) => setHomeServiceInfo(prev => ({ ...prev, specialInstructions: e.target.value }))}
                          className="bg-black/50 border-gold/30 text-white"
                          placeholder="Etage, dørtelefon, parkeringsmuligheder, etc."
                          rows={3}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {currentStep === 4 && bookingType === 'corporate' && (
          <Card className="bg-gray-900/50 border-gold/20">
            <CardHeader>
              <CardTitle className="text-gold">Virksomhedsoplysninger</CardTitle>
              <p className="text-gray-300">Oplysninger om virksomheden og kontaktperson</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="company-name" className="text-gold">Virksomhedsnavn *</Label>
                  <Input
                    id="company-name"
                    value={corporateInfo.companyName}
                    onChange={(e) => setCorporateInfo(prev => ({ ...prev, companyName: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="ABC Virksomhed ApS"
                  />
                </div>
                <div>
                  <Label htmlFor="contact-person" className="text-gold">Kontaktperson *</Label>
                  <Input
                    id="contact-person"
                    value={corporateInfo.contactPerson}
                    onChange={(e) => setCorporateInfo(prev => ({ ...prev, contactPerson: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="Fornavn Efternavn"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="company-email" className="text-gold">Email *</Label>
                  <Input
                    id="company-email"
                    type="email"
                    value={corporateInfo.email}
                    onChange={(e) => setCorporateInfo(prev => ({ ...prev, email: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="kontakt@virksomhed.dk"
                  />
                </div>
                <div>
                  <Label htmlFor="company-phone" className="text-gold">Telefon *</Label>
                  <Input
                    id="company-phone"
                    value={corporateInfo.phone}
                    onChange={(e) => setCorporateInfo(prev => ({ ...prev, phone: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="+45 12 34 56 78"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="company-address" className="text-gold">Virksomhedsadresse *</Label>
                <Input
                  id="company-address"
                  value={corporateInfo.address}
                  onChange={(e) => setCorporateInfo(prev => ({ ...prev, address: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="Vejnavn og nummer"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="company-city" className="text-gold">By *</Label>
                  <Input
                    id="company-city"
                    value={corporateInfo.city}
                    onChange={(e) => setCorporateInfo(prev => ({ ...prev, city: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="København"
                  />
                </div>
                <div>
                  <Label htmlFor="company-postal" className="text-gold">Postnummer *</Label>
                  <Input
                    id="company-postal"
                    value={corporateInfo.postalCode}
                    onChange={(e) => setCorporateInfo(prev => ({ ...prev, postalCode: e.target.value }))}
                    className="bg-black/50 border-gold/30 text-white"
                    placeholder="1000"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="travel-fee" className="text-gold">Udkørsel/rejseomkostninger (DKK) *</Label>
                <Input
                  id="travel-fee"
                  type="number"
                  value={corporateInfo.travelFee}
                  onChange={(e) => setCorporateInfo(prev => ({ ...prev, travelFee: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="500"
                  min="0"
                />
                <p className="text-gray-400 text-sm mt-1">Ekstra omkostninger for at komme til virksomheden</p>
              </div>

              <div>
                <Label htmlFor="special-requirements" className="text-gold">Særlige krav (valgfrit)</Label>
                <Textarea
                  id="special-requirements"
                  value={corporateInfo.specialRequirements}
                  onChange={(e) => setCorporateInfo(prev => ({ ...prev, specialRequirements: e.target.value }))}
                  className="bg-black/50 border-gold/30 text-white"
                  placeholder="F.eks. parkeringsforhold, adgang til lokaler, tidskrav..."
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
                      {isHomeService && (
                        <div className="flex justify-between text-gold">
                          <span>🏠 Hjemmeservice</span>
                          <span>+{settings.home_service_fee || 150} DKK</span>
                        </div>
                      )}
                      <Separator className="my-2 bg-gold/20" />
                      <div className="flex justify-between font-bold text-gold">
                        <span>I alt ({getTotalDuration()} min):</span>
                        <span>{getTotalPrice()} DKK</span>
                      </div>
                    </div>
                    
                    {isHomeService && (
                      <div className="mt-4">
                        <Label className="text-gold">Service adresse:</Label>
                        <div className="text-white">
                          <p>{homeServiceInfo.address}</p>
                          <p>{homeServiceInfo.postalCode} {homeServiceInfo.city}</p>
                          {homeServiceInfo.specialInstructions && (
                            <p className="text-gray-300 text-sm mt-1">
                              Bemærkninger: {homeServiceInfo.specialInstructions}
                            </p>
                          )}
                        </div>
                      </div>
                    )}
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
                onClick={bookingType === 'corporate' ? handleCorporateBooking : handleBooking}
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