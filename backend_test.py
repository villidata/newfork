import requests
import sys
import json
from datetime import datetime, date, timedelta

class FrisorLaFataAPITester:
    def __init__(self, base_url="https://trim-time-49.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

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
        endpoint = f"bookings/available-slots?staff_id={staff_id}&date={test_date}"
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
            tester.test_create_booking(
                staff_id=staff_id,
                service_ids=[service_id],
                booking_date=tomorrow,
                booking_time="10:00:00"
            )
    
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