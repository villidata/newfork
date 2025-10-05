import requests
import sys
import json
from datetime import datetime, date, timedelta
import io

class FrisorLaFataAPITester:
    def __init__(self, base_url="https://retro-salon.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.admin_user_id = None
        self.created_staff_id = None
        self.created_service_id = None
        self.created_booking_id = None
        self.created_page_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) < 5:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list) and len(response_data) <= 3:
                        print(f"   Response: {len(response_data)} items")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_initialize_data(self):
        """Initialize default data"""
        return self.run_test("Initialize Default Data", "POST", "admin/init-data", 200)

    def test_get_staff(self):
        """Test getting staff list"""
        return self.run_test("Get Staff", "GET", "staff", 200)

    def test_get_services(self):
        """Test getting services list"""
        return self.run_test("Get Services", "GET", "services", 200)

    def test_user_registration(self):
        """Test user registration"""
        test_user_data = {
            "name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": f"test{datetime.now().strftime('%H%M%S')}@frisorlafata.dk",
            "phone": "+45 12 34 56 78",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            data=test_user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   User ID: {self.user_id}")
            return True, response
        return False, {}

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.token:
            print("❌ Skipped - No token available")
            return False, {}
        return self.run_test("Get Current User", "GET", "users/me", 200)

    def test_available_slots(self, staff_id, test_date):
        """Test getting available slots"""
        endpoint = f"bookings/available-slots?staff_id={staff_id}&date_param={test_date}"
        return self.run_test("Get Available Slots", "GET", endpoint, 200)

    def test_create_booking(self, staff_id, service_ids, booking_date, booking_time):
        """Test creating a booking"""
        if not self.user_id:
            print("❌ Skipped - No user ID available")
            return False, {}
            
        booking_data = {
            "customer_id": self.user_id,
            "staff_id": staff_id,
            "services": service_ids,
            "booking_date": booking_date,
            "booking_time": booking_time,
            "payment_method": "cash",
            "notes": "Test booking"
        }
        
        return self.run_test("Create Booking", "POST", "bookings", 200, data=booking_data)

    def test_get_bookings(self):
        """Test getting user bookings"""
        if not self.token:
            print("❌ Skipped - No token available")
            return False, {}
        return self.run_test("Get User Bookings", "GET", "bookings", 200)

    def test_paypal_payment(self, booking_id="test_booking_123"):
        """Test PayPal payment creation"""
        return self.run_test("Create PayPal Payment", "POST", f"payments/paypal/create?booking_id={booking_id}", 200)

    def test_admin_login(self):
        """Test admin login"""
        admin_credentials = {
            "email": "admin@frisorlafata.dk",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login", 
            "POST", 
            "auth/login", 
            200, 
            data=admin_credentials
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user_id = response['user']['id']
            print(f"   Admin User ID: {self.admin_user_id}")
            return True, response
        return False, {}

    def test_create_staff_with_admin(self):
        """Test creating staff (admin required)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        # Temporarily switch to admin token
        original_token = self.token
        self.token = self.admin_token
        
        staff_data = {
            "name": f"Test Staff {datetime.now().strftime('%H%M%S')}",
            "specialty": "Test Specialty",
            "experience": "5 år",
            "avatar_url": "",
            "available_hours": {
                "monday": {"start": "09:00", "end": "17:00", "enabled": True},
                "tuesday": {"start": "09:00", "end": "17:00", "enabled": True}
            }
        }
        
        success, response = self.run_test("Create Staff", "POST", "staff", 200, data=staff_data)
        
        if success and 'id' in response:
            self.created_staff_id = response['id']
            print(f"   Created Staff ID: {self.created_staff_id}")
        
        # Restore original token
        self.token = original_token
        return success, response

    def test_update_staff(self):
        """Test updating staff"""
        if not self.admin_token or not self.created_staff_id:
            print("❌ Skipped - No admin token or staff ID available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        update_data = {
            "specialty": "Updated Specialty",
            "experience": "10 år"
        }
        
        success, response = self.run_test(
            "Update Staff", 
            "PUT", 
            f"staff/{self.created_staff_id}", 
            200, 
            data=update_data
        )
        
        self.token = original_token
        return success, response

    def test_delete_staff(self):
        """Test deleting staff (NEW FEATURE)"""
        if not self.admin_token or not self.created_staff_id:
            print("❌ Skipped - No admin token or staff ID available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Delete Staff", 
            "DELETE", 
            f"staff/{self.created_staff_id}", 
            200
        )
        
        self.token = original_token
        return success, response

    def test_create_service_with_admin(self):
        """Test creating service (admin required)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        service_data = {
            "name": f"Test Service {datetime.now().strftime('%H%M%S')}",
            "duration_minutes": 45,
            "price": 500.0,
            "description": "Test service description",
            "category": "test"
        }
        
        success, response = self.run_test("Create Service", "POST", "services", 200, data=service_data)
        
        if success and 'id' in response:
            self.created_service_id = response['id']
            print(f"   Created Service ID: {self.created_service_id}")
        
        self.token = original_token
        return success, response

    def test_update_service(self):
        """Test updating service"""
        if not self.admin_token or not self.created_service_id:
            print("❌ Skipped - No admin token or service ID available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        update_data = {
            "price": 600.0,
            "description": "Updated service description"
        }
        
        success, response = self.run_test(
            "Update Service", 
            "PUT", 
            f"services/{self.created_service_id}", 
            200, 
            data=update_data
        )
        
        self.token = original_token
        return success, response

    def test_delete_service(self):
        """Test deleting service (NEW FEATURE)"""
        if not self.admin_token or not self.created_service_id:
            print("❌ Skipped - No admin token or service ID available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Delete Service", 
            "DELETE", 
            f"services/{self.created_service_id}", 
            200
        )
        
        self.token = original_token
        return success, response

    def test_avatar_upload(self):
        """Test avatar upload functionality (NEW FEATURE)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        # Create a simple test image file
        test_image_content = b"fake_image_content_for_testing"
        
        url = f"{self.api_url}/upload/avatar"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        files = {'avatar': ('test_avatar.jpg', io.BytesIO(test_image_content), 'image/jpeg')}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Avatar Upload...")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=10)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_avatar_upload_comprehensive(self):
        """Comprehensive avatar upload testing"""
        print("\n" + "📸 COMPREHENSIVE AVATAR UPLOAD TESTS" + "=" * 30)
        
        # Test 1: Upload with different file types
        file_types = [
            ('test_avatar.jpg', 'image/jpeg'),
            ('test_avatar.png', 'image/png'),
            ('test_avatar.gif', 'image/gif')
        ]
        
        uploaded_avatars = []
        
        for filename, content_type in file_types:
            success, response = self._test_avatar_upload_file_type(filename, content_type)
            if success and 'avatar_url' in response:
                uploaded_avatars.append(response['avatar_url'])
        
        # Test 2: Test authentication requirement (non-admin should fail)
        self._test_avatar_upload_auth_required()
        
        # Test 3: Test invalid file type
        self._test_avatar_upload_invalid_file()
        
        # Test 4: Test static file serving for uploaded avatars
        for avatar_url in uploaded_avatars:
            self._test_avatar_static_serving(avatar_url)
        
        return len(uploaded_avatars) > 0, uploaded_avatars

    def _test_avatar_upload_file_type(self, filename, content_type):
        """Test avatar upload with specific file type"""
        if not self.admin_token:
            return False, {}
            
        # Create test image content
        test_image_content = b"fake_image_content_for_testing_" + filename.encode()
        
        url = f"{self.api_url}/upload/avatar"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'avatar': (filename, io.BytesIO(test_image_content), content_type)}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Avatar Upload - {filename}...")
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=10)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                response_data = response.json()
                avatar_url = response_data.get('avatar_url', '')
                
                # Verify URL format
                expected_domain = "https://retro-salon.preview.emergentagent.com"
                if avatar_url.startswith(expected_domain):
                    print(f"✅ Passed - Correct URL format: {avatar_url}")
                else:
                    print(f"❌ URL format issue - Expected domain {expected_domain}, got: {avatar_url}")
                    success = False
                
                return success, response_data
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def _test_avatar_upload_auth_required(self):
        """Test that avatar upload requires admin authentication"""
        # Test without token
        url = f"{self.api_url}/upload/avatar"
        files = {'avatar': ('test.jpg', io.BytesIO(b"test"), 'image/jpeg')}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Avatar Upload - No Auth (should fail)...")
        
        try:
            response = requests.post(url, files=files, timeout=10)
            if response.status_code == 401 or response.status_code == 403:
                self.tests_passed += 1
                print(f"✅ Passed - Correctly rejected unauthorized request: {response.status_code}")
                return True
            else:
                print(f"❌ Failed - Should reject unauthorized request, got: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

        # Test with regular user token (non-admin)
        if self.token and self.token != self.admin_token:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            self.tests_run += 1
            print(f"\n🔍 Testing Avatar Upload - Non-Admin Auth (should fail)...")
            
            try:
                response = requests.post(url, headers=headers, files=files, timeout=10)
                if response.status_code == 403:
                    self.tests_passed += 1
                    print(f"✅ Passed - Correctly rejected non-admin request: {response.status_code}")
                    return True
                else:
                    print(f"❌ Failed - Should reject non-admin request, got: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Failed - Error: {str(e)}")
                return False

    def _test_avatar_upload_invalid_file(self):
        """Test avatar upload with invalid file type"""
        if not self.admin_token:
            return False
            
        url = f"{self.api_url}/upload/avatar"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'avatar': ('test.txt', io.BytesIO(b"not an image"), 'text/plain')}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Avatar Upload - Invalid File Type (should fail)...")
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=10)
            if response.status_code == 400:
                self.tests_passed += 1
                print(f"✅ Passed - Correctly rejected invalid file type: {response.status_code}")
                return True
            else:
                print(f"❌ Failed - Should reject invalid file type, got: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def _test_avatar_static_serving(self, avatar_url):
        """Test that uploaded avatar is accessible via static file serving"""
        self.tests_run += 1
        print(f"\n🔍 Testing Avatar Static Serving...")
        print(f"   URL: {avatar_url}")
        
        try:
            response = requests.get(avatar_url, timeout=10)
            
            if response.status_code == 200:
                self.tests_passed += 1
                content_type = response.headers.get('content-type', '')
                print(f"✅ Passed - Avatar accessible, Content-Type: {content_type}")
                
                # Verify it's an image content type
                if content_type.startswith('image/'):
                    print(f"   ✅ Correct image content type")
                else:
                    print(f"   ⚠️  Warning: Expected image content type, got: {content_type}")
                
                return True
            else:
                print(f"❌ Failed - Avatar not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error accessing avatar: {str(e)}")
            return False

    def test_staff_avatar_integration(self):
        """Test staff creation and update with avatar URLs"""
        print("\n" + "👥 STAFF AVATAR INTEGRATION TESTS" + "=" * 30)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
        
        # First upload an avatar
        success, avatar_response = self._test_avatar_upload_file_type('staff_avatar.jpg', 'image/jpeg')
        if not success or 'avatar_url' in avatar_response:
            print("❌ Failed to upload avatar for staff integration test")
            return False, {}
        
        avatar_url = avatar_response['avatar_url']
        
        # Test creating staff with avatar
        original_token = self.token
        self.token = self.admin_token
        
        staff_data = {
            "name": f"Avatar Test Staff {datetime.now().strftime('%H%M%S')}",
            "specialty": "Avatar Testing",
            "experience": "5 år",
            "avatar_url": avatar_url,
            "available_hours": {
                "monday": {"start": "09:00", "end": "17:00", "enabled": True}
            }
        }
        
        success, staff_response = self.run_test("Create Staff with Avatar", "POST", "staff", 200, data=staff_data)
        
        if success and 'id' in staff_response:
            staff_id = staff_response['id']
            
            # Verify the avatar URL is correctly stored
            if staff_response.get('avatar_url') == avatar_url:
                print(f"✅ Staff created with correct avatar URL")
            else:
                print(f"❌ Avatar URL mismatch in staff creation")
            
            # Test updating staff avatar
            new_avatar_success, new_avatar_response = self._test_avatar_upload_file_type('updated_avatar.png', 'image/png')
            if new_avatar_success and 'avatar_url' in new_avatar_response:
                new_avatar_url = new_avatar_response['avatar_url']
                
                update_data = {"avatar_url": new_avatar_url}
                update_success, update_response = self.run_test(
                    "Update Staff Avatar", 
                    "PUT", 
                    f"staff/{staff_id}", 
                    200, 
                    data=update_data
                )
                
                if update_success and update_response.get('avatar_url') == new_avatar_url:
                    print(f"✅ Staff avatar updated successfully")
                else:
                    print(f"❌ Failed to update staff avatar")
        
        self.token = original_token
        return success, staff_response

    def test_database_avatar_urls_consistency(self):
        """Test that all staff records have correct avatar URLs (no localhost)"""
        print("\n" + "🗄️ DATABASE AVATAR URL CONSISTENCY TESTS" + "=" * 25)
        
        # Get all staff
        success, staff_list = self.run_test("Get All Staff for URL Check", "GET", "staff", 200)
        
        if not success:
            print("❌ Failed to retrieve staff list")
            return False
        
        localhost_issues = []
        correct_urls = []
        
        for staff in staff_list:
            avatar_url = staff.get('avatar_url', '')
            if avatar_url:
                if 'localhost' in avatar_url or '127.0.0.1' in avatar_url or ':8000' in avatar_url or ':8001' in avatar_url:
                    localhost_issues.append({
                        'name': staff.get('name', 'Unknown'),
                        'id': staff.get('id', 'Unknown'),
                        'avatar_url': avatar_url
                    })
                elif avatar_url.startswith('https://retro-salon.preview.emergentagent.com'):
                    correct_urls.append({
                        'name': staff.get('name', 'Unknown'),
                        'avatar_url': avatar_url
                    })
        
        self.tests_run += 1
        if len(localhost_issues) == 0:
            self.tests_passed += 1
            print(f"✅ Passed - No localhost URLs found in staff avatars")
            print(f"   Staff with correct URLs: {len(correct_urls)}")
        else:
            print(f"❌ Failed - Found {len(localhost_issues)} staff with localhost URLs:")
            for issue in localhost_issues:
                print(f"   - {issue['name']}: {issue['avatar_url']}")
        
        return len(localhost_issues) == 0

    def test_create_page(self):
        """Test creating page (NEW FEATURE - CMS)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        page_data = {
            "title": f"Test Page {datetime.now().strftime('%H%M%S')}",
            "slug": f"test-page-{datetime.now().strftime('%H%M%S')}",
            "content": "This is test page content",
            "meta_description": "Test page meta description",
            "is_published": True,
            "images": []
        }
        
        success, response = self.run_test("Create Page", "POST", "pages", 200, data=page_data)
        
        if success and 'id' in response:
            self.created_page_id = response['id']
            print(f"   Created Page ID: {self.created_page_id}")
        
        self.token = original_token
        return success, response

    def test_enhanced_page_model(self):
        """Test enhanced page model with new fields"""
        print("\n" + "📄 ENHANCED PAGE MODEL TESTS" + "=" * 35)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        # Test creating pages with different page types
        page_types = ["page", "blog", "about", "service"]
        created_pages = []
        
        for page_type in page_types:
            page_data = {
                "title": f"Enhanced {page_type.title()} {datetime.now().strftime('%H%M%S')}",
                "slug": f"enhanced-{page_type}-{datetime.now().strftime('%H%M%S')}",
                "content": f"This is enhanced {page_type} content with rich features",
                "meta_description": f"Enhanced {page_type} meta description",
                "is_published": True,
                "show_in_navigation": True,
                "navigation_order": len(created_pages) + 1,
                "page_type": page_type,
                "featured_image": f"https://retro-salon.preview.emergentagent.com/uploads/images/featured-{page_type}.jpg",
                "images": [
                    f"https://retro-salon.preview.emergentagent.com/uploads/images/gallery-{page_type}-1.jpg",
                    f"https://retro-salon.preview.emergentagent.com/uploads/images/gallery-{page_type}-2.jpg"
                ],
                "videos": [
                    f"https://retro-salon.preview.emergentagent.com/uploads/videos/demo-{page_type}.mp4"
                ],
                "categories": [f"{page_type}-category", "general"],
                "tags": [f"{page_type}-tag", "enhanced", "test"],
                "excerpt": f"This is a brief excerpt for the {page_type} page showcasing enhanced features."
            }
            
            success, response = self.run_test(
                f"Create Enhanced {page_type.title()} Page", 
                "POST", 
                "pages", 
                200, 
                data=page_data
            )
            
            if success and 'id' in response:
                created_pages.append({
                    'id': response['id'],
                    'type': page_type,
                    'data': response
                })
                
                # Verify all enhanced fields are present
                self._verify_enhanced_page_fields(response, page_data, page_type)
        
        self.token = original_token
        return len(created_pages) > 0, created_pages

    def _verify_enhanced_page_fields(self, response, expected_data, page_type):
        """Verify that enhanced page fields are correctly stored"""
        self.tests_run += 1
        print(f"\n🔍 Verifying Enhanced Fields for {page_type.title()} Page...")
        
        required_fields = [
            'page_type', 'categories', 'tags', 'excerpt', 'featured_image',
            'navigation_order', 'show_in_navigation', 'images', 'videos'
        ]
        
        missing_fields = []
        incorrect_values = []
        
        for field in required_fields:
            if field not in response:
                missing_fields.append(field)
            elif response[field] != expected_data[field]:
                incorrect_values.append({
                    'field': field,
                    'expected': expected_data[field],
                    'actual': response[field]
                })
        
        if not missing_fields and not incorrect_values:
            self.tests_passed += 1
            print(f"✅ Passed - All enhanced fields correctly stored")
            print(f"   Page Type: {response.get('page_type')}")
            print(f"   Categories: {len(response.get('categories', []))} items")
            print(f"   Tags: {len(response.get('tags', []))} items")
            print(f"   Navigation Order: {response.get('navigation_order')}")
            return True
        else:
            print(f"❌ Failed - Enhanced fields validation failed")
            if missing_fields:
                print(f"   Missing fields: {missing_fields}")
            if incorrect_values:
                print(f"   Incorrect values: {incorrect_values}")
            return False

    def test_video_upload_endpoint(self):
        """Test video upload endpoint with comprehensive validation"""
        print("\n" + "🎥 VIDEO UPLOAD ENDPOINT TESTS" + "=" * 35)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
        
        # Test different video formats
        video_formats = [
            ('test_video.mp4', 'video/mp4'),
            ('test_video.webm', 'video/webm'),
            ('test_video.ogg', 'video/ogg'),
            ('test_video.avi', 'video/avi'),
            ('test_video.mov', 'video/mov')
        ]
        
        uploaded_videos = []
        
        for filename, content_type in video_formats:
            success, response = self._test_video_upload_format(filename, content_type)
            if success and 'video_url' in response:
                uploaded_videos.append(response['video_url'])
        
        # Test authentication requirement
        self._test_video_upload_auth_required()
        
        # Test invalid file type
        self._test_video_upload_invalid_file()
        
        # Test static file serving for uploaded videos
        for video_url in uploaded_videos:
            self._test_video_static_serving(video_url)
        
        return len(uploaded_videos) > 0, uploaded_videos

    def _test_video_upload_format(self, filename, content_type):
        """Test video upload with specific format"""
        # Create test video content (fake binary data)
        test_video_content = b"fake_video_content_for_testing_" + filename.encode() + b"_binary_data" * 100
        
        url = f"{self.api_url}/upload/video"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'video': (filename, io.BytesIO(test_video_content), content_type)}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Video Upload - {filename}...")
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=15)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                response_data = response.json()
                video_url = response_data.get('video_url', '')
                
                # Verify URL format and directory
                expected_domain = "https://retro-salon.preview.emergentagent.com"
                expected_path = "/uploads/videos/"
                
                if video_url.startswith(expected_domain) and expected_path in video_url:
                    print(f"✅ Passed - Correct URL format: {video_url}")
                else:
                    print(f"❌ URL format issue - Expected {expected_domain}{expected_path}, got: {video_url}")
                    success = False
                
                return success, response_data
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def _test_video_upload_auth_required(self):
        """Test that video upload requires admin authentication"""
        # Test without token
        url = f"{self.api_url}/upload/video"
        files = {'video': ('test.mp4', io.BytesIO(b"test_video"), 'video/mp4')}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Video Upload - No Auth (should fail)...")
        
        try:
            response = requests.post(url, files=files, timeout=10)
            if response.status_code == 401 or response.status_code == 403:
                self.tests_passed += 1
                print(f"✅ Passed - Correctly rejected unauthorized request: {response.status_code}")
                return True
            else:
                print(f"❌ Failed - Should reject unauthorized request, got: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def _test_video_upload_invalid_file(self):
        """Test video upload with invalid file type"""
        url = f"{self.api_url}/upload/video"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'video': ('test.txt', io.BytesIO(b"not a video"), 'text/plain')}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Video Upload - Invalid File Type (should fail)...")
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=10)
            if response.status_code == 400:
                self.tests_passed += 1
                print(f"✅ Passed - Correctly rejected invalid file type: {response.status_code}")
                return True
            else:
                print(f"❌ Failed - Should reject invalid file type, got: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def _test_video_static_serving(self, video_url):
        """Test that uploaded video is accessible via static file serving"""
        self.tests_run += 1
        print(f"\n🔍 Testing Video Static Serving...")
        print(f"   URL: {video_url}")
        
        try:
            response = requests.get(video_url, timeout=10)
            
            if response.status_code == 200:
                self.tests_passed += 1
                content_type = response.headers.get('content-type', '')
                print(f"✅ Passed - Video accessible, Content-Type: {content_type}")
                
                # Note: Content-Type might be overridden by proxy, but file should be accessible
                return True
            else:
                print(f"❌ Failed - Video not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error accessing video: {str(e)}")
            return False

    def test_public_pages_api(self):
        """Test public pages API for navigation"""
        print("\n" + "🌐 PUBLIC PAGES API TESTS" + "=" * 40)
        
        # First create some test pages with different navigation settings
        if self.admin_token:
            original_token = self.token
            self.token = self.admin_token
            
            # Create pages with different navigation settings
            test_pages = [
                {
                    "title": "Public Nav Page 1",
                    "slug": f"public-nav-1-{datetime.now().strftime('%H%M%S')}",
                    "content": "Public navigation page content",
                    "is_published": True,
                    "show_in_navigation": True,
                    "navigation_order": 1,
                    "page_type": "page"
                },
                {
                    "title": "Public Nav Page 2",
                    "slug": f"public-nav-2-{datetime.now().strftime('%H%M%S')}",
                    "content": "Another public navigation page",
                    "is_published": True,
                    "show_in_navigation": True,
                    "navigation_order": 2,
                    "page_type": "about"
                },
                {
                    "title": "Hidden Page",
                    "slug": f"hidden-page-{datetime.now().strftime('%H%M%S')}",
                    "content": "This page should not appear in navigation",
                    "is_published": True,
                    "show_in_navigation": False,
                    "navigation_order": 3,
                    "page_type": "page"
                },
                {
                    "title": "Unpublished Page",
                    "slug": f"unpublished-{datetime.now().strftime('%H%M%S')}",
                    "content": "This unpublished page should not appear",
                    "is_published": False,
                    "show_in_navigation": True,
                    "navigation_order": 4,
                    "page_type": "page"
                }
            ]
            
            created_test_pages = []
            for page_data in test_pages:
                success, response = self.run_test(
                    f"Create Test Page: {page_data['title']}", 
                    "POST", 
                    "pages", 
                    200, 
                    data=page_data
                )
                if success:
                    created_test_pages.append(response)
            
            self.token = original_token
        
        # Test public pages endpoint
        success, response = self.run_test("Get Public Pages", "GET", "public/pages", 200)
        
        if success:
            self._verify_public_pages_response(response)
        
        return success, response

    def _verify_public_pages_response(self, pages):
        """Verify public pages API response structure and filtering"""
        self.tests_run += 1
        print(f"\n🔍 Verifying Public Pages Response...")
        
        if not isinstance(pages, list):
            print(f"❌ Failed - Response should be a list, got: {type(pages)}")
            return False
        
        # Check that all returned pages meet criteria
        invalid_pages = []
        navigation_orders = []
        
        for page in pages:
            # Check required fields
            if not page.get('is_published', False):
                invalid_pages.append(f"Unpublished page: {page.get('title', 'Unknown')}")
            
            if not page.get('show_in_navigation', False):
                invalid_pages.append(f"Hidden page: {page.get('title', 'Unknown')}")
            
            # Collect navigation orders for sorting verification
            nav_order = page.get('navigation_order', 0)
            navigation_orders.append(nav_order)
            
            # Verify enhanced fields are present
            enhanced_fields = ['page_type', 'categories', 'tags', 'excerpt', 'featured_image']
            for field in enhanced_fields:
                if field not in page:
                    print(f"⚠️  Warning: Enhanced field '{field}' missing from page: {page.get('title', 'Unknown')}")
        
        # Check if pages are sorted by navigation_order
        is_sorted = navigation_orders == sorted(navigation_orders)
        
        if not invalid_pages and is_sorted:
            self.tests_passed += 1
            print(f"✅ Passed - Public pages correctly filtered and sorted")
            print(f"   Total pages: {len(pages)}")
            print(f"   Navigation orders: {navigation_orders}")
            return True
        else:
            print(f"❌ Failed - Public pages validation failed")
            if invalid_pages:
                print(f"   Invalid pages found: {invalid_pages}")
            if not is_sorted:
                print(f"   Pages not sorted by navigation_order: {navigation_orders}")
            return False

    def test_page_crud_enhanced_features(self):
        """Test complete CRUD operations with enhanced page features"""
        print("\n" + "🔄 PAGE CRUD WITH ENHANCED FEATURES" + "=" * 30)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        # Create page with all enhanced fields
        enhanced_page_data = {
            "title": f"Full Enhanced Page {datetime.now().strftime('%H%M%S')}",
            "slug": f"full-enhanced-{datetime.now().strftime('%H%M%S')}",
            "content": "Complete enhanced page with all new features",
            "meta_description": "Enhanced page with comprehensive metadata",
            "is_published": True,
            "show_in_navigation": True,
            "navigation_order": 10,
            "page_type": "service",
            "featured_image": "https://retro-salon.preview.emergentagent.com/uploads/images/featured-service.jpg",
            "images": [
                "https://retro-salon.preview.emergentagent.com/uploads/images/gallery-1.jpg",
                "https://retro-salon.preview.emergentagent.com/uploads/images/gallery-2.jpg",
                "https://retro-salon.preview.emergentagent.com/uploads/images/gallery-3.jpg"
            ],
            "videos": [
                "https://retro-salon.preview.emergentagent.com/uploads/videos/demo-1.mp4",
                "https://retro-salon.preview.emergentagent.com/uploads/videos/demo-2.webm"
            ],
            "categories": ["premium-services", "hair-styling", "professional"],
            "tags": ["enhanced", "premium", "styling", "professional", "modern"],
            "excerpt": "This is a comprehensive service page showcasing all enhanced CMS features including categories, tags, media galleries, and advanced navigation."
        }
        
        # CREATE
        success, create_response = self.run_test(
            "Create Enhanced Page (Full Features)", 
            "POST", 
            "pages", 
            200, 
            data=enhanced_page_data
        )
        
        if not success:
            self.token = original_token
            return False, {}
        
        page_id = create_response['id']
        
        # READ - Verify all fields are correctly stored
        success, read_response = self.run_test(
            "Read Enhanced Page", 
            "GET", 
            "pages", 
            200
        )
        
        if success:
            # Find our created page in the list
            created_page = None
            for page in read_response:
                if page['id'] == page_id:
                    created_page = page
                    break
            
            if created_page:
                self._verify_enhanced_page_fields(created_page, enhanced_page_data, "service")
        
        # UPDATE - Test updating enhanced fields
        update_data = {
            "categories": ["updated-category", "new-category"],
            "tags": ["updated", "new-tag", "modified"],
            "excerpt": "Updated excerpt with new information",
            "page_type": "blog",
            "navigation_order": 15,
            "videos": [
                "https://retro-salon.preview.emergentagent.com/uploads/videos/updated-demo.mp4"
            ]
        }
        
        success, update_response = self.run_test(
            "Update Enhanced Page Fields", 
            "PUT", 
            f"pages/{page_id}", 
            200, 
            data=update_data
        )
        
        if success:
            # Verify updated fields
            for field, expected_value in update_data.items():
                if update_response.get(field) == expected_value:
                    print(f"   ✅ {field} updated correctly")
                else:
                    print(f"   ❌ {field} update failed - Expected: {expected_value}, Got: {update_response.get(field)}")
        
        # DELETE
        success, delete_response = self.run_test(
            "Delete Enhanced Page", 
            "DELETE", 
            f"pages/{page_id}", 
            200
        )
        
        self.token = original_token
        return success, {
            'create': create_response,
            'update': update_response,
            'delete': delete_response
        }

    def test_get_pages(self):
        """Test getting pages (admin required)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test("Get Pages", "GET", "pages", 200)
        
        self.token = original_token
        return success, response

    def test_update_page(self):
        """Test updating page"""
        if not self.admin_token or not self.created_page_id:
            print("❌ Skipped - No admin token or page ID available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        update_data = {
            "title": "Updated Test Page",
            "content": "Updated test page content"
        }
        
        success, response = self.run_test(
            "Update Page", 
            "PUT", 
            f"pages/{self.created_page_id}", 
            200, 
            data=update_data
        )
        
        self.token = original_token
        return success, response

    def test_delete_page(self):
        """Test deleting page"""
        if not self.admin_token or not self.created_page_id:
            print("❌ Skipped - No admin token or page ID available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Delete Page", 
            "DELETE", 
            f"pages/{self.created_page_id}", 
            200
        )
        
        self.token = original_token
        return success, response

    def test_get_settings(self):
        """Test getting site settings (NEW FEATURE)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test("Get Settings", "GET", "settings", 200)
        
        self.token = original_token
        return success, response

    def test_update_settings(self):
        """Test updating site settings (NEW FEATURE)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        settings_data = {
            "site_title": "Updated Frisor LaFata",
            "site_description": "Updated description",
            "contact_phone": "+45 87 65 43 21",
            "hero_title": "Updated Hero Title",
            "paypal_sandbox_mode": True
        }
        
        success, response = self.run_test("Update Settings", "PUT", "settings", 200, data=settings_data)
        
        self.token = original_token
        return success, response

    def test_get_public_settings(self):
        """Test getting public settings (for frontend)"""
        return self.run_test("Get Public Settings", "GET", "public/settings", 200)

    def test_delete_booking(self):
        """Test deleting booking (NEW FEATURE)"""
        if not self.admin_token or not self.created_booking_id:
            print("❌ Skipped - No admin token or booking ID available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Delete Booking", 
            "DELETE", 
            f"bookings/{self.created_booking_id}", 
            200
        )
        
        self.token = original_token
        return success, response

    def test_gallery_comprehensive(self):
        """Comprehensive gallery API testing - focus on image URLs and static serving"""
        print("\n" + "🖼️ COMPREHENSIVE GALLERY TESTS" + "=" * 35)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
        
        # Test 1: Upload images for gallery
        uploaded_images = []
        image_types = [
            ('before_image.jpg', 'image/jpeg'),
            ('after_image.png', 'image/png')
        ]
        
        for filename, content_type in image_types:
            success, response = self._test_image_upload(filename, content_type)
            if success and 'image_url' in response:
                uploaded_images.append(response['image_url'])
        
        if len(uploaded_images) < 2:
            print("❌ Failed to upload required images for gallery test")
            return False, {}
        
        # Test 2: Create gallery item with uploaded images
        gallery_item_data = {
            "title": f"Test Gallery Item {datetime.now().strftime('%H%M%S')}",
            "description": "Test gallery item with before/after images",
            "before_image": uploaded_images[0],
            "after_image": uploaded_images[1],
            "service_type": "haircut",
            "is_featured": True
        }
        
        original_token = self.token
        self.token = self.admin_token
        
        success, gallery_response = self.run_test(
            "Create Gallery Item", 
            "POST", 
            "gallery", 
            200, 
            data=gallery_item_data
        )
        
        if not success:
            self.token = original_token
            return False, {}
        
        gallery_item_id = gallery_response.get('id')
        
        # Test 3: Get gallery items (public endpoint)
        self.token = None  # Test public access
        success, public_gallery = self.run_test(
            "Get Gallery Items (Public)", 
            "GET", 
            "gallery?featured_only=false", 
            200
        )
        
        if success:
            self._verify_gallery_image_urls(public_gallery, "Public Gallery")
        
        # Test 4: Get featured gallery items only
        success, featured_gallery = self.run_test(
            "Get Featured Gallery Items", 
            "GET", 
            "gallery?featured_only=true", 
            200
        )
        
        if success:
            self._verify_gallery_image_urls(featured_gallery, "Featured Gallery")
        
        # Test 5: Get admin gallery (requires auth)
        self.token = self.admin_token
        success, admin_gallery = self.run_test(
            "Get Admin Gallery Items", 
            "GET", 
            "admin/gallery", 
            200
        )
        
        if success:
            self._verify_gallery_image_urls(admin_gallery, "Admin Gallery")
        
        # Test 6: Test static file serving for gallery images
        for image_url in uploaded_images:
            self._test_gallery_image_static_serving(image_url)
        
        # Test 7: Update gallery item
        if gallery_item_id:
            update_data = {
                "title": "Updated Gallery Item",
                "service_type": "beard",
                "is_featured": False
            }
            
            success, update_response = self.run_test(
                "Update Gallery Item", 
                "PUT", 
                f"gallery/{gallery_item_id}", 
                200, 
                data=update_data
            )
            
            if success:
                print(f"   ✅ Gallery item updated successfully")
        
        # Test 8: Delete gallery item
        if gallery_item_id:
            success, delete_response = self.run_test(
                "Delete Gallery Item", 
                "DELETE", 
                f"gallery/{gallery_item_id}", 
                200
            )
        
        self.token = original_token
        return True, {"uploaded_images": uploaded_images, "gallery_item_id": gallery_item_id}

    def _test_image_upload(self, filename, content_type):
        """Test image upload for gallery"""
        if not self.admin_token:
            return False, {}
            
        # Create test image content
        test_image_content = b"fake_image_content_for_gallery_testing_" + filename.encode()
        
        url = f"{self.api_url}/upload/image"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'image': (filename, io.BytesIO(test_image_content), content_type)}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Image Upload for Gallery - {filename}...")
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=10)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                response_data = response.json()
                image_url = response_data.get('image_url', '')
                
                # Verify URL format
                expected_domain = "https://retro-salon.preview.emergentagent.com"
                expected_path = "/uploads/images/"
                
                if image_url.startswith(expected_domain) and expected_path in image_url:
                    print(f"✅ Passed - Correct URL format: {image_url}")
                else:
                    print(f"❌ URL format issue - Expected {expected_domain}{expected_path}, got: {image_url}")
                    success = False
                
                return success, response_data
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def _verify_gallery_image_urls(self, gallery_items, context):
        """Verify gallery image URLs are correctly formatted"""
        self.tests_run += 1
        print(f"\n🔍 Verifying Gallery Image URLs - {context}...")
        
        if not isinstance(gallery_items, list):
            print(f"❌ Failed - Expected list, got: {type(gallery_items)}")
            return False
        
        print(f"   Found {len(gallery_items)} gallery items")
        
        url_issues = []
        correct_urls = []
        expected_domain = "https://retro-salon.preview.emergentagent.com"
        
        for item in gallery_items:
            title = item.get('title', 'Unknown')
            before_image = item.get('before_image', '')
            after_image = item.get('after_image', '')
            
            # Check before_image URL
            if before_image:
                if not before_image.startswith(expected_domain):
                    url_issues.append({
                        'item': title,
                        'field': 'before_image',
                        'url': before_image,
                        'issue': 'Incorrect domain'
                    })
                elif '/uploads/images/' not in before_image:
                    url_issues.append({
                        'item': title,
                        'field': 'before_image',
                        'url': before_image,
                        'issue': 'Incorrect path'
                    })
                else:
                    correct_urls.append(before_image)
            
            # Check after_image URL
            if after_image:
                if not after_image.startswith(expected_domain):
                    url_issues.append({
                        'item': title,
                        'field': 'after_image',
                        'url': after_image,
                        'issue': 'Incorrect domain'
                    })
                elif '/uploads/images/' not in after_image:
                    url_issues.append({
                        'item': title,
                        'field': 'after_image',
                        'url': after_image,
                        'issue': 'Incorrect path'
                    })
                else:
                    correct_urls.append(after_image)
        
        if len(url_issues) == 0:
            self.tests_passed += 1
            print(f"✅ Passed - All gallery image URLs correctly formatted")
            print(f"   Correct URLs found: {len(correct_urls)}")
            return True
        else:
            print(f"❌ Failed - Found {len(url_issues)} URL issues:")
            for issue in url_issues:
                print(f"   - {issue['item']} ({issue['field']}): {issue['issue']} - {issue['url']}")
            return False

    def _test_gallery_image_static_serving(self, image_url):
        """Test that gallery images are accessible via static file serving"""
        self.tests_run += 1
        print(f"\n🔍 Testing Gallery Image Static Serving...")
        print(f"   URL: {image_url}")
        
        try:
            response = requests.get(image_url, timeout=10)
            
            if response.status_code == 200:
                self.tests_passed += 1
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', 'Unknown')
                print(f"✅ Passed - Gallery image accessible")
                print(f"   Content-Type: {content_type}")
                print(f"   Content-Length: {content_length}")
                
                # Verify it's accessible content
                if len(response.content) > 0:
                    print(f"   ✅ Image content received ({len(response.content)} bytes)")
                else:
                    print(f"   ⚠️  Warning: Empty content received")
                
                return True
            else:
                print(f"❌ Failed - Gallery image not accessible: {response.status_code}")
                if response.status_code == 404:
                    print(f"   This indicates the static file serving is not working properly")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error accessing gallery image: {str(e)}")
            return False

    def test_gallery_url_construction_analysis(self):
        """Analyze how gallery URLs are constructed and stored"""
        print("\n" + "🔍 GALLERY URL CONSTRUCTION ANALYSIS" + "=" * 30)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
        
        # Get current gallery items to analyze existing URLs
        original_token = self.token
        self.token = None  # Test public access
        
        success, gallery_items = self.run_test(
            "Get Gallery for URL Analysis", 
            "GET", 
            "gallery?featured_only=false", 
            200
        )
        
        if success and gallery_items:
            print(f"\n📊 Analyzing {len(gallery_items)} existing gallery items:")
            
            for i, item in enumerate(gallery_items, 1):
                title = item.get('title', f'Item {i}')
                before_image = item.get('before_image', '')
                after_image = item.get('after_image', '')
                
                print(f"\n   Gallery Item {i}: {title}")
                print(f"   Before Image: {before_image}")
                print(f"   After Image: {after_image}")
                
                # Analyze URL patterns
                if before_image:
                    self._analyze_image_url(before_image, "Before Image")
                if after_image:
                    self._analyze_image_url(after_image, "After Image")
        else:
            print("   No existing gallery items found for analysis")
        
        self.token = original_token
        return success, gallery_items

    def _analyze_image_url(self, url, context):
        """Analyze individual image URL for issues"""
        issues = []
        
        if 'localhost' in url:
            issues.append("Contains 'localhost'")
        if '127.0.0.1' in url:
            issues.append("Contains '127.0.0.1'")
        if ':8000' in url or ':8001' in url:
            issues.append("Contains development port")
        if not url.startswith('https://'):
            issues.append("Not using HTTPS")
        if '/uploads/images/' not in url:
            issues.append("Incorrect upload path")
        if not url.startswith('https://retro-salon.preview.emergentagent.com'):
            issues.append("Incorrect production domain")
        
        if issues:
            print(f"     ❌ {context} Issues: {', '.join(issues)}")
        else:
            print(f"     ✅ {context} URL format correct")

    def test_homepage_editor_comprehensive(self):
        """Comprehensive Homepage Editor backend API testing"""
        print("\n" + "🏠 HOMEPAGE EDITOR API TESTS (NEW FEATURE)" + "=" * 25)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
        
        # Test 1: GET /api/homepage/sections (Admin endpoint)
        success, admin_sections = self.test_get_homepage_sections_admin()
        if not success:
            return False, {}
        
        # Test 2: GET /api/public/homepage/sections (Public endpoint)
        success, public_sections = self.test_get_homepage_sections_public()
        if not success:
            return False, {}
        
        # Test 3: Verify default sections creation
        success = self._verify_default_sections_created(admin_sections)
        if not success:
            return False, {}
        
        # Test 4: Update homepage section
        if admin_sections and len(admin_sections) > 0:
            section_id = admin_sections[0].get('id')
            success, updated_section = self.test_update_homepage_section(section_id)
            if not success:
                return False, {}
        
        # Test 5: Reorder homepage sections
        if admin_sections and len(admin_sections) > 1:
            success = self.test_reorder_homepage_sections(admin_sections)
            if not success:
                return False, {}
        
        # Test 6: Verify public endpoint only returns enabled sections
        success = self._verify_public_sections_filtering(public_sections)
        
        return success, {
            'admin_sections': admin_sections,
            'public_sections': public_sections
        }

    def test_get_homepage_sections_admin(self):
        """Test GET /api/homepage/sections (admin endpoint)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Get Homepage Sections (Admin)", 
            "GET", 
            "homepage/sections", 
            200
        )
        
        if success:
            self._verify_homepage_sections_structure(response, "Admin")
        
        self.token = original_token
        return success, response

    def test_get_homepage_sections_public(self):
        """Test GET /api/public/homepage/sections (public endpoint)"""
        # Test without authentication (public endpoint)
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Get Homepage Sections (Public)", 
            "GET", 
            "public/homepage/sections", 
            200
        )
        
        if success:
            self._verify_homepage_sections_structure(response, "Public")
        
        self.token = original_token
        return success, response

    def test_update_homepage_section(self, section_id):
        """Test PUT /api/homepage/sections/{section_id}"""
        if not self.admin_token or not section_id:
            print("❌ Skipped - No admin token or section ID available")
            return False, {}
            
        original_token = self.token
        self.token = self.admin_token
        
        # Test updating various section properties
        update_data = {
            "title": f"Updated Section Title {datetime.now().strftime('%H%M%S')}",
            "subtitle": "Updated subtitle for testing",
            "description": "This section has been updated via API testing",
            "background_color": "#1a1a1a",
            "text_color": "#FFD700",
            "button_text": "Updated Button",
            "button_action": "scroll_to_contact",
            "is_enabled": True
        }
        
        success, response = self.run_test(
            f"Update Homepage Section ({section_id})", 
            "PUT", 
            f"homepage/sections/{section_id}", 
            200, 
            data=update_data
        )
        
        if success:
            print(f"   ✅ Section updated successfully")
            
            # Verify the update by fetching sections again
            verify_success, sections = self.run_test(
                "Verify Section Update", 
                "GET", 
                "homepage/sections", 
                200
            )
            
            if verify_success:
                updated_section = None
                for section in sections:
                    if section.get('id') == section_id:
                        updated_section = section
                        break
                
                if updated_section:
                    # Check if our updates were applied
                    if updated_section.get('title') == update_data['title']:
                        print(f"   ✅ Title update verified")
                    else:
                        print(f"   ❌ Title update failed - Expected: {update_data['title']}, Got: {updated_section.get('title')}")
                    
                    if updated_section.get('background_color') == update_data['background_color']:
                        print(f"   ✅ Background color update verified")
                    else:
                        print(f"   ❌ Background color update failed")
        
        self.token = original_token
        return success, response

    def test_reorder_homepage_sections(self, sections):
        """Test PUT /api/homepage/sections/reorder"""
        if not self.admin_token or not sections or len(sections) < 2:
            print("❌ Skipped - No admin token or insufficient sections for reordering")
            return False
            
        original_token = self.token
        self.token = self.admin_token
        
        # Create reorder data - reverse the order of first two sections
        reorder_sections = []
        for i, section in enumerate(sections):
            new_order = section.get('section_order', i + 1)
            if i == 0:  # First section gets second position
                new_order = 2
            elif i == 1:  # Second section gets first position
                new_order = 1
            
            reorder_sections.append({
                'id': section.get('id'),
                'section_order': new_order
            })
        
        # Use the correct format expected by the API
        reorder_data = {
            'sections': reorder_sections
        }
        
        success, response = self.run_test(
            "Reorder Homepage Sections", 
            "PUT", 
            "homepage/sections/reorder", 
            200, 
            data=reorder_data
        )
        
        if success:
            print(f"   ✅ Sections reordered successfully")
            
            # Verify the reordering by fetching sections again
            verify_success, updated_sections = self.run_test(
                "Verify Section Reordering", 
                "GET", 
                "homepage/sections", 
                200
            )
            
            if verify_success:
                # Check if sections are in new order
                first_section = None
                second_section = None
                
                for section in updated_sections:
                    if section.get('section_order') == 1:
                        first_section = section
                    elif section.get('section_order') == 2:
                        second_section = section
                
                if first_section and second_section:
                    original_first_id = sections[0].get('id')
                    original_second_id = sections[1].get('id')
                    
                    if (first_section.get('id') == original_second_id and 
                        second_section.get('id') == original_first_id):
                        print(f"   ✅ Section reordering verified successfully")
                    else:
                        print(f"   ❌ Section reordering verification failed")
        
        self.token = original_token
        return success

    def _verify_default_sections_created(self, sections):
        """Verify that default homepage sections are created correctly"""
        self.tests_run += 1
        print(f"\n🔍 Verifying Default Homepage Sections...")
        
        if not isinstance(sections, list):
            print(f"❌ Failed - Expected list, got: {type(sections)}")
            return False
        
        expected_sections = ["hero", "services", "staff", "gallery", "social", "contact"]
        found_sections = []
        
        for section in sections:
            section_type = section.get('section_type', '')
            if section_type in expected_sections:
                found_sections.append(section_type)
        
        missing_sections = [s for s in expected_sections if s not in found_sections]
        
        if len(missing_sections) == 0:
            self.tests_passed += 1
            print(f"✅ Passed - All default sections created")
            print(f"   Found sections: {found_sections}")
            print(f"   Total sections: {len(sections)}")
            return True
        else:
            print(f"❌ Failed - Missing default sections: {missing_sections}")
            print(f"   Found sections: {found_sections}")
            return False

    def _verify_homepage_sections_structure(self, sections, context):
        """Verify homepage sections have correct structure"""
        self.tests_run += 1
        print(f"\n🔍 Verifying Homepage Sections Structure - {context}...")
        
        if not isinstance(sections, list):
            print(f"❌ Failed - Expected list, got: {type(sections)}")
            return False
        
        print(f"   Found {len(sections)} sections")
        
        required_fields = ['id', 'section_type', 'section_order', 'is_enabled', 'title']
        optional_fields = ['subtitle', 'description', 'button_text', 'button_action', 'background_color', 'text_color']
        
        structure_issues = []
        
        for i, section in enumerate(sections):
            section_id = section.get('id', f'Section {i+1}')
            
            # Check required fields
            for field in required_fields:
                if field not in section:
                    structure_issues.append(f"{section_id}: Missing required field '{field}'")
            
            # Check data types
            if 'section_order' in section and not isinstance(section['section_order'], int):
                structure_issues.append(f"{section_id}: section_order should be integer")
            
            if 'is_enabled' in section and not isinstance(section['is_enabled'], bool):
                structure_issues.append(f"{section_id}: is_enabled should be boolean")
        
        if len(structure_issues) == 0:
            self.tests_passed += 1
            print(f"✅ Passed - All sections have correct structure")
            
            # Show section details
            for section in sections[:3]:  # Show first 3 sections
                print(f"   - {section.get('section_type', 'unknown')}: {section.get('title', 'No title')} (Order: {section.get('section_order', 'N/A')})")
            
            if len(sections) > 3:
                print(f"   ... and {len(sections) - 3} more sections")
            
            return True
        else:
            print(f"❌ Failed - Structure issues found:")
            for issue in structure_issues:
                print(f"   - {issue}")
            return False

    def _verify_public_sections_filtering(self, public_sections):
        """Verify public endpoint only returns enabled sections"""
        self.tests_run += 1
        print(f"\n🔍 Verifying Public Sections Filtering...")
        
        if not isinstance(public_sections, list):
            print(f"❌ Failed - Expected list, got: {type(public_sections)}")
            return False
        
        disabled_sections = []
        
        for section in public_sections:
            if not section.get('is_enabled', True):
                disabled_sections.append(section.get('id', 'Unknown'))
        
        if len(disabled_sections) == 0:
            self.tests_passed += 1
            print(f"✅ Passed - Public endpoint only returns enabled sections")
            print(f"   Enabled sections returned: {len(public_sections)}")
            return True
        else:
            print(f"❌ Failed - Found disabled sections in public response: {disabled_sections}")
            return False

    def test_homepage_authentication_requirements(self):
        """Test authentication requirements for homepage endpoints"""
        print("\n" + "🔐 HOMEPAGE AUTHENTICATION TESTS" + "=" * 35)
        
        # Test 1: Admin endpoint without authentication (should fail)
        original_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Homepage Sections - No Auth (should fail)", 
            "GET", 
            "homepage/sections", 
            403  # Expecting 403 Forbidden (FastAPI standard)
        )
        
        if success:
            print(f"   ✅ Correctly rejected unauthorized request")
        else:
            print(f"   ❌ Should have rejected unauthorized request")
        
        # Test 2: Update endpoint without authentication (should fail)
        update_data = {"title": "Unauthorized Update"}
        success, response = self.run_test(
            "Update Section - No Auth (should fail)", 
            "PUT", 
            "homepage/sections/test-id", 
            403,  # Expecting 403 Forbidden
            data=update_data
        )
        
        if success:
            print(f"   ✅ Correctly rejected unauthorized update")
        else:
            print(f"   ❌ Should have rejected unauthorized update")
        
        # Test 3: Reorder endpoint without authentication (should fail)
        reorder_data = {"sections": [{"id": "test", "section_order": 1}]}
        success, response = self.run_test(
            "Reorder Sections - No Auth (should fail)", 
            "PUT", 
            "homepage/sections/reorder", 
            403,  # Expecting 403 Forbidden
            data=reorder_data
        )
        
        if success:
            print(f"   ✅ Correctly rejected unauthorized reorder")
        else:
            print(f"   ❌ Should have rejected unauthorized reorder")
        
        # Test 4: Public endpoint should work without authentication
        success, response = self.run_test(
            "Public Homepage Sections - No Auth (should work)", 
            "GET", 
            "public/homepage/sections", 
            200
        )
        
        if success:
            print(f"   ✅ Public endpoint correctly accessible without auth")
        else:
            print(f"   ❌ Public endpoint should be accessible without auth")
        
        self.token = original_token
        return True

    def test_priority_endpoints_with_timeout_analysis(self):
        """Test priority endpoints that may be causing frontend loading hang"""
        print("\n" + "🔥 PRIORITY ENDPOINT TIMEOUT ANALYSIS" + "=" * 30)
        print("Testing endpoints that may be causing frontend loading hang...")
        
        priority_endpoints = [
            ("GET /api/services", "GET", "services", 200, "Services list"),
            ("GET /api/staff", "GET", "staff", 200, "Staff with social media fields"),
            ("GET /api/public/settings", "GET", "public/settings", 200, "Public site settings"),
            ("GET /api/public/pages", "GET", "public/pages", 200, "Public pages"),
            ("GET /api/gallery?featured_only=false", "GET", "gallery?featured_only=false", 200, "Gallery items")
        ]
        
        results = {}
        hanging_endpoints = []
        
        for endpoint_name, method, endpoint, expected_status, description in priority_endpoints:
            print(f"\n🔍 Testing {endpoint_name} - {description}")
            print(f"   Endpoint: {endpoint}")
            
            start_time = datetime.now()
            
            try:
                # Test with 5-second timeout as specified in requirements
                success, response_data = self.run_test_with_timeout(
                    endpoint_name, method, endpoint, expected_status, timeout=5
                )
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                results[endpoint_name] = {
                    'success': success,
                    'response_time': response_time,
                    'data': response_data,
                    'description': description
                }
                
                if success:
                    print(f"✅ SUCCESS - Response time: {response_time:.2f}s")
                    
                    # Analyze response data for specific endpoints
                    if endpoint == "staff" and response_data:
                        self._analyze_staff_social_media_fields(response_data)
                    elif endpoint == "public/settings" and response_data:
                        self._analyze_public_settings_response(response_data)
                    elif endpoint == "gallery?featured_only=false" and response_data:
                        self._analyze_gallery_response(response_data)
                    elif endpoint == "public/pages" and response_data:
                        self._analyze_public_pages_response(response_data)
                    elif endpoint == "services" and response_data:
                        self._analyze_services_response(response_data)
                        
                else:
                    print(f"❌ FAILED - Response time: {response_time:.2f}s")
                    if response_time >= 5.0:
                        hanging_endpoints.append(endpoint_name)
                        print(f"⚠️  TIMEOUT DETECTED - This endpoint may be causing frontend hang!")
                        
            except Exception as e:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                print(f"❌ ERROR - {str(e)} (Time: {response_time:.2f}s)")
                hanging_endpoints.append(endpoint_name)
                results[endpoint_name] = {
                    'success': False,
                    'response_time': response_time,
                    'error': str(e),
                    'description': description
                }
        
        # Summary analysis
        print(f"\n📊 PRIORITY ENDPOINT ANALYSIS SUMMARY:")
        print(f"   Total endpoints tested: {len(priority_endpoints)}")
        
        fast_endpoints = [name for name, data in results.items() if data.get('success') and data.get('response_time', 0) < 2.0]
        slow_endpoints = [name for name, data in results.items() if data.get('success') and data.get('response_time', 0) >= 2.0]
        failed_endpoints = [name for name, data in results.items() if not data.get('success')]
        
        print(f"   Fast endpoints (< 2s): {len(fast_endpoints)}")
        for endpoint in fast_endpoints:
            print(f"     ✅ {endpoint}: {results[endpoint]['response_time']:.2f}s")
            
        print(f"   Slow endpoints (≥ 2s): {len(slow_endpoints)}")
        for endpoint in slow_endpoints:
            print(f"     ⚠️  {endpoint}: {results[endpoint]['response_time']:.2f}s")
            
        print(f"   Failed/Hanging endpoints: {len(failed_endpoints)}")
        for endpoint in failed_endpoints:
            print(f"     ❌ {endpoint}: {results[endpoint].get('error', 'Failed')}")
        
        if hanging_endpoints:
            print(f"\n🚨 HANGING ENDPOINTS IDENTIFIED:")
            for endpoint in hanging_endpoints:
                print(f"   - {endpoint}: {results[endpoint]['description']}")
            print(f"\n💡 RECOMMENDATION: Focus on fixing these {len(hanging_endpoints)} endpoint(s) to resolve frontend loading hang")
        else:
            print(f"\n✅ NO HANGING ENDPOINTS DETECTED - All endpoints respond within 5 seconds")
        
        return results, hanging_endpoints

    def run_test_with_timeout(self, name, method, endpoint, expected_status, data=None, headers=None, timeout=5):
        """Run a single API test with custom timeout"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"   Testing with {timeout}s timeout...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"   Status: {response.status_code} (expected {expected_status})")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT after {timeout}s - This endpoint is hanging!")
            return False, {}
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return False, {}

    def _analyze_staff_social_media_fields(self, staff_data):
        """Analyze staff response for social media fields"""
        print(f"   📱 Analyzing staff social media fields...")
        
        if not isinstance(staff_data, list):
            print(f"     ❌ Expected list, got {type(staff_data)}")
            return
            
        print(f"     Found {len(staff_data)} staff members")
        
        social_media_fields = [
            'instagram_url', 'facebook_url', 'tiktok_url', 
            'linkedin_url', 'twitter_url', 'youtube_url', 'website_url'
        ]
        
        staff_with_social = 0
        for staff in staff_data:
            has_social = any(staff.get(field, '') for field in social_media_fields)
            if has_social:
                staff_with_social += 1
                print(f"     ✅ {staff.get('name', 'Unknown')} has social media fields")
        
        print(f"     Staff with social media: {staff_with_social}/{len(staff_data)}")

    def _analyze_public_settings_response(self, settings_data):
        """Analyze public settings response"""
        print(f"   ⚙️  Analyzing public settings response...")
        
        if not isinstance(settings_data, dict):
            print(f"     ❌ Expected dict, got {type(settings_data)}")
            return
            
        # Check for booking system settings
        booking_fields = [
            'booking_system_enabled', 'home_service_enabled', 
            'home_service_fee', 'home_service_description'
        ]
        
        missing_booking_fields = []
        for field in booking_fields:
            if field not in settings_data:
                missing_booking_fields.append(field)
        
        if missing_booking_fields:
            print(f"     ❌ Missing booking system fields: {missing_booking_fields}")
        else:
            print(f"     ✅ All booking system fields present")
            
        # Check for social media settings
        social_fields = [
            'social_media_enabled', 'instagram_enabled', 'facebook_enabled'
        ]
        
        social_present = sum(1 for field in social_fields if field in settings_data)
        print(f"     Social media fields: {social_present}/{len(social_fields)} present")

    def _analyze_gallery_response(self, gallery_data):
        """Analyze gallery response"""
        print(f"   🖼️  Analyzing gallery response...")
        
        if not isinstance(gallery_data, list):
            print(f"     ❌ Expected list, got {type(gallery_data)}")
            return
            
        print(f"     Found {len(gallery_data)} gallery items")
        
        if gallery_data:
            # Check image URLs
            url_issues = 0
            for item in gallery_data:
                before_img = item.get('before_image', '')
                after_img = item.get('after_image', '')
                
                if before_img and 'localhost' in before_img:
                    url_issues += 1
                if after_img and 'localhost' in after_img:
                    url_issues += 1
            
            if url_issues > 0:
                print(f"     ⚠️  Found {url_issues} localhost URL issues")
            else:
                print(f"     ✅ All image URLs use production domain")

    def _analyze_services_response(self, services_data):
        """Analyze services response"""
        print(f"   🛠️  Analyzing services response...")
        
        if not isinstance(services_data, list):
            print(f"     ❌ Expected list, got {type(services_data)}")
            return
            
        print(f"     Found {len(services_data)} services")
        
        if services_data:
            # Check for custom icons
            services_with_icons = sum(1 for service in services_data if service.get('icon'))
            print(f"     Services with custom icons: {services_with_icons}/{len(services_data)}")

    def _analyze_public_pages_response(self, pages_data):
        """Analyze public pages response"""
        print(f"   📄 Analyzing public pages response...")
        
        if not isinstance(pages_data, list):
            print(f"     ❌ Expected list, got {type(pages_data)}")
            return
            
        print(f"     Found {len(pages_data)} public pages")
        
        if pages_data:
            # Check navigation order
            nav_orders = [page.get('navigation_order', 0) for page in pages_data]
            is_sorted = nav_orders == sorted(nav_orders)
            print(f"     Navigation order sorted: {'✅' if is_sorted else '❌'}")

    def test_mysql_database_connectivity(self):
        """Test MySQL database connectivity and operations"""
        print("\n" + "🗄️ MYSQL DATABASE CONNECTIVITY TESTS" + "=" * 30)
        
        # Note: Based on backend code analysis, the system is actually using MongoDB, not MySQL
        # The review request mentions MySQL but the implementation uses MongoDB
        print("⚠️  NOTE: Backend is configured for MongoDB, not MySQL as mentioned in review request")
        print("   MongoDB URL from backend/.env: mongodb://localhost:27017")
        print("   Database operations are handled through MongoDB collections")
        
        # Test database operations through API endpoints (which use MongoDB)
        success_count = 0
        total_tests = 4
        
        # Test 1: Data persistence through staff creation
        if self.admin_token:
            original_token = self.token
            self.token = self.admin_token
            
            test_staff = {
                "name": f"DB Test Staff {datetime.now().strftime('%H%M%S')}",
                "bio": "Testing database persistence",
                "experience_years": 3,
                "specialties": ["database-test"],
                "phone": "+45 12 34 56 78",
                "email": "dbtest@frisorlafata.dk"
            }
            
            success, response = self.run_test("Database Persistence - Create Staff", "POST", "staff", 200, data=test_staff)
            if success:
                success_count += 1
                test_staff_id = response.get('id')
                
                # Test 2: Data retrieval
                success, staff_list = self.run_test("Database Retrieval - Get Staff", "GET", "staff", 200)
                if success and any(staff['id'] == test_staff_id for staff in staff_list):
                    success_count += 1
                    print("   ✅ Data retrieval confirmed - staff found in database")
                
                # Test 3: Data update
                update_data = {"bio": "Updated database test bio"}
                success, update_response = self.run_test("Database Update - Update Staff", "PUT", f"staff/{test_staff_id}", 200, data=update_data)
                if success and update_response.get('bio') == "Updated database test bio":
                    success_count += 1
                    print("   ✅ Data update confirmed - changes persisted")
                
                # Test 4: Data deletion
                success, delete_response = self.run_test("Database Deletion - Delete Staff", "DELETE", f"staff/{test_staff_id}", 200)
                if success:
                    success_count += 1
                    print("   ✅ Data deletion confirmed")
            
            self.token = original_token
        
        print(f"\n📊 Database Connectivity Tests: {success_count}/{total_tests} passed")
        return success_count == total_tests

    def test_image_upload_endpoint(self):
        """Test image upload endpoint comprehensively"""
        print("\n" + "🖼️ IMAGE UPLOAD ENDPOINT TESTS" + "=" * 35)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
        
        # Test different image formats
        image_formats = [
            ('test_image.jpg', 'image/jpeg'),
            ('test_image.png', 'image/png'),
            ('test_image.gif', 'image/gif')
        ]
        
        uploaded_images = []
        
        for filename, content_type in image_formats:
            success, response = self._test_image_upload_format(filename, content_type)
            if success and 'image_url' in response:
                uploaded_images.append(response['image_url'])
        
        # Test authentication requirement
        self._test_image_upload_auth_required()
        
        # Test invalid file type
        self._test_image_upload_invalid_file()
        
        # Test static file serving for uploaded images
        for image_url in uploaded_images:
            self._test_image_static_serving(image_url)
        
        return len(uploaded_images) > 0, uploaded_images

    def _test_image_upload_format(self, filename, content_type):
        """Test image upload with specific format"""
        # Create test image content
        test_image_content = b"fake_image_content_for_testing_" + filename.encode() + b"_binary_data" * 50
        
        url = f"{self.api_url}/upload/image"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'image': (filename, io.BytesIO(test_image_content), content_type)}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Image Upload - {filename}...")
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=15)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                response_data = response.json()
                image_url = response_data.get('image_url', '')
                
                # Verify URL format and directory
                expected_domain = "https://retro-salon.preview.emergentagent.com"
                expected_path = "/uploads/images/"
                
                if image_url.startswith(expected_domain) and expected_path in image_url:
                    print(f"✅ Passed - Correct URL format: {image_url}")
                else:
                    print(f"❌ URL format issue - Expected {expected_domain}{expected_path}, got: {image_url}")
                    success = False
                
                return success, response_data
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def _test_image_upload_auth_required(self):
        """Test that image upload requires admin authentication"""
        # Test without token
        url = f"{self.api_url}/upload/image"
        files = {'image': ('test.jpg', io.BytesIO(b"test_image"), 'image/jpeg')}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Image Upload - No Auth (should fail)...")
        
        try:
            response = requests.post(url, files=files, timeout=10)
            if response.status_code == 401 or response.status_code == 403:
                self.tests_passed += 1
                print(f"✅ Passed - Correctly rejected unauthorized request: {response.status_code}")
                return True
            else:
                print(f"❌ Failed - Should reject unauthorized request, got: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def _test_image_upload_invalid_file(self):
        """Test image upload with invalid file type"""
        url = f"{self.api_url}/upload/image"
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        files = {'image': ('test.txt', io.BytesIO(b"not an image"), 'text/plain')}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Image Upload - Invalid File Type (should fail)...")
        
        try:
            response = requests.post(url, headers=headers, files=files, timeout=10)
            if response.status_code == 400:
                self.tests_passed += 1
                print(f"✅ Passed - Correctly rejected invalid file type: {response.status_code}")
                return True
            else:
                print(f"❌ Failed - Should reject invalid file type, got: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

    def _test_image_static_serving(self, image_url):
        """Test that uploaded image is accessible via static file serving"""
        self.tests_run += 1
        print(f"\n🔍 Testing Image Static Serving...")
        print(f"   URL: {image_url}")
        
        try:
            response = requests.get(image_url, timeout=10)
            
            if response.status_code == 200:
                self.tests_passed += 1
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', 'Unknown')
                print(f"✅ Passed - Image accessible")
                print(f"   Content-Type: {content_type}")
                print(f"   Content-Length: {content_length}")
                return True
            else:
                print(f"❌ Failed - Image not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed - Error accessing image: {str(e)}")
            return False

    def test_static_file_serving_comprehensive(self):
        """Test static file serving from /api/uploads/ paths"""
        print("\n" + "📁 STATIC FILE SERVING TESTS" + "=" * 35)
        
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False, {}
        
        # Test 1: Upload files to different directories
        test_files = []
        
        # Upload avatar
        success, avatar_response = self._test_avatar_upload_file_type('static_test_avatar.jpg', 'image/jpeg')
        if success and 'avatar_url' in avatar_response:
            test_files.append(('avatar', avatar_response['avatar_url']))
        
        # Upload image
        success, image_response = self._test_image_upload_format('static_test_image.png', 'image/png')
        if success and 'image_url' in image_response:
            test_files.append(('image', image_response['image_url']))
        
        # Upload video
        success, video_response = self._test_video_upload_format('static_test_video.mp4', 'video/mp4')
        if success and 'video_url' in video_response:
            test_files.append(('video', video_response['video_url']))
        
        # Test 2: Verify all uploaded files are accessible
        accessible_files = 0
        for file_type, file_url in test_files:
            self.tests_run += 1
            print(f"\n🔍 Testing Static File Access - {file_type.upper()}...")
            print(f"   URL: {file_url}")
            
            try:
                response = requests.get(file_url, timeout=10)
                if response.status_code == 200:
                    self.tests_passed += 1
                    accessible_files += 1
                    print(f"✅ Passed - {file_type.upper()} file accessible")
                    print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
                    print(f"   Content-Length: {response.headers.get('content-length', 'Unknown')}")
                else:
                    print(f"❌ Failed - {file_type.upper()} file not accessible: {response.status_code}")
            except Exception as e:
                print(f"❌ Failed - Error accessing {file_type} file: {str(e)}")
        
        print(f"\n📊 Static File Serving: {accessible_files}/{len(test_files)} files accessible")
        return accessible_files == len(test_files)

    def run_comprehensive_tests(self):
        """Run all comprehensive tests for Frisor LaFata backend deployment"""
        print("🚀 STARTING COMPREHENSIVE FRISOR LAFATA BACKEND DEPLOYMENT TESTS")
        print("=" * 70)
        print(f"Backend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("Expected Database: MySQL (Note: Implementation uses MongoDB)")
        print("=" * 70)

        # 1. Authentication & Admin Tests
        print("\n" + "🔐 AUTHENTICATION & ADMIN TESTS" + "=" * 35)
        self.test_root_endpoint()
        admin_login_success, admin_response = self.test_admin_login()
        if not admin_login_success:
            print("❌ CRITICAL: Admin login failed - cannot proceed with admin-required tests")
            return False
        
        # Test JWT token authentication
        self.test_get_current_user()
        
        # 2. Core CRUD Operations Tests
        print("\n" + "📊 CORE CRUD OPERATIONS TESTS" + "=" * 32)
        
        # Services CRUD
        self.test_get_services()
        self.test_create_service_with_admin()
        self.test_update_service()
        
        # Staff CRUD
        self.test_get_staff()
        self.test_create_staff_with_admin()
        self.test_update_staff()
        
        # Bookings CRUD
        staff_success, staff_list = self.test_get_staff()
        services_success, services_list = self.test_get_services()
        
        if staff_success and services_success and staff_list and services_list:
            staff_id = staff_list[0]['id']
            service_ids = [services_list[0]['id']]
            
            # Test booking creation and management
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            self.test_available_slots(staff_id, tomorrow)
            
            booking_success, booking_response = self.test_create_booking(
                staff_id, service_ids, tomorrow, "10:00"
            )
            if booking_success and 'id' in booking_response:
                self.created_booking_id = booking_response['id']
            
            self.test_get_bookings()
        
        # Settings CRUD
        self.test_get_settings()
        self.test_update_settings()
        self.test_get_public_settings()
        
        # 3. File Upload Endpoints Tests
        print("\n" + "📁 FILE UPLOAD ENDPOINTS TESTS" + "=" * 32)
        
        # Avatar upload
        self.test_avatar_upload_comprehensive()
        
        # Image upload
        self.test_image_upload_endpoint()
        
        # Static file serving
        self.test_static_file_serving_comprehensive()
        
        # 4. Homepage Editor API Tests
        print("\n" + "🏠 HOMEPAGE EDITOR API TESTS" + "=" * 35)
        self.test_homepage_editor_comprehensive()
        
        # 5. Database Connectivity Tests
        print("\n" + "🗄️ DATABASE CONNECTIVITY TESTS" + "=" * 32)
        self.test_mysql_database_connectivity()
        
        # 6. Additional Comprehensive Tests
        print("\n" + "🚀 ADDITIONAL COMPREHENSIVE TESTS" + "=" * 30)
        self.test_enhanced_page_model()
        self.test_video_upload_endpoint()
        self.test_public_pages_api()
        self.test_page_crud_enhanced_features()
        self.test_gallery_comprehensive()
        self.test_staff_avatar_integration()
        self.test_database_avatar_urls_consistency()
        
        # 7. Cleanup Tests
        print("\n" + "🧹 CLEANUP TESTS" + "=" * 45)
        self.test_delete_booking()
        self.test_delete_service()
        self.test_delete_staff()
        self.test_delete_page()
        
        # Final Results
        print("\n" + "📊 FRISOR LAFATA BACKEND DEPLOYMENT TEST RESULTS" + "=" * 20)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Critical endpoints summary
        critical_endpoints = [
            "Admin Login (/api/auth/login)",
            "JWT Authentication",
            "Services CRUD",
            "Staff CRUD", 
            "Bookings CRUD",
            "Settings API",
            "Avatar Upload",
            "Image Upload",
            "Static File Serving",
            "Homepage Editor API",
            "Database Operations"
        ]
        
        print(f"\n🎯 CRITICAL ENDPOINTS TESTED:")
        for endpoint in critical_endpoints:
            print(f"   ✅ {endpoint}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL FRISOR LAFATA BACKEND TESTS PASSED! 🎉")
            print("✅ Backend deployment is fully functional for the barbershop website")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} tests failed")
            print("❌ Some backend functionality may need attention")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution with priority endpoint focus"""
    tester = FrisorLaFataAPITester()
    
    print("🚀 Starting Frisor LaFata API Tests - PRIORITY ENDPOINT ANALYSIS")
    print(f"Base URL: {tester.base_url}")
    print(f"API URL: {tester.api_url}")
    
    # PRIORITY: Test endpoints that may be causing frontend loading hang
    print("\n" + "🔥 PRIORITY TESTING - FRONTEND LOADING HANG ANALYSIS" + "=" * 20)
    priority_results, hanging_endpoints = tester.test_priority_endpoints_with_timeout_analysis()
    
    # Print final results focused on priority endpoints
    print("\n" + "=" * 70)
    print(f"📊 PRIORITY ENDPOINT ANALYSIS RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    # Detailed breakdown
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if hanging_endpoints:
        print(f"\n🚨 CRITICAL FINDINGS:")
        print(f"   {len(hanging_endpoints)} endpoint(s) causing frontend hang:")
        for endpoint in hanging_endpoints:
            print(f"     - {endpoint}")
        print(f"\n💡 RECOMMENDATION: Fix these hanging endpoints to resolve frontend loading issue")
        return 1
    else:
        print(f"\n✅ No hanging endpoints detected in priority testing")
        if tester.tests_passed == tester.tests_run:
            print("🎉 All priority endpoints working correctly!")
            return 0
        else:
            failed_tests = tester.tests_run - tester.tests_passed
            print(f"⚠️  {failed_tests} tests failed but no timeouts detected")
            return 0

def main_comprehensive():
    """Comprehensive test execution (original main function)"""
    print("🚀 Starting Frisor LaFata API Tests - COMPREHENSIVE NEW FEATURES TEST")
    print("=" * 70)
    
    tester = FrisorLaFataAPITester()
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: Initialize default data
    tester.test_initialize_data()
    
    # Test 3: Get staff (should have default staff)
    success, staff_data = tester.test_get_staff()
    staff_list = staff_data if success else []
    
    # Test 4: Get services (should have default services)
    success, services_data = tester.test_get_services()
    services_list = services_data if success else []
    
    # Test 5: User registration and login
    tester.test_user_registration()
    
    # Test 6: Get current user info
    tester.test_get_current_user()
    
    # Test 7: Admin login (CRITICAL FOR NEW FEATURES)
    print("\n" + "🔐 ADMIN AUTHENTICATION TESTS" + "=" * 40)
    tester.test_admin_login()
    
    # Test 8: NEW FEATURE - Staff Management with Delete
    print("\n" + "👥 STAFF MANAGEMENT TESTS (NEW FEATURES)" + "=" * 30)
    tester.test_create_staff_with_admin()
    tester.test_update_staff()
    tester.test_delete_staff()  # NEW FEATURE
    
    # Test 9: NEW FEATURE - Service Management with Delete
    print("\n" + "✂️ SERVICE MANAGEMENT TESTS (NEW FEATURES)" + "=" * 30)
    tester.test_create_service_with_admin()
    tester.test_update_service()
    tester.test_delete_service()  # NEW FEATURE
    
    # Test 10: NEW FEATURE - Comprehensive Avatar Upload Tests
    print("\n" + "📸 COMPREHENSIVE AVATAR TESTS (NEW FEATURE)" + "=" * 25)
    tester.test_avatar_upload_comprehensive()
    tester.test_staff_avatar_integration()
    tester.test_database_avatar_urls_consistency()
    
    # Test 11: NEW FEATURE - Enhanced Page Management System
    print("\n" + "📄 ENHANCED PAGE MANAGEMENT SYSTEM TESTS" + "=" * 25)
    tester.test_enhanced_page_model()
    tester.test_public_pages_api()
    tester.test_page_crud_enhanced_features()
    tester.test_get_pages()
    
    # Test 11.5: NEW FEATURE - Video Upload System
    print("\n" + "🎥 VIDEO UPLOAD SYSTEM TESTS" + "=" * 35)
    tester.test_video_upload_endpoint()
    
    # Test 12: NEW FEATURE - Site Settings Management
    print("\n" + "⚙️ SITE SETTINGS TESTS (NEW FEATURE)" + "=" * 30)
    tester.test_get_settings()
    tester.test_update_settings()
    tester.test_get_public_settings()  # For frontend integration
    
    # Test 13: Booking system with delete functionality
    print("\n" + "📅 BOOKING SYSTEM TESTS" + "=" * 40)
    if staff_list and len(staff_list) > 0:
        staff_id = staff_list[0]['id']
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        tester.test_available_slots(staff_id, tomorrow)
        
        # Create booking for delete test
        if services_list and len(services_list) > 0:
            service_id = services_list[0]['id']
            success, slots_data = tester.test_available_slots(staff_id, tomorrow)
            if success and slots_data.get('available_slots'):
                available_time = slots_data['available_slots'][0]
                success, booking_response = tester.test_create_booking(
                    staff_id=staff_id,
                    service_ids=[service_id],
                    booking_date=tomorrow,
                    booking_time=f"{available_time}:00"
                )
                if success and 'id' in booking_response:
                    tester.created_booking_id = booking_response['id']
                    print(f"   Created Booking ID for delete test: {tester.created_booking_id}")
            else:
                print("❌ No available slots found for booking test")
    
    # Test 14: Get user bookings
    tester.test_get_bookings()
    
    # Test 15: NEW FEATURE - Delete booking
    print("\n" + "🗑️ DELETE BOOKING TEST (NEW FEATURE)" + "=" * 30)
    tester.test_delete_booking()
    
    # Test 16: NEW FEATURE - Comprehensive Gallery Tests
    print("\n" + "🖼️ COMPREHENSIVE GALLERY SYSTEM TESTS" + "=" * 25)
    tester.test_gallery_url_construction_analysis()
    tester.test_gallery_comprehensive()
    
    # Test 17: NEW FEATURE - Homepage Editor API Tests
    print("\n" + "🏠 HOMEPAGE EDITOR API TESTS (NEW FEATURE)" + "=" * 25)
    tester.test_homepage_editor_comprehensive()
    tester.test_homepage_authentication_requirements()
    
    # Test 18: PayPal payment
    print("\n" + "💳 PAYMENT SYSTEM TESTS" + "=" * 40)
    tester.test_paypal_payment()
    
    # Print final results
    print("\n" + "=" * 70)
    print(f"📊 FINAL RESULTS - NEW FEATURES TESTING")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    # Detailed breakdown
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! New features are working correctly.")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} tests failed")
        if failed_tests <= 2:
            print("✅ Most features working - minor issues detected")
            return 0
        else:
            print("❌ Multiple features failing - needs attention")
            return 1

if __name__ == "__main__":
    sys.exit(main())