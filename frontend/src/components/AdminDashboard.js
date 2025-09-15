import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Calendar, Users, Settings, LogOut, User, Scissors, Clock, Mail, Phone } from 'lucide-react';
import axios from 'axios';
import { format } from 'date-fns';
import { da } from 'date-fns/locale';

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
        setError('Du har ikke admin rettigheder');
      }
    } catch (error) {
      setError('Login mislykkedes. Tjek dine oplysninger.');
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
              {loading ? 'Logger ind...' : 'Log ind'}
            </Button>
          </form>
          
          <div className="mt-4 p-3 bg-gold/10 rounded border border-gold/20">
            <p className="text-xs text-gray-300">
              <strong>Demo Admin:</strong><br/>
              Email: admin6@frisorlafata.dk<br/>
              Password: admin123
            </p>
          </div>
        </CardContent>
      </Card>
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
      setError('Kunne ikke hente data');
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

  const getStaffName = (staffId) => {
    const staffMember = staff.find(s => s.id === staffId);
    return staffMember ? staffMember.name : 'Ukendt';
  };

  const getServiceNames = (serviceIds) => {
    return serviceIds.map(id => {
      const service = services.find(s => s.id === id);
      return service ? service.name : 'Ukendt service';
    }).join(', ');
  };

  const formatDate = (dateStr) => {
    try {
      return format(new Date(dateStr), 'dd/MM/yyyy', { locale: da });
    } catch {
      return dateStr;
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'confirmed': { color: 'bg-green-500', text: 'Bekræftet' },
      'cancelled': { color: 'bg-red-500', text: 'Aflyst' },
      'completed': { color: 'bg-blue-500', text: 'Gennemført' }
    };
    const config = statusConfig[status] || { color: 'bg-gray-500', text: status };
    return (
      <Badge className={`${config.color} text-white`}>
        {config.text}
      </Badge>
    );
  };

  const getPaymentStatusBadge = (status) => {
    const statusConfig = {
      'paid': { color: 'bg-green-500', text: 'Betalt' },
      'pending': { color: 'bg-yellow-500', text: 'Afventer' },
      'cancelled': { color: 'bg-red-500', text: 'Aflyst' }
    };
    const config = statusConfig[status] || { color: 'bg-gray-500', text: status };
    return (
      <Badge className={`${config.color} text-white`}>
        {config.text}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-gold">Indlæser admin dashboard...</div>
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
                Log ud
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
              Bookinger
            </TabsTrigger>
            <TabsTrigger value="staff" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Users className="h-4 w-4 mr-2" />
              Personale
            </TabsTrigger>
            <TabsTrigger value="services" className="data-[state=active]:bg-gold data-[state=active]:text-black">
              <Scissors className="h-4 w-4 mr-2" />
              Tjenester
            </TabsTrigger>
          </TabsList>

          {/* Bookings Tab */}
          <TabsContent value="bookings" className="space-y-6">
            <Card className="bg-gray-900/50 border-gold/20">
              <CardHeader>
                <CardTitle className="text-gold">Alle Bookinger</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="border-gold/20">
                        <TableHead className="text-gold">Dato</TableHead>
                        <TableHead className="text-gold">Tid</TableHead>
                        <TableHead className="text-gold">Kunde</TableHead>
                        <TableHead className="text-gold">Frisør</TableHead>
                        <TableHead className="text-gold">Tjenester</TableHead>
                        <TableHead className="text-gold">Pris</TableHead>
                        <TableHead className="text-gold">Betaling</TableHead>
                        <TableHead className="text-gold">Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bookings.map((booking) => (
                        <TableRow key={booking.id} className="border-gold/10">
                          <TableCell className="text-white">
                            {formatDate(booking.booking_date)}
                          </TableCell>
                          <TableCell className="text-white">
                            {booking.booking_time.substring(0, 5)}
                          </TableCell>
                          <TableCell className="text-white">
                            <div className="space-y-1">
                              <div>Kunde ID: {booking.customer_id.substring(0, 8)}...</div>
                            </div>
                          </TableCell>
                          <TableCell className="text-white">
                            {getStaffName(booking.staff_id)}
                          </TableCell>
                          <TableCell className="text-white">
                            <div className="max-w-xs">
                              {getServiceNames(booking.services)}
                            </div>
                          </TableCell>
                          <TableCell className="text-white">
                            {booking.total_price} DKK
                          </TableCell>
                          <TableCell>
                            {getPaymentStatusBadge(booking.payment_status)}
                          </TableCell>
                          <TableCell>
                            {getStatusBadge(booking.status)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                
                {bookings.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    Ingen bookinger fundet
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Staff Tab */}
          <TabsContent value="staff" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {staff.map((member) => (
                <Card key={member.id} className="bg-gray-900/50 border-gold/20">
                  <CardHeader>
                    <CardTitle className="text-gold flex items-center">
                      <Users className="h-5 w-5 mr-2" />
                      {member.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-gray-300">
                      <strong>Specialitet:</strong> {member.specialty}
                    </div>
                    <div className="text-gray-300">
                      <strong>Erfaring:</strong> {member.experience}
                    </div>
                    <Badge variant="outline" className="border-gold/50 text-gold">
                      Aktiv
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Services Tab */}
          <TabsContent value="services" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {services.map((service) => (
                <Card key={service.id} className="bg-gray-900/50 border-gold/20">
                  <CardHeader>
                    <CardTitle className="text-gold flex items-center">
                      <Scissors className="h-5 w-5 mr-2" />
                      {service.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center text-gray-300">
                      <Clock className="h-4 w-4 mr-2" />
                      {service.duration_minutes} minutter
                    </div>
                    <div className="text-2xl font-bold text-gold">
                      {service.price} DKK
                    </div>
                    {service.description && (
                      <p className="text-gray-300 text-sm">{service.description}</p>
                    )}
                    <Badge variant="outline" className="border-gold/50 text-gold">
                      {service.category}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
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