import React, { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Separator } from "./components/ui/separator";
import { Clock, MapPin, Phone, Mail, Scissors, Users, Star } from "lucide-react";
import BookingSystem from "./components/BookingSystem";
import AdminApp from "./components/AdminDashboard";
import PublicPage from "./components/PublicPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [showBooking, setShowBooking] = useState(false);
  const [services, setServices] = useState([]);
  const [staff, setStaff] = useState([]);
  const [settings, setSettings] = useState({});
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);

  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log(response.data.message);
    } catch (e) {
      console.error(e, `errored out requesting / api`);
    }
  };

  const fetchData = async () => {
    try {
      const [servicesRes, staffRes, settingsRes, pagesRes] = await Promise.all([
        axios.get(`${API}/services`),
        axios.get(`${API}/staff`),
        axios.get(`${API}/public/settings`),
        axios.get(`${API}/public/pages`)
      ]);
      
      setServices(servicesRes.data);
      setStaff(staffRes.data);
      setSettings(settingsRes.data);
      setPages(pagesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      // Fallback to default data if API fails
      setServices([
        { name: "Klipning", duration_minutes: 30, price: 350, category: "haircut", icon: "✂️" },
        { name: "Skæg trimning", duration_minutes: 20, price: 200, category: "beard", icon: "🪒" },
        { name: "Vask & styling", duration_minutes: 45, price: 400, category: "styling", icon: "💧" },
        { name: "Farvning", duration_minutes: 60, price: 600, category: "coloring", icon: "🎨" },
        { name: "Børneklip", duration_minutes: 25, price: 250, category: "haircut", icon: "👶" },
        { name: "Komplet styling", duration_minutes: 90, price: 750, category: "premium", icon: "⭐" }
      ]);
      setStaff([
        { name: "Lars Andersen", specialty: "Klassisk klipning", experience: "15 år" },
        { name: "Mikael Jensen", specialty: "Modern styling", experience: "12 år" },
        { name: "Sofia Nielsen", specialty: "Farvning", experience: "8 år" }
      ]);
      setSettings({
        site_title: "Frisor LaFata",
        site_description: "Klassisk barbering siden 2010",
        contact_phone: "+45 12 34 56 78",
        contact_email: "info@frisorlafata.dk",
        address: "Hovedgaden 123, 1000 København",
        hero_title: "Klassisk Barbering",
        hero_subtitle: "i Hjertet af Byen",
        hero_description: "Oplev den autentiske barber-oplevelse hos Frisor LaFata. Vi kombinerer traditionel håndværk med moderne teknikker.",
        hero_image: "https://images.unsplash.com/photo-1573586927918-3e6476da8395?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwzfHxyZXRybyUyMGJhcmJlcnxlbnwwfHx8fDE3NTc5NzcyODB8MA&ixlib=rb-4.1.0&q=85"
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    helloWorldApi();
    fetchData();
  }, []);

  const getServiceIcon = (category) => {
    const icons = {
      haircut: "✂️",
      beard: "🪒",
      styling: "💧",
      coloring: "🎨",
      premium: "⭐",
      general: "✨"
    };
    return icons[category] || "✨";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-gold">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-gold">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-black/90 backdrop-blur-md z-50 border-b border-gold/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Scissors className="h-8 w-8 text-gold mr-3" />
              <h1 className="text-2xl font-bold text-gold font-serif">{settings.site_title}</h1>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-8">
                <a href="#home" className="text-gold hover:text-gold/80 transition-colors px-3 py-2">Hjem</a>
                <a href="#services" className="text-gold hover:text-gold/80 transition-colors px-3 py-2">Tjenester</a>
                <a href="#staff" className="text-gold hover:text-gold/80 transition-colors px-3 py-2">Frisører</a>
                {pages.slice(0, 3).map((page) => (
                  <Link 
                    key={page.id} 
                    to={`/page/${page.slug}`} 
                    className="text-gold hover:text-gold/80 transition-colors px-3 py-2"
                  >
                    {page.title}
                  </Link>
                ))}
                <a href="#contact" className="text-gold hover:text-gold/80 transition-colors px-3 py-2">Kontakt</a>
                <Button 
                  className="bg-gold text-black hover:bg-gold/90 font-semibold"
                  onClick={() => setShowBooking(true)}
                >
                  Book tid
                </Button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="home" className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img 
            src={settings.hero_image || "https://images.unsplash.com/photo-1573586927918-3e6476da8395?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwzfHxyZXRybyUyMGJhcmJlcnxlbnwwfHx8fDE3NTc5NzcyODB8MA&ixlib=rb-4.1.0&q=85"}
            alt="Frisor LaFata barbershop"
            className="w-full h-full object-cover opacity-30"
          />
          <div className="absolute inset-0 bg-black/70"></div>
        </div>
        
        <div className="relative z-10 text-center max-w-4xl mx-auto px-4">
          <div className="mb-8">
            <Badge variant="outline" className="border-gold text-gold mb-4 text-sm">
              Siden 2010
            </Badge>
            <h2 className="text-5xl md:text-7xl font-bold text-gold mb-6 font-serif leading-tight">
              {settings.hero_title}
              <span className="block text-4xl md:text-5xl text-gold/80 mt-2">{settings.hero_subtitle}</span>
            </h2>
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-2xl mx-auto">
              {settings.hero_description}
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button 
              size="lg" 
              className="bg-gold text-black hover:bg-gold/90 text-lg px-8 py-3 font-semibold"
              onClick={() => setShowBooking(true)}
            >
              Book din tid nu
            </Button>
            <Button variant="outline" size="lg" className="border-gold text-gold hover:bg-gold hover:text-black text-lg px-8 py-3">
              Se vores tjenester
            </Button>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section id="services" className="py-20 bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gold mb-4 font-serif">Vores Tjenester</h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Fra klassisk klipning til moderne styling - vi tilbyder det hele
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((service, index) => (
              <Card key={service.id || index} className="bg-black/50 border-gold/20 hover:border-gold/50 transition-all duration-300 hover:transform hover:scale-105">
                <CardContent className="p-6 text-center">
                  <div className="text-4xl mb-4">{getServiceIcon(service.category)}</div>
                  <h3 className="text-xl font-semibold text-gold mb-2">{service.name}</h3>
                  <div className="flex items-center justify-center text-gray-300 mb-3">
                    <Clock className="h-4 w-4 mr-1" />
                    <span className="text-sm">{service.duration_minutes} min</span>
                  </div>
                  <div className="text-2xl font-bold text-gold">{service.price} DKK</div>
                  {service.description && (
                    <p className="text-gray-300 text-sm mt-2">{service.description}</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Staff Section */}
      <section id="staff" className="py-20 relative">
        <div className="absolute inset-0 z-0">
          <img 
            src="https://images.unsplash.com/photo-1734723836256-0e168f4721a7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHw0fHxyZXRybyUyMGJhcmJlcnxlbnwwfHx8fDE3NTc5NzcyODB8MA&ixlib=rb-4.1.0&q=85"
            alt="Barbershop interior"
            className="w-full h-full object-cover opacity-20"
          />
          <div className="absolute inset-0 bg-black/80"></div>
        </div>
        
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gold mb-4 font-serif">Mød Vores Frisører</h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Erfarne professionelle der elsker hvad de laver
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {staff.map((member, index) => (
              <Card key={member.id || index} className="bg-black/70 border-gold/20 hover:border-gold/50 transition-all duration-300">
                <CardContent className="p-6 text-center">
                  <div className="mb-4">
                    {member.avatar_url ? (
                      <img 
                        src={member.avatar_url} 
                        alt={member.name}
                        className="w-16 h-16 rounded-full object-cover mx-auto mb-4 border-2 border-gold/30"
                      />
                    ) : (
                      <Users className="h-16 w-16 text-gold mx-auto mb-4" />
                    )}
                  </div>
                  <h3 className="text-xl font-semibold text-gold mb-2">{member.name}</h3>
                  <p className="text-gray-300 mb-2">{member.specialty}</p>
                  <div className="flex items-center justify-center text-gold">
                    <Star className="h-4 w-4 mr-1" />
                    <span className="text-sm">{member.experience} erfaring</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-20 bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gold mb-4 font-serif">Kontakt Os</h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Book din tid eller kontakt os for mere information
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div className="space-y-8">
              <div className="flex items-center space-x-4">
                <div className="bg-gold/10 p-3 rounded-full">
                  <MapPin className="h-6 w-6 text-gold" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gold">Address</h3>
                  <p className="text-gray-300">{settings.address}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="bg-gold/10 p-3 rounded-full">
                  <Phone className="h-6 w-6 text-gold" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gold">Telefon</h3>
                  <p className="text-gray-300">{settings.contact_phone}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="bg-gold/10 p-3 rounded-full">
                  <Mail className="h-6 w-6 text-gold" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gold">Email</h3>
                  <p className="text-gray-300">{settings.contact_email}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="bg-gold/10 p-3 rounded-full">
                  <Clock className="h-6 w-6 text-gold" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gold">Åbningstider</h3>
                  <div className="text-gray-300 space-y-1">
                    <p>Man-Fre: 09:00 - 18:00</p>
                    <p>Lørdag: 09:00 - 16:00</p>
                    <p>Søndag: Lukket</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-black/50 border border-gold/20 rounded-lg p-8">
              <h3 className="text-2xl font-semibold text-gold mb-6">Book din tid</h3>
              <Button 
                size="lg" 
                className="w-full bg-gold text-black hover:bg-gold/90 text-lg py-3 font-semibold"
                onClick={() => setShowBooking(true)}
              >
                Gå til booking system
              </Button>
              <Separator className="my-6 bg-gold/20" />
              <p className="text-center text-gray-300">
                Eller ring til os på <span className="text-gold font-semibold">{settings.contact_phone}</span>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black border-t border-gold/20 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <Scissors className="h-8 w-8 text-gold mr-3" />
              <h2 className="text-2xl font-bold text-gold font-serif">{settings.site_title}</h2>
            </div>
            <p className="text-gray-300 mb-4">{settings.site_description}</p>
            <p className="text-gray-400 text-sm mb-2">
              © 2024 Frisor LaFata. Alle rettigheder forbeholdes.
            </p>
            <a 
              href="/admin" 
              className="text-xs text-gray-500 hover:text-gold transition-colors"
            >
              Admin Login
            </a>
          </div>
        </div>
      </footer>

      {showBooking && (
        <BookingSystem onClose={() => setShowBooking(false)} />
      )}
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/admin" element={<AdminApp />} />
          <Route path="/page/:slug" element={<PublicPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;