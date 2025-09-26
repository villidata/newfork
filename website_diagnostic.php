<?php
/**
 * Frisør LaFata Website Diagnostic Script
 * Checks all files and configurations for proper setup
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);

class WebsiteDiagnostic {
    private $results = [];
    private $errors = [];
    private $warnings = [];
    
    public function __construct() {
        echo "<h1>🔍 Frisør LaFata Website Diagnostic</h1>";
        echo "<style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .success { color: #28a745; }
            .error { color: #dc3545; }
            .warning { color: #ffc107; }
            .info { color: #17a2b8; }
            .section { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
            .file-check { margin: 5px 0; }
        </style>";
    }
    
    public function runFullDiagnostic() {
        echo "<div class='info'>Starting comprehensive diagnostic...</div>";
        
        $this->checkEssentialFiles();
        $this->checkHtaccessFile();
        $this->checkIndexHtml();
        $this->checkJavaScriptFiles();
        $this->checkCSSFiles();
        $this->checkTinyMCE();
        $this->checkBackendConnection();
        $this->checkCommonIssues();
        $this->generateReport();
    }
    
    private function checkEssentialFiles() {
        echo "<div class='section'>";
        echo "<h2>📁 Essential Files Check</h2>";
        
        $requiredFiles = [
            'index.html' => 'Main website file',
            '.htaccess' => 'React Router configuration',
            'asset-manifest.json' => 'Asset references',
            'static/js/' => 'JavaScript files directory',
            'static/css/' => 'CSS files directory',
            'tinymce/tinymce.min.js' => 'TinyMCE editor'
        ];
        
        foreach ($requiredFiles as $file => $description) {
            $exists = file_exists($file) || is_dir($file);
            $status = $exists ? "✅" : "❌";
            $class = $exists ? "success" : "error";
            
            echo "<div class='file-check $class'>$status $file - $description</div>";
            
            if (!$exists) {
                $this->errors[] = "Missing: $file ($description)";
            }
        }
        echo "</div>";
    }
    
    private function checkHtaccessFile() {
        echo "<div class='section'>";
        echo "<h2>⚙️ .htaccess Configuration</h2>";
        
        if (file_exists('.htaccess')) {
            $htaccess = file_get_contents('.htaccess');
            echo "<div class='success'>✅ .htaccess file exists</div>";
            
            // Check for React Router rules
            if (strpos($htaccess, 'RewriteEngine On') !== false) {
                echo "<div class='success'>✅ RewriteEngine is enabled</div>";
            } else {
                echo "<div class='error'>❌ RewriteEngine not found</div>";
                $this->errors[] = ".htaccess missing RewriteEngine On";
            }
            
            if (strpos($htaccess, 'index.html') !== false) {
                echo "<div class='success'>✅ React Router rules present</div>";
            } else {
                echo "<div class='error'>❌ React Router rules missing</div>";
                $this->errors[] = ".htaccess missing React Router rules";
            }
            
            echo "<h3>Current .htaccess content:</h3>";
            echo "<pre>" . htmlspecialchars($htaccess) . "</pre>";
        } else {
            echo "<div class='error'>❌ .htaccess file is missing!</div>";
            $this->errors[] = "Missing .htaccess file";
            
            echo "<h3>Required .htaccess content:</h3>";
            echo "<pre>RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]
RewriteRule ^admin/?$ /index.html [L,QSA]</pre>";
        }
        echo "</div>";
    }
    
    private function checkIndexHtml() {
        echo "<div class='section'>";
        echo "<h2>🏠 index.html Analysis</h2>";
        
        if (file_exists('index.html')) {
            $content = file_get_contents('index.html');
            echo "<div class='success'>✅ index.html exists</div>";
            
            // Check for React app div
            if (strpos($content, 'id="root"') !== false) {
                echo "<div class='success'>✅ React root div found</div>";
            } else {
                echo "<div class='error'>❌ React root div missing</div>";
                $this->errors[] = "index.html missing React root div";
            }
            
            // Check for JavaScript files
            if (strpos($content, 'static/js/main.') !== false) {
                echo "<div class='success'>✅ Main JavaScript file referenced</div>";
            } else {
                echo "<div class='error'>❌ Main JavaScript file not referenced</div>";
                $this->errors[] = "index.html not referencing main JavaScript";
            }
            
            // Check for CSS files
            if (strpos($content, 'static/css/main.') !== false) {
                echo "<div class='success'>✅ Main CSS file referenced</div>";
            } else {
                echo "<div class='error'>❌ Main CSS file not referenced</div>";
                $this->errors[] = "index.html not referencing main CSS";
            }
            
            // Extract and show referenced files
            preg_match_all('/static\/(js|css)\/[^"\']+/', $content, $matches);
            if (!empty($matches[0])) {
                echo "<h3>Referenced static files:</h3>";
                foreach ($matches[0] as $file) {
                    $exists = file_exists($file);
                    $status = $exists ? "✅" : "❌";
                    $class = $exists ? "success" : "error";
                    echo "<div class='$class'>$status $file</div>";
                    
                    if (!$exists) {
                        $this->errors[] = "Referenced file missing: $file";
                    }
                }
            }
        } else {
            echo "<div class='error'>❌ index.html is missing!</div>";
            $this->errors[] = "Missing index.html file";
        }
        echo "</div>";
    }
    
    private function checkJavaScriptFiles() {
        echo "<div class='section'>";
        echo "<h2>📜 JavaScript Files Check</h2>";
        
        $jsDir = 'static/js/';
        if (is_dir($jsDir)) {
            $jsFiles = glob($jsDir . '*.js');
            echo "<div class='success'>✅ JavaScript directory exists</div>";
            echo "<div class='info'>Found " . count($jsFiles) . " JavaScript files</div>";
            
            foreach ($jsFiles as $file) {
                $size = filesize($file);
                $sizeKB = round($size / 1024, 2);
                echo "<div class='success'>✅ $file ($sizeKB KB)</div>";
                
                // Check if main JS file is suspiciously small
                if (strpos($file, 'main.') !== false && $size < 10000) {
                    echo "<div class='warning'>⚠️ Main JS file seems small - might be corrupted</div>";
                    $this->warnings[] = "Main JavaScript file is unusually small";
                }
            }
        } else {
            echo "<div class='error'>❌ JavaScript directory missing</div>";
            $this->errors[] = "Missing static/js/ directory";
        }
        echo "</div>";
    }
    
    private function checkCSSFiles() {
        echo "<div class='section'>";
        echo "<h2>🎨 CSS Files Check</h2>";
        
        $cssDir = 'static/css/';
        if (is_dir($cssDir)) {
            $cssFiles = glob($cssDir . '*.css');
            echo "<div class='success'>✅ CSS directory exists</div>";
            echo "<div class='info'>Found " . count($cssFiles) . " CSS files</div>";
            
            foreach ($cssFiles as $file) {
                $size = filesize($file);
                $sizeKB = round($size / 1024, 2);
                echo "<div class='success'>✅ $file ($sizeKB KB)</div>";
            }
        } else {
            echo "<div class='error'>❌ CSS directory missing</div>";
            $this->errors[] = "Missing static/css/ directory";
        }
        echo "</div>";
    }
    
    private function checkTinyMCE() {
        echo "<div class='section'>";
        echo "<h2>📝 TinyMCE Editor Check</h2>";
        
        $tinyMCEFiles = [
            'tinymce/tinymce.min.js' => 'Main TinyMCE file',
            'tinymce/themes/silver/' => 'Silver theme',
            'tinymce/plugins/' => 'Plugins directory',
            'tinymce/skins/ui/oxide/' => 'Oxide skin'
        ];
        
        foreach ($tinyMCEFiles as $file => $description) {
            $exists = file_exists($file) || is_dir($file);
            $status = $exists ? "✅" : "❌";
            $class = $exists ? "success" : "error";
            echo "<div class='$class'>$status $file - $description</div>";
            
            if (!$exists) {
                $this->errors[] = "TinyMCE missing: $file";
            }
        }
        
        // Check if TinyMCE is properly sized
        if (file_exists('tinymce/tinymce.min.js')) {
            $size = filesize('tinymce/tinymce.min.js');
            $sizeKB = round($size / 1024, 2);
            echo "<div class='info'>TinyMCE size: {$sizeKB} KB</div>";
            
            if ($size < 100000) { // Less than 100KB seems wrong
                echo "<div class='warning'>⚠️ TinyMCE file seems corrupted or incomplete</div>";
                $this->warnings[] = "TinyMCE file is suspiciously small";
            }
        }
        echo "</div>";
    }
    
    private function checkBackendConnection() {
        echo "<div class='section'>";
        echo "<h2>🔗 Backend Connection Test</h2>";
        
        // Try to determine backend URL from index.html
        $backendUrl = 'https://frisorlafata.dk'; // Default
        
        if (file_exists('index.html')) {
            $content = file_get_contents('index.html');
            // Look for backend URL in the compiled JavaScript
            if (preg_match('/https?:\/\/[^"\']+preview\.emergentagent\.com/', $content, $matches)) {
                $backendUrl = $matches[0];
                echo "<div class='warning'>⚠️ Using Emergent backend: $backendUrl</div>";
                $this->warnings[] = "Using temporary Emergent backend";
            } elseif (preg_match('/https?:\/\/[^"\']+frisorlafata\.dk/', $content, $matches)) {
                $backendUrl = $matches[0];
                echo "<div class='info'>Using your domain backend: $backendUrl</div>";
            }
        }
        
        // Test backend connection
        $testUrl = $backendUrl . '/api/settings';
        echo "<div class='info'>Testing: $testUrl</div>";
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $testUrl);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($httpCode == 200) {
            echo "<div class='success'>✅ Backend connection successful</div>";
            if ($response) {
                $data = json_decode($response, true);
                if ($data) {
                    echo "<div class='success'>✅ Valid JSON response received</div>";
                } else {
                    echo "<div class='warning'>⚠️ Response is not valid JSON</div>";
                }
            }
        } else {
            echo "<div class='error'>❌ Backend connection failed (HTTP $httpCode)</div>";
            if ($error) {
                echo "<div class='error'>Error: $error</div>";
            }
            $this->errors[] = "Backend connection failed";
        }
        echo "</div>";
    }
    
    private function checkCommonIssues() {
        echo "<div class='section'>";
        echo "<h2>🚨 Common Issues Check</h2>";
        
        // Check file permissions
        $files = ['index.html', '.htaccess'];
        foreach ($files as $file) {
            if (file_exists($file)) {
                $perms = substr(sprintf('%o', fileperms($file)), -4);
                if ($perms == '0644' || $perms == '0664') {
                    echo "<div class='success'>✅ $file permissions: $perms</div>";
                } else {
                    echo "<div class='warning'>⚠️ $file permissions: $perms (should be 644)</div>";
                    $this->warnings[] = "$file has unusual permissions: $perms";
                }
            }
        }
        
        // Check for common admin panel issues
        echo "<h3>Admin Panel Black Screen Diagnostics:</h3>";
        
        // Check if main JS file contains React components
        $jsFiles = glob('static/js/main.*.js');
        if (!empty($jsFiles)) {
            $jsContent = file_get_contents($jsFiles[0]);
            
            if (strpos($jsContent, 'AdminDashboard') !== false) {
                echo "<div class='success'>✅ AdminDashboard component found in JS</div>";
            } else {
                echo "<div class='error'>❌ AdminDashboard component missing from JS</div>";
                $this->errors[] = "AdminDashboard component not found in compiled JavaScript";
            }
            
            if (strpos($jsContent, 'React') !== false) {
                echo "<div class='success'>✅ React library found in JS</div>";
            } else {
                echo "<div class='error'>❌ React library missing from JS</div>";
                $this->errors[] = "React library not found in compiled JavaScript";
            }
            
            // Check for common error patterns
            if (strpos($jsContent, 'Cannot read prop') !== false) {
                echo "<div class='warning'>⚠️ Potential property access errors in JS</div>";
                $this->warnings[] = "JavaScript may have property access errors";
            }
        }
        
        echo "</div>";
    }
    
    private function generateReport() {
        echo "<div class='section'>";
        echo "<h2>📊 Diagnostic Report</h2>";
        
        $totalErrors = count($this->errors);
        $totalWarnings = count($this->warnings);
        
        if ($totalErrors == 0 && $totalWarnings == 0) {
            echo "<div class='success'><h3>🎉 All checks passed!</h3></div>";
            echo "<p>Your website appears to be properly configured.</p>";
        } else {
            if ($totalErrors > 0) {
                echo "<div class='error'><h3>❌ Critical Issues Found ($totalErrors):</h3></div>";
                echo "<ul>";
                foreach ($this->errors as $error) {
                    echo "<li class='error'>$error</li>";
                }
                echo "</ul>";
            }
            
            if ($totalWarnings > 0) {
                echo "<div class='warning'><h3>⚠️ Warnings ($totalWarnings):</h3></div>";
                echo "<ul>";
                foreach ($this->warnings as $warning) {
                    echo "<li class='warning'>$warning</li>";
                }
                echo "</ul>";
            }
        }
        
        // Specific fix for admin panel black screen
        if ($totalErrors > 0) {
            echo "<div class='info'>";
            echo "<h3>🔧 Recommended Fixes for Admin Panel Black Screen:</h3>";
            echo "<ol>";
            echo "<li><strong>Re-upload all files:</strong> Extract and upload all files from FRONTEND-YOUR-DOMAIN.zip</li>";
            echo "<li><strong>Check .htaccess:</strong> Ensure React Router rules are present</li>";
            echo "<li><strong>Clear browser cache:</strong> Hard refresh with Ctrl+F5</li>";
            echo "<li><strong>Check browser console:</strong> Press F12 and look for JavaScript errors</li>";
            echo "<li><strong>Verify TinyMCE:</strong> Ensure tinymce folder is uploaded completely</li>";
            echo "</ol>";
            echo "</div>";
        }
        
        echo "</div>";
        
        // System info
        echo "<div class='section'>";
        echo "<h2>ℹ️ System Information</h2>";
        echo "<div>PHP Version: " . PHP_VERSION . "</div>";
        echo "<div>Server: " . $_SERVER['SERVER_SOFTWARE'] . "</div>";
        echo "<div>Document Root: " . $_SERVER['DOCUMENT_ROOT'] . "</div>";
        echo "<div>Current Directory: " . getcwd() . "</div>";
        echo "<div>Mod Rewrite: " . (function_exists('apache_get_modules') && in_array('mod_rewrite', apache_get_modules()) ? '✅ Enabled' : '❓ Unknown') . "</div>";
        echo "</div>";
    }
}

// Run the diagnostic
$diagnostic = new WebsiteDiagnostic();
$diagnostic->runFullDiagnostic();

echo "<div style='margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 5px;'>";
echo "<strong>📋 How to use this script:</strong><br>";
echo "1. Upload this file (website_diagnostic.php) to your public_html/ directory<br>";
echo "2. Visit: https://frisorlafata.dk/website_diagnostic.php<br>";
echo "3. Follow the recommendations to fix any issues<br>";
echo "4. Delete this file after fixing issues for security";
echo "</div>";
?>