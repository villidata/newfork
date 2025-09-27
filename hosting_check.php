<?php
// Check if your hosting supports Python for FastAPI backend
echo "<h1>🔍 Hosting Capability Check</h1>";
echo "<style>body{font-family:Arial;margin:20px;} .success{color:#28a745;} .error{color:#dc3545;} .info{color:#17a2b8;}</style>";

echo "<h2>Server Information</h2>";
echo "Server: " . $_SERVER['SERVER_SOFTWARE'] . "<br>";
echo "PHP Version: " . phpversion() . "<br>";

// Check if Python is available
echo "<h2>Python Support Check</h2>";
$python_check = shell_exec('python3 --version 2>&1');
if ($python_check) {
    echo "<div class='success'>✅ Python3: " . trim($python_check) . "</div>";
} else {
    $python_check = shell_exec('python --version 2>&1');
    if ($python_check) {
        echo "<div class='success'>✅ Python: " . trim($python_check) . "</div>";
    } else {
        echo "<div class='error'>❌ Python not available</div>";
    }
}

// Check pip
$pip_check = shell_exec('pip3 --version 2>&1');
if ($pip_check) {
    echo "<div class='success'>✅ pip3: " . trim($pip_check) . "</div>";
} else {
    echo "<div class='error'>❌ pip3 not available</div>";
}

echo "<h2>cPanel Features to Look For</h2>";
echo "<ul>";
echo "<li>Python Apps (in Software section)</li>";
echo "<li>Node.js Apps (alternative)</li>";
echo "<li>MySQL Databases</li>";
echo "<li>Cron Jobs</li>";
echo "</ul>";

echo "<h2>Next Steps</h2>";
echo "<p>If Python is available, you can set up FastAPI backend.</p>";
echo "<p>If not, you'll need to upgrade hosting or use external backend service.</p>";
?>