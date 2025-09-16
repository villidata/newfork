import requests
import sys
import json
from datetime import datetime, date, timedelta
import io

class FrisorLaFataAPITester:
    def __init__(self, base_url="https://trim-time-49.preview.emergentagent.com"):
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

def main():
    print("🚀 Starting Frisor LaFata API Tests")
    print("=" * 50)
    
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
    
    # Test 7: Available slots (if we have staff)
    if staff_list and len(staff_list) > 0:
        staff_id = staff_list[0]['id']
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        tester.test_available_slots(staff_id, tomorrow)
        
        # Test 8: Create booking (if we have services)
        if services_list and len(services_list) > 0:
            service_id = services_list[0]['id']
            # Get available slots first
            success, slots_data = tester.test_available_slots(staff_id, tomorrow)
            if success and slots_data.get('available_slots'):
                available_time = slots_data['available_slots'][0]  # Use first available slot
                tester.test_create_booking(
                    staff_id=staff_id,
                    service_ids=[service_id],
                    booking_date=tomorrow,
                    booking_time=f"{available_time}:00"
                )
            else:
                print("❌ No available slots found for booking test")
    
    # Test 9: Get user bookings
    tester.test_get_bookings()
    
    # Test 10: PayPal payment
    tester.test_paypal_payment()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())