import React, { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Separator } from "./components/ui/separator";
import { Clock, MapPin, Phone, Mail, Scissors, Users, Star, Instagram, Facebook, Youtube, Linkedin, Globe, Menu, X } from "lucide-react";
import { 
  GiRazor,
  GiComb,
  GiMustache,
  GiBeard,
  GiHairStrands,
  GiScissors,
  GiSpray,
  GiHotSurface
} from 'react-icons/gi';
import { 
  FaCut,
  FaSprayCan,
  FaPaintBrush,
  FaUserTie,
  FaMale,
  FaChild
} from 'react-icons/fa';
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
  const [galleryItems, setGalleryItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log(response.data.message);
    } catch (e) {
      console.error(e, `errored out requesting / api`);
    }
  };

  const fetchData = async () => {
    console.log('fetchData started, loading state should be true');
    
    try {
      // Set fallback data immediately to get the site working
      setServices([
        { name: "Klipning", duration_minutes: 30, price: 350, category: "haircut", icon: "✂️" },
        { name: "Skæg trimning", duration_minutes: 20, price: 200, category: "beard", icon: "🪒" },
        { name: "Vask & styling", duration_minutes: 45, price: 400, category: "styling", icon: "💧" },
        { name: "Farvning", duration_minutes: 60, price: 600, category: "coloring", icon: "🎨" }
      ]);
      
      setStaff([
        { 
          id: "1",
          name: "Kristofer Bruno la Fata", 
          bio: "Specialist i klassisk barbering med passion for detaljer",
          experience_years: 8,
          specialties: ["Classic cuts", "Beard styling", "Hot towel shaves"],
          instagram_url: "https://instagram.com/kristofer_barber",
          facebook_url: "https://facebook.com/kristofer.barber",
          linkedin_url: "",
          youtube_url: "",
          tiktok_url: "",
          twitter_url: "",
          website_url: "",
          avatar_url: ""
        },
        { 
          id: "2",
          name: "Marcus Nielsen", 
          bio: "Modern styling ekspert med 12 års erfaring",
          experience_years: 12,
          specialties: ["Modern cuts", "Hair coloring", "Styling"],
          instagram_url: "https://instagram.com/marcus_hair",
          facebook_url: "",
          linkedin_url: "https://linkedin.com/in/marcus-nielsen",
          youtube_url: "https://youtube.com/@marcushair",
          tiktok_url: "",
          twitter_url: "",
          website_url: "",
          avatar_url: ""
        }
      ]);
      
      setSettings({
        site_title: "Frisor LaFata",
        hero_title: "Klassisk Barbering",
        hero_subtitle: "i Hjertet af Byen",
        hero_description: "Oplev den autentiske barber-oplevelse hos Frisor LaFata. Vi kombinerer traditionel håndværk med moderne teknikker.",
        hero_image: "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHxiYXJiZXJzaG9wfGVufDB8fHx8MTczMjgzMjAzMnww&ixlib=rb-4.1.0&q=85",
        booking_system_enabled: true,
        social_media_enabled: true,
        contact_phone: "+45 12 34 56 78",
        contact_email: "info@frisorlafata.dk",
        address: "Hovedgaden 123, 1000 København"
      });
      
      setPages([
        { id: "1", title: "Om Os", slug: "om-os" },
        { id: "2", title: "Priser", slug: "priser" },
        { id: "3", title: "Historie", slug: "historie" }
      ]);
      
      setGalleryItems([]);
      
      console.log('Fallback data set successfully');
      
      // Try to fetch real data in background
      try {
        const response = await fetch(`${API}/staff`, { timeout: 3000 });
        if (response.ok) {
          const realStaffData = await response.json();
          if (realStaffData && realStaffData.length > 0) {
            setStaff(realStaffData);
            console.log('Real staff data loaded:', realStaffData.length, 'members');
          }
        }
      } catch (e) {
        console.log('Background staff fetch failed, using fallback data');
      }
      
    } catch (error) {
      console.error('Error in fetchData:', error);
    } finally {
      console.log('fetchData completed, setting loading to false');
      setLoading(false);
    }
  };

  // Function to fix image URLs that point to wrong domain
  const fixImageUrl = (url) => {
    if (!url) return '';
    // Replace wrong domain with correct domain
    return url.replace('stylista-admin.preview.emergentagent.com', 'barberedit.preview.emergentagent.com');
  };

  useEffect(() => {
    console.log('Starting fetchData - direct approach');
    
    // Set loading to false immediately and then load data in background
    setLoading(false);
    
    // Load data directly without complex error handling
    const fetchData = async () => {
      try {
        // Staff data
        const staffRes = await fetch(`${API}/staff`);
        if (staffRes.ok) {
          const staffData = await staffRes.json();
          // Fix avatar URLs
          const fixedStaffData = staffData.map(staff => ({
            ...staff,
            avatar_url: fixImageUrl(staff.avatar_url)
          }));
          setStaff(fixedStaffData);
        }
        
        // Settings data (includes hero image)
        const settingsRes = await fetch(`${API}/public/settings`);
        if (settingsRes.ok) {
          const settingsData = await settingsRes.json();
          // Fix hero image URL
          const fixedSettingsData = {
            ...settingsData,
            hero_image: fixImageUrl(settingsData.hero_image)
          };
          setSettings(fixedSettingsData);
        }
        
        // Gallery data
        const galleryRes = await fetch(`${API}/gallery?featured_only=false`);
        if (galleryRes.ok) {
          const galleryData = await galleryRes.json();
          setGalleryItems(galleryData);
        }
        
        // Services data
        const servicesRes = await fetch(`${API}/services`);
        if (servicesRes.ok) {
          const servicesData = await servicesRes.json();
          setServices(servicesData);
        }
        
        // Pages data
        const pagesRes = await fetch(`${API}/public/pages`);
        if (pagesRes.ok) {
          const pagesData = await pagesRes.json();
          setPages(pagesData);
        }
        
        console.log('All data loaded successfully');
        
      } catch (error) {
        console.error('Error loading data:', error);
      }
    };
    
    // Start loading data in background
    fetchData();
  }, []);

  const getServiceIcon = (iconValue) => {
    // First check emoji icons
    const emojiIcons = {
      "scissors-emoji": "✂️",
      "razor-emoji": "🪒",
      "haircut-man": "💇‍♂️",
      "haircut-woman": "💇‍♀️",
      "massage-man": "💆‍♂️",
      "massage-woman": "💆‍♀️",
      "beard-emoji": "🧔",
      "bald-man": "👨‍🦲",
      "makeup": "💄",
      "star-emoji": "🌟",
      "star-filled": "⭐",
      "sparkles-emoji": "✨",
      "diamond-emoji": "💎",
      "crown-emoji": "👑",
      "fire-emoji": "🔥",
      "lightning": "⚡",
      "water-drop": "💧",
      "art": "🎨",
      "hundred": "💯",
      "heart-emoji": "❤️"
    };

    if (emojiIcons[iconValue]) {
      return emojiIcons[iconValue];
    }

    // Component icons mapping
    const componentIcons = {
      "scissors": <Scissors className="h-8 w-8 text-gold" />,
      "razor": <GiRazor className="h-8 w-8 text-gold" />,
      "comb": <GiComb className="h-8 w-8 text-gold" />,
      "barber-scissors": <GiScissors className="h-8 w-8 text-gold" />,
      "cut": <FaCut className="h-8 w-8 text-gold" />,
      "hair-strands": <GiHairStrands className="h-8 w-8 text-gold" />,
      "spray": <GiSpray className="h-8 w-8 text-gold" />,
      "spray-can": <FaSprayCan className="h-8 w-8 text-gold" />,
      "paint-brush": <FaPaintBrush className="h-8 w-8 text-gold" />,
      "hot-surface": <GiHotSurface className="h-8 w-8 text-gold" />,
      "mustache": <GiMustache className="h-8 w-8 text-gold" />,
      "beard": <GiBeard className="h-8 w-8 text-gold" />,
      "user": <Users className="h-8 w-8 text-gold" />,
      "male": <FaMale className="h-8 w-8 text-gold" />,
      "child": <FaChild className="h-8 w-8 text-gold" />,
      "user-tie": <FaUserTie className="h-8 w-8 text-gold" />,
      "star": <Star className="h-8 w-8 text-gold" />,
      "clock": <Clock className="h-8 w-8 text-gold" />
    };

    if (componentIcons[iconValue]) {
      return componentIcons[iconValue];
    }

    // Legacy category mapping for backward compatibility
    const categoryIcons = {
      haircut: "✂️",
      beard: "🧔", 
      styling: "💧",
      coloring: "🎨",
      premium: "👑",
      general: "✨"
    };

    return categoryIcons[iconValue] || "✨";
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
            
            {/* Desktop Navigation */}
            <div className="hidden md:block">
              <div className="flex items-center space-x-6">
                {/* Main Navigation Links - Fixed positions */}
                <div className="flex items-center space-x-6">
                  <a href="#home" className="text-gold hover:text-gold/80 transition-colors px-3 py-2 whitespace-nowrap">Hjem</a>
                  <a href="#services" className="text-gold hover:text-gold/80 transition-colors px-3 py-2 whitespace-nowrap">Tjenester</a>
                  <a href="#staff" className="text-gold hover:text-gold/80 transition-colors px-3 py-2 whitespace-nowrap">Frisører</a>
                  <a href="#gallery" className="text-gold hover:text-gold/80 transition-colors px-3 py-2 whitespace-nowrap">Galleri</a>
                  
                  {/* Social Media Link - Fixed width container */}
                  <div className="w-24 flex justify-center">
                    {settings.social_media_enabled && (
                      <a href="#social" className="text-gold hover:text-gold/80 transition-colors px-3 py-2 whitespace-nowrap">Social</a>
                    )}
                  </div>
                  
                  {/* Dynamic Pages - Fixed width container for up to 3 pages */}
                  <div className="flex items-center space-x-4 w-48 justify-center">
                    {pages.slice(0, 3).map((page, index) => (
                      <Link 
                        key={page.id} 
                        to={`/page/${page.slug}`} 
                        className="text-gold hover:text-gold/80 transition-colors px-2 py-2 text-sm whitespace-nowrap"
                      >
                        {page.title}
                      </Link>
                    ))}
                  </div>
                  
                  <a href="#contact" className="text-gold hover:text-gold/80 transition-colors px-3 py-2 whitespace-nowrap">Kontakt</a>
                </div>
                
                {/* Booking Button - Fixed width container */}
                <div className="w-24 flex justify-center ml-4">
                  {settings.booking_system_enabled !== false && (
                    <Button 
                      className="bg-gold text-black hover:bg-gold/90 font-semibold whitespace-nowrap px-4 py-2"
                      onClick={() => setShowBooking(true)}
                    >
                      Book tid
                    </Button>
                  )}
                </div>
              </div>
            </div>
            
            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-gold hover:text-gold/80 transition-colors p-2"
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>
          
          {/* Mobile Navigation Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden bg-black/95 border-t border-gold/20">
              <div className="px-2 pt-2 pb-3 space-y-1">
                <a href="#home" className="block text-gold hover:text-gold/80 transition-colors px-3 py-2" onClick={() => setMobileMenuOpen(false)}>Hjem</a>
                <a href="#services" className="block text-gold hover:text-gold/80 transition-colors px-3 py-2" onClick={() => setMobileMenuOpen(false)}>Tjenester</a>
                <a href="#staff" className="block text-gold hover:text-gold/80 transition-colors px-3 py-2" onClick={() => setMobileMenuOpen(false)}>Frisører</a>
                <a href="#gallery" className="block text-gold hover:text-gold/80 transition-colors px-3 py-2" onClick={() => setMobileMenuOpen(false)}>Galleri</a>
                {settings.social_media_enabled && (
                  <a href="#social" className="block text-gold hover:text-gold/80 transition-colors px-3 py-2" onClick={() => setMobileMenuOpen(false)}>Social Media</a>
                )}
                {pages.slice(0, 3).map((page) => (
                  <Link 
                    key={page.id} 
                    to={`/page/${page.slug}`} 
                    className="block text-gold hover:text-gold/80 transition-colors px-3 py-2"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {page.title}
                  </Link>
                ))}
                <a href="#contact" className="block text-gold hover:text-gold/80 transition-colors px-3 py-2" onClick={() => setMobileMenuOpen(false)}>Kontakt</a>
                {settings.booking_system_enabled !== false && (
                  <div className="px-3 py-2">
                    <Button 
                      className="bg-gold text-black hover:bg-gold/90 font-semibold w-full"
                      onClick={() => {
                        setShowBooking(true);
                        setMobileMenuOpen(false);
                      }}
                    >
                      Book tid
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section id="home" className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img 
            src={settings.hero_image || "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHxiYXJiZXJzaG9wfGVufDB8fHx8MTczMjgzMjAzMnww&ixlib=rb-4.1.0&q=85"}
            alt="Frisor LaFata barbershop"
            className="w-full h-full object-cover opacity-30"
            onLoad={() => console.log('Hero image loaded:', settings.hero_image || 'fallback')}
            onError={(e) => {
              console.error('Hero image failed to load:', e.target.src);
              e.target.src = "https://images.unsplash.com/photo-1585747860715-2ba37e788b70?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHxiYXJiZXJzaG9wfGVufDB8fHx8MTczMjgzMjAzMnww&ixlib=rb-4.1.0&q=85";
            }}
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
          
          {settings.booking_system_enabled !== false && (
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
          )}
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
                  <div className="text-4xl mb-4">{getServiceIcon(service.icon || service.category)}</div>
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
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {staff.map((member, index) => (
              <Card key={member.id || index} className="bg-black/70 border-gold/20 hover:border-gold/50 transition-all duration-300 hover:scale-105">
                <CardContent className="p-8 text-center">
                  <div className="mb-6">
                    {member.avatar_url ? (
                      <img 
                        src={member.avatar_url} 
                        alt={member.name}
                        className="w-24 h-24 rounded-full object-cover mx-auto mb-4 border-4 border-gold/30 shadow-lg"
                      />
                    ) : (
                      <div className="w-24 h-24 rounded-full bg-gold/20 border-4 border-gold/30 flex items-center justify-center mx-auto mb-4">
                        <Users className="h-12 w-12 text-gold" />
                      </div>
                    )}
                  </div>
                  
                  <h3 className="text-2xl font-semibold text-gold mb-3 font-serif">{member.name}</h3>
                  
                  {member.bio && (
                    <p className="text-gray-300 text-sm mb-3 italic">{member.bio}</p>
                  )}
                  
                  {member.specialties && member.specialties.length > 0 && (
                    <div className="mb-3">
                      <div className="flex flex-wrap justify-center gap-1">
                        {member.specialties.slice(0, 3).map((specialty, idx) => (
                          <Badge key={idx} variant="outline" className="border-gold/50 text-gold text-xs">
                            {specialty}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-center text-gold mb-4">
                    <Star className="h-4 w-4 mr-1" />
                    <span className="text-sm">{member.experience_years} års erfaring</span>
                  </div>

                  {/* Social Media Icons */}
                  <div className="flex items-center justify-center space-x-3 pt-4 border-t border-gold/20">
                    {member.instagram_url && (
                      <button
                        onClick={() => window.open(member.instagram_url, '_blank')}
                        className="p-2 rounded-full bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white hover:scale-110 transition-transform duration-200"
                        title="Instagram"
                      >
                        <Instagram className="h-4 w-4" />
                      </button>
                    )}
                    {member.facebook_url && (
                      <button
                        onClick={() => window.open(member.facebook_url, '_blank')}
                        className="p-2 rounded-full bg-blue-600 text-white hover:scale-110 transition-transform duration-200"
                        title="Facebook"
                      >
                        <Facebook className="h-4 w-4" />
                      </button>
                    )}
                    {member.linkedin_url && (
                      <button
                        onClick={() => window.open(member.linkedin_url, '_blank')}
                        className="p-2 rounded-full bg-blue-700 text-white hover:scale-110 transition-transform duration-200"
                        title="LinkedIn"
                      >
                        <Linkedin className="h-4 w-4" />
                      </button>
                    )}
                    {member.youtube_url && (
                      <button
                        onClick={() => window.open(member.youtube_url, '_blank')}
                        className="p-2 rounded-full bg-red-600 text-white hover:scale-110 transition-transform duration-200"
                        title="YouTube"
                      >
                        <Youtube className="h-4 w-4" />
                      </button>
                    )}
                    {member.tiktok_url && (
                      <button
                        onClick={() => window.open(member.tiktok_url, '_blank')}
                        className="p-2 rounded-full bg-black text-white hover:scale-110 transition-transform duration-200"
                        title="TikTok"
                      >
                        <span className="text-xs font-bold">TT</span>
                      </button>
                    )}
                    {member.twitter_url && (
                      <button
                        onClick={() => window.open(member.twitter_url, '_blank')}
                        className="p-2 rounded-full bg-black text-white hover:scale-110 transition-transform duration-200"
                        title="X (Twitter)"
                      >
                        <span className="text-xs font-bold">𝕏</span>
                      </button>
                    )}
                    {member.website_url && (
                      <button
                        onClick={() => window.open(member.website_url, '_blank')}
                        className="p-2 rounded-full bg-gold text-black hover:scale-110 transition-transform duration-200"
                        title="Website"
                      >
                        <Globe className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Gallery Section */}
      <section id="gallery" className="py-20 bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gold mb-4 font-serif">Vores Arbejde</h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Se før og efter fotos af vores fantastiske transformationer
            </p>
          </div>
          
          {galleryItems.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Show featured items first, then regular items if needed */}
              {(galleryItems.filter(item => item.is_featured).length > 0 
                ? galleryItems.filter(item => item.is_featured) 
                : galleryItems
              ).slice(0, 6).map((item) => (
                <Card key={item.id} className="bg-black/50 border-gold/20 hover:border-gold/50 transition-all duration-300 overflow-hidden">
                  <CardContent className="p-0">
                    <div className="grid grid-cols-2 h-48">
                      <div className="relative">
                        <img 
                          src={item.before_image} 
                          alt="Before"
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute top-2 left-2">
                          <Badge className="bg-red-500 text-white text-xs">Før</Badge>
                        </div>
                      </div>
                      <div className="relative">
                        <img 
                          src={item.after_image} 
                          alt="After"
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute top-2 right-2">
                          <Badge className="bg-green-500 text-white text-xs">Efter</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="text-lg font-semibold text-gold mb-2">{item.title}</h3>
                      {item.description && (
                        <p className="text-gray-300 text-sm mb-2">{item.description}</p>
                      )}
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        {item.service_type && (
                          <Badge variant="outline" className="border-gold/50 text-gold">
                            {item.service_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </Badge>
                        )}
                        {item.is_featured && (
                          <Badge className="bg-yellow-500 text-black flex items-center gap-1">
                            <Star className="h-3 w-3" />
                            Featured
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📸</div>
              <h3 className="text-xl font-semibold text-gray-300 mb-2">Galleri kommer snart</h3>
              <p className="text-gray-400">Vi arbejder på at uploade vores seneste arbejde</p>
            </div>
          )}
          
          {galleryItems.length > 6 && (
            <div className="text-center mt-12">
              <Button variant="outline" className="border-gold text-gold hover:bg-gold hover:text-black">
                Se mere galleri
              </Button>
            </div>
          )}
        </div>
      </section>

      {/* Social Media Section */}
      {settings.social_media_enabled && (
        <section id="social" className="py-20 bg-black/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold text-gold mb-4 font-serif">
                {settings.social_media_title || 'Follow Us'}
              </h2>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                {settings.social_media_description || 'Se vores seneste arbejde og tilbud på sociale medier'}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Instagram */}
              {settings.instagram_enabled && (settings.instagram_username || settings.instagram_embed_code) && (
                <Card className="bg-gray-900/50 border-gold/20 hover:border-gold/50 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center mb-4">
                      <div className="w-8 h-8 bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 rounded-lg flex items-center justify-center mr-3">
                        <span className="text-white font-bold text-sm">IG</span>
                      </div>
                      <h3 className="text-xl font-semibold text-gold">Instagram</h3>
                    </div>
                    
                    {settings.instagram_embed_code ? (
                      <div 
                        className="instagram-embed-container"
                        dangerouslySetInnerHTML={{ __html: settings.instagram_embed_code }}
                      />
                    ) : settings.instagram_username && (
                      <div className="text-center">
                        <p className="text-gray-300 mb-4">Follow us on Instagram</p>
                        <Button
                          variant="outline"
                          className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                          onClick={() => window.open(`https://instagram.com/${settings.instagram_username.replace('@', '')}`, '_blank')}
                        >
                          {settings.instagram_username}
                        </Button>
                        {settings.instagram_hashtag && (
                          <p className="text-gray-400 text-sm mt-2">{settings.instagram_hashtag}</p>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Facebook */}
              {settings.facebook_enabled && (settings.facebook_page_url || settings.facebook_embed_code) && (
                <Card className="bg-gray-900/50 border-gold/20 hover:border-gold/50 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center mb-4">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                        <span className="text-white font-bold text-sm">f</span>
                      </div>
                      <h3 className="text-xl font-semibold text-gold">Facebook</h3>
                    </div>
                    
                    {settings.facebook_embed_code ? (
                      <div 
                        className="facebook-embed-container"
                        dangerouslySetInnerHTML={{ __html: settings.facebook_embed_code }}
                      />
                    ) : settings.facebook_page_url && (
                      <div className="text-center">
                        <p className="text-gray-300 mb-4">Like our Facebook page</p>
                        <Button
                          variant="outline"
                          className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                          onClick={() => window.open(settings.facebook_page_url, '_blank')}
                        >
                          Visit Page
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* TikTok */}
              {settings.tiktok_enabled && (settings.tiktok_username || settings.tiktok_embed_code) && (
                <Card className="bg-gray-900/50 border-gold/20 hover:border-gold/50 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center mb-4">
                      <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center mr-3 border border-white">
                        <span className="text-white font-bold text-sm">T</span>
                      </div>
                      <h3 className="text-xl font-semibold text-gold">TikTok</h3>
                    </div>
                    
                    {settings.tiktok_embed_code ? (
                      <div 
                        className="tiktok-embed-container"
                        dangerouslySetInnerHTML={{ __html: settings.tiktok_embed_code }}
                      />
                    ) : settings.tiktok_username && (
                      <div className="text-center">
                        <p className="text-gray-300 mb-4">Follow us on TikTok</p>
                        <Button
                          variant="outline"
                          className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                          onClick={() => window.open(`https://tiktok.com/${settings.tiktok_username.replace('@', '')}`, '_blank')}
                        >
                          {settings.tiktok_username}
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Twitter/X */}
              {settings.twitter_enabled && (settings.twitter_username || settings.twitter_embed_code) && (
                <Card className="bg-gray-900/50 border-gold/20 hover:border-gold/50 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center mb-4">
                      <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center mr-3 border border-white">
                        <span className="text-white font-bold text-sm">X</span>
                      </div>
                      <h3 className="text-xl font-semibold text-gold">Twitter / X</h3>
                    </div>
                    
                    {settings.twitter_embed_code ? (
                      <div 
                        className="twitter-embed-container"
                        dangerouslySetInnerHTML={{ __html: settings.twitter_embed_code }}
                      />
                    ) : settings.twitter_username && (
                      <div className="text-center">
                        <p className="text-gray-300 mb-4">Follow us on X</p>
                        <Button
                          variant="outline"
                          className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                          onClick={() => window.open(`https://x.com/${settings.twitter_username.replace('@', '')}`, '_blank')}
                        >
                          {settings.twitter_username}
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* YouTube */}
              {settings.youtube_enabled && (settings.youtube_channel_url || settings.youtube_embed_code) && (
                <Card className="bg-gray-900/50 border-gold/20 hover:border-gold/50 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center mb-4">
                      <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center mr-3">
                        <span className="text-white font-bold text-sm">▶</span>
                      </div>
                      <h3 className="text-xl font-semibold text-gold">YouTube</h3>
                    </div>
                    
                    {settings.youtube_embed_code ? (
                      <div 
                        className="youtube-embed-container"
                        dangerouslySetInnerHTML={{ __html: settings.youtube_embed_code }}
                      />
                    ) : settings.youtube_channel_url && (
                      <div className="text-center">
                        <p className="text-gray-300 mb-4">Subscribe to our channel</p>
                        <Button
                          variant="outline"
                          className="border-gold/50 text-gold hover:bg-gold hover:text-black"
                          onClick={() => window.open(settings.youtube_channel_url, '_blank')}
                        >
                          Visit Channel
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Social Media CTA */}
            <div className="text-center mt-12">
              <p className="text-gray-300 mb-4">Stay connected with us on social media for the latest updates and exclusive offers!</p>
            </div>
          </div>
        </section>
      )}

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
              {settings.booking_system_enabled !== false ? (
                <>
                  <h3 className="text-2xl font-semibold text-gold mb-6">Book din tid</h3>
                  <Button 
                    size="lg" 
                    className="w-full bg-gold text-black hover:bg-gold/90 text-lg py-3 font-semibold"
                    onClick={() => setShowBooking(true)}
                  >
                    Gå til booking system
                  </Button>
                  <Separator className="my-6 bg-gold/20" />
                </>
              ) : (
                <>
                  <h3 className="text-2xl font-semibold text-gold mb-6">Kontakt os</h3>
                  <p className="text-gray-300 mb-6">
                    Online booking er midlertidigt ikke tilgængelig. Kontakt os direkte for at booke din tid.
                  </p>
                  <Separator className="my-6 bg-gold/20" />
                </>
              )}
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