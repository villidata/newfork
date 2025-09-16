import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Scissors, ArrowLeft, Calendar, Tag, User, Clock } from 'lucide-react';
import { format } from 'date-fns';
import BookingSystem from './BookingSystem';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PublicPage = () => {
  const { slug } = useParams();
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [settings, setSettings] = useState({});
  const [pages, setPages] = useState([]);
  const [showBooking, setShowBooking] = useState(false);

  useEffect(() => {
    fetchPage();
    fetchSettings();
    fetchPages();
  }, [slug]);

  const fetchPage = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/pages/${slug}`);
      setPage(response.data);
    } catch (error) {
      console.error('Error fetching page:', error);
      setError('Page not found');
    } finally {
      setLoading(false);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/public/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const fetchPages = async () => {
    try {
      const response = await axios.get(`${API}/public/pages`);
      setPages(response.data);
    } catch (error) {
      console.error('Error fetching pages:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-gold">Loading...</div>
      </div>
    );
  }

  if (error || !page) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gold mb-4">Page Not Found</h1>
          <p className="text-gray-300 mb-8">The page you're looking for doesn't exist.</p>
          <Link to="/">
            <Button className="bg-gold text-black hover:bg-gold/90">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-gold">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-black/90 backdrop-blur-md z-50 border-b border-gold/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center">
              <Scissors className="h-8 w-8 text-gold mr-3" />
              <h1 className="text-2xl font-bold text-gold font-serif">{settings.site_title || 'Frisor LaFata'}</h1>
            </Link>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-8">
                <Link to="/" className="text-gold hover:text-gold/80 transition-colors px-3 py-2">Hjem</Link>
                <a href="/#services" className="text-gold hover:text-gold/80 transition-colors px-3 py-2">Tjenester</a>
                <a href="/#staff" className="text-gold hover:text-gold/80 transition-colors px-3 py-2">Frisører</a>
                {pages.slice(0, 3).map((page) => (
                  <Link 
                    key={page.id} 
                    to={`/page/${page.slug}`} 
                    className="text-gold hover:text-gold/80 transition-colors px-3 py-2"
                  >
                    {page.title}
                  </Link>
                ))}
                <a href="/#contact" className="text-gold hover:text-gold/80 transition-colors px-3 py-2">Kontakt</a>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <div className="pt-16">
        {/* Featured Image Hero */}
        {page.featured_image && (
          <div className="relative h-96 overflow-hidden">
            <img 
              src={page.featured_image} 
              alt={page.title}
              className="w-full h-full object-cover opacity-40"
            />
            <div className="absolute inset-0 bg-black/70"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <Badge variant="outline" className="border-gold text-gold mb-4">
                  {page.page_type === 'blog' ? 'Blog Post' : 'Page'}
                </Badge>
                <h1 className="text-5xl md:text-6xl font-bold text-gold mb-4 font-serif">
                  {page.title}
                </h1>
                {page.excerpt && (
                  <p className="text-xl text-gray-300 max-w-2xl">
                    {page.excerpt}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Page Header (if no featured image) */}
          {!page.featured_image && (
            <div className="text-center mb-12">
              <Badge variant="outline" className="border-gold text-gold mb-4">
                {page.page_type === 'blog' ? 'Blog Post' : 'Page'}
              </Badge>
              <h1 className="text-5xl md:text-6xl font-bold text-gold mb-6 font-serif">
                {page.title}
              </h1>
              {page.excerpt && (
                <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
                  {page.excerpt}
                </p>
              )}
            </div>
          )}

          {/* Page Meta */}
          <div className="flex flex-wrap items-center justify-center gap-6 mb-12 text-gray-400">
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-2" />
              <span>{format(new Date(page.created_at), 'dd MMMM yyyy')}</span>
            </div>
            {page.categories && page.categories.length > 0 && (
              <div className="flex items-center">
                <Tag className="h-4 w-4 mr-2" />
                <div className="flex gap-2">
                  {page.categories.map((category, index) => (
                    <Badge key={index} variant="outline" className="border-gold/50 text-gold">
                      {category}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Page Content */}
          <div className="prose prose-invert prose-gold max-w-none">
            <div 
              className="rich-content"
              dangerouslySetInnerHTML={{ __html: page.content }}
              style={{
                color: '#e5e5e5',
                lineHeight: '1.8',
                fontSize: '1.1rem'
              }}
            />
          </div>

          {/* Tags */}
          {page.tags && page.tags.length > 0 && (
            <div className="mt-12 pt-8 border-t border-gold/20">
              <h3 className="text-lg font-semibold text-gold mb-4">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {page.tags.map((tag, index) => (
                  <Badge key={index} variant="outline" className="border-gold/30 text-gold">
                    #{tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Back to Home */}
          <div className="mt-12 text-center">
            <Link to="/">
              <Button variant="outline" className="border-gold text-gold hover:bg-gold hover:text-black">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Tilbage til forsiden
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-black border-t border-gold/20 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <Scissors className="h-8 w-8 text-gold mr-3" />
              <h2 className="text-2xl font-bold text-gold font-serif">{settings.site_title || 'Frisor LaFata'}</h2>
            </div>
            <p className="text-gray-300 mb-4">{settings.site_description || 'Klassisk barbering siden 2010'}</p>
            <p className="text-gray-400 text-sm mb-2">
              © 2024 Frisor LaFata. Alle rettigheder forbeholdes.
            </p>
          </div>
        </div>
      </footer>

      <style jsx>{`
        .rich-content h1,
        .rich-content h2,
        .rich-content h3,
        .rich-content h4,
        .rich-content h5,
        .rich-content h6 {
          color: #D4AF37;
          margin-top: 2rem;
          margin-bottom: 1rem;
          font-weight: bold;
        }
        
        .rich-content h1 {
          font-size: 2.5rem;
          border-bottom: 2px solid #D4AF37;
          padding-bottom: 0.5rem;
        }
        
        .rich-content h2 {
          font-size: 2rem;
          border-bottom: 1px solid #D4AF37;
          padding-bottom: 0.25rem;
        }
        
        .rich-content p {
          margin-bottom: 1.5rem;
        }
        
        .rich-content blockquote {
          border-left: 4px solid #D4AF37;
          padding-left: 1.5rem;
          margin: 2rem 0;
          font-style: italic;
          color: #D4AF37;
          background-color: rgba(212, 175, 55, 0.1);
          padding: 1rem 1.5rem;
          border-radius: 4px;
        }
        
        .rich-content img {
          max-width: 100%;
          height: auto;
          border-radius: 8px;
          margin: 2rem 0;
          box-shadow: 0 4px 20px rgba(212, 175, 55, 0.2);
        }
        
        .rich-content video {
          max-width: 100%;
          height: auto;
          border-radius: 8px;
          margin: 2rem 0;
        }
        
        .rich-content iframe {
          max-width: 100%;
          border-radius: 8px;
          margin: 2rem 0;
        }
        
        .rich-content ul,
        .rich-content ol {
          margin: 1.5rem 0;
          padding-left: 2rem;
        }
        
        .rich-content li {
          margin-bottom: 0.5rem;
        }
        
        .rich-content a {
          color: #D4AF37;
          text-decoration: underline;
        }
        
        .rich-content a:hover {
          color: #B8941F;
        }
        
        .rich-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 2rem 0;
        }
        
        .rich-content th,
        .rich-content td {
          border: 1px solid #D4AF37;
          padding: 0.75rem;
          text-align: left;
        }
        
        .rich-content th {
          background-color: rgba(212, 175, 55, 0.2);
          color: #D4AF37;
          font-weight: bold;
        }
      `}</style>
    </div>
  );
};

export default PublicPage;