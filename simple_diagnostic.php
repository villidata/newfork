<?php
// Simple Website Diagnostic - Compatible Version
ini_set('display_errors', 1);
error_reporting(E_ALL);

echo "<!DOCTYPE html><html><head><title>Website Diagnostic</title>";
echo "<style>body{font-family:Arial;margin:20px;background:#f5f5f5;} .success{color:#28a745;} .error{color:#dc3545;} .warning{color:#ffc107;} .section{background:white;padding:15px;margin:10px 0;border-radius:5px;} pre{background:#f8f9fa;padding:10px;border-radius:4px;}</style></head><body>";

echo "<h1>🔍 Frisor LaFata Diagnostic</h1>";

// Basic PHP info
echo "<div class='section'>";
echo "<h2>PHP Information</h2>";
echo "PHP Version: " . phpversion() . "<br>";
echo "Server: " . (isset($_SERVER['SERVER_SOFTWARE']) ? $_SERVER['SERVER_SOFTWARE'] : 'Unknown') . "<br>";
echo "Document Root: " . (isset($_SERVER['DOCUMENT_ROOT']) ? $_SERVER['DOCUMENT_ROOT'] : 'Unknown') . "<br>";
echo "</div>";

// Check essential files
echo "<div class='section'>";
echo "<h2>📁 File Check</h2>";

$files = array(
    'index.html' => 'Main website',
    '.htaccess' => 'URL routing',
    'asset-manifest.json' => 'Asset map',
    'static/js/' => 'JavaScript folder',
    'static/css/' => 'CSS folder',
    'tinymce/tinymce.min.js' => 'Text editor'
);

foreach($files as $file => $desc) {
    $exists = file_exists($file) || is_dir($file);
    $status = $exists ? "✅" : "❌";
    $class = $exists ? "success" : "error";
    echo "<div class='$class'>$status $file - $desc</div>";
}
echo "</div>";

// Check .htaccess
echo "<div class='section'>";
echo "<h2>⚙️ .htaccess Check</h2>";
if(file_exists('.htaccess')) {
    $htaccess = file_get_contents('.htaccess');
    echo "<div class='success'>✅ .htaccess exists</div>";
    
    if(strpos($htaccess, 'RewriteEngine On') !== false) {
        echo "<div class='success'>✅ RewriteEngine found</div>";
    } else {
        echo "<div class='error'>❌ RewriteEngine missing</div>";
    }
    
    if(strpos($htaccess, 'index.html') !== false) {
        echo "<div class='success'>✅ React routing found</div>";
    } else {
        echo "<div class='error'>❌ React routing missing</div>";
    }
    
    echo "<h3>Content:</h3><pre>" . htmlspecialchars($htaccess) . "</pre>";
} else {
    echo "<div class='error'>❌ .htaccess missing</div>";
    echo "<h3>Required .htaccess:</h3>";
    echo "<pre>RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d  
RewriteRule . /index.html [L]</pre>";
}
echo "</div>";

// Check index.html
echo "<div class='section'>";
echo "<h2>🏠 index.html Check</h2>";
if(file_exists('index.html')) {
    $content = file_get_contents('index.html');
    echo "<div class='success'>✅ index.html exists (" . strlen($content) . " chars)</div>";
    
    if(strpos($content, 'id="root"') !== false) {
        echo "<div class='success'>✅ React root found</div>";
    } else {
        echo "<div class='error'>❌ React root missing</div>";
    }
    
    // Check for backend URL
    if(strpos($content, 'emergentagent.com') !== false) {
        echo "<div class='warning'>⚠️ Using Emergent backend</div>";
    } elseif(strpos($content, 'frisorlafata.dk') !== false) {
        echo "<div class='success'>✅ Using your domain backend</div>";
    }
} else {
    echo "<div class='error'>❌ index.html missing</div>";
}
echo "</div>";

// Check static files
echo "<div class='section'>";
echo "<h2>📜 Static Files</h2>";

if(is_dir('static/js/')) {
    $jsFiles = glob('static/js/*.js');
    echo "<div class='success'>✅ JS folder exists (" . count($jsFiles) . " files)</div>";
    foreach($jsFiles as $file) {
        $size = round(filesize($file)/1024, 1);
        echo "<div class='success'>✅ $file ({$size}KB)</div>";
    }
} else {
    echo "<div class='error'>❌ JS folder missing</div>";
}

if(is_dir('static/css/')) {
    $cssFiles = glob('static/css/*.css');
    echo "<div class='success'>✅ CSS folder exists (" . count($cssFiles) . " files)</div>";
    foreach($cssFiles as $file) {
        $size = round(filesize($file)/1024, 1);
        echo "<div class='success'>✅ $file ({$size}KB)</div>";
    }
} else {
    echo "<div class='error'>❌ CSS folder missing</div>";
}
echo "</div>";

// Admin black screen specific checks
echo "<div class='section'>";
echo "<h2>🚨 Admin Panel Issues</h2>";
echo "<div class='warning'>Common causes of black admin screen:</div>";
echo "<ul>";
echo "<li>Missing JavaScript files</li>";
echo "<li>Corrupted TinyMCE files</li>";
echo "<li>Backend connection failed</li>";
echo "<li>Browser cache issues</li>";
echo "</ul>";

echo "<h3>Quick Fixes:</h3>";
echo "<ol>";
echo "<li><strong>Clear browser cache:</strong> Ctrl+F5</li>";
echo "<li><strong>Check browser console:</strong> Press F12, look for errors</li>";
echo "<li><strong>Re-upload files:</strong> Extract and upload ALL files from ZIP</li>";
echo "<li><strong>Check TinyMCE:</strong> Ensure tinymce folder uploaded completely</li>";
echo "</ol>";
echo "</div>";

echo "<div class='section'>";
echo "<h2>🔧 Browser Console Check</h2>";
echo "<p>To check for JavaScript errors:</p>";
echo "<ol>";
echo "<li>Go to https://frisorlafata.dk/admin</li>";
echo "<li>Press F12 to open developer tools</li>";
echo "<li>Click 'Console' tab</li>";
echo "<li>Look for red error messages</li>";
echo "<li>Common errors: 'Failed to load resource', 'Cannot read property', 'tinymce is not defined'</li>";
echo "</ol>";
echo "</div>";

echo "</body></html>";
?>