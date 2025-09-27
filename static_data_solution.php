<?php
/**
 * Static Data API Endpoints for Shared Hosting
 * This creates API endpoints using PHP instead of FastAPI
 * Temporary solution until external backend is set up
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://frisorlafata.dk');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');  
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    exit(0);
}

// Get the requested endpoint
$request = $_SERVER['REQUEST_URI'];
$path = parse_url($request, PHP_URL_PATH);
$path = str_replace('/api', '', $path);

// Route the request
switch ($path) {
    case '/settings':
        echo json_encode([
            'site_title' => 'Frisør LaFata',
            'hero_title' => 'Frisør LaFata',
            'hero_subtitle' => 'Klassik Barbering',
            'hero_description' => 'Oplev den autentiske barber-oplevelse hos Frisør LaFata. Vi kombinerer traditionel håndværk med moderne teknikker.',
            'hero_image' => 'https://images.unsplash.com/photo-1585747860715-2ba37e788b70',
            'hero_video' => null,
            'hero_video_enabled' => false,
            'hero_text_overlay_enabled' => true,
            'hero_image_opacity' => 30,
            'booking_system_enabled' => true,
            'contact_phone' => '+45 12 34 56 78',
            'contact_email' => 'info@frisorlafata.dk',
            'address' => 'Hovedgaden 123, 8000 Århus',
            'social_media_enabled' => true
        ]);
        break;
        
    case '/staff':
        echo json_encode([
            [
                'id' => '1',
                'name' => 'Anders Nielsen',
                'role' => 'Mester Frisør',
                'experience_years' => 15,
                'bio' => 'Specialist i klassisk herreklipning og traditionel barbering.',
                'avatar_url' => 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=300',
                'instagram_url' => '',
                'facebook_url' => '',
                'linkedin_url' => '',
                'twitter_url' => ''
            ],
            [
                'id' => '2', 
                'name' => 'Maria Larsen',
                'role' => 'Senior Frisør',
                'experience_years' => 8,
                'bio' => 'Ekspert i moderne styling og farveteknikker.',
                'avatar_url' => 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=300',
                'instagram_url' => '',
                'facebook_url' => '',
                'linkedin_url' => '',
                'twitter_url' => ''
            ]
        ]);
        break;
        
    case '/services':
        echo json_encode([
            [
                'id' => '1',
                'name' => 'Klassisk Herreklipning',
                'duration_minutes' => 45,
                'price' => 350,
                'description' => 'Traditionel herreklipning med saks og maskine',
                'category' => 'haircut',
                'icon' => 'scissors'
            ],
            [
                'id' => '2',
                'name' => 'Skæg Trimming',
                'duration_minutes' => 30,
                'price' => 250,
                'description' => 'Professionel skægtrimning og styling',
                'category' => 'beard',
                'icon' => 'beard'
            ],
            [
                'id' => '3',
                'name' => 'Traditionel Barbering',
                'duration_minutes' => 60,
                'price' => 450,
                'description' => 'Komplet barbering med varmt håndklæde',
                'category' => 'shave',
                'icon' => 'razor'
            ]
        ]);
        break;
        
    case '/gallery':
        echo json_encode([]);
        break;
        
    case '/pages':
        echo json_encode([
            [
                'id' => '1',
                'title' => 'Om Os',
                'slug' => 'about',
                'content' => 'Velkommen til Frisør LaFata - din lokale barbershop siden 2010.',
                'is_published' => true
            ]
        ]);
        break;
        
    default:
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint not found']);
        break;
}
?>