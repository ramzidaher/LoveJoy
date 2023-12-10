import unittest
import requests

class AuthTestCase(unittest.TestCase):
    BASE_URL = 'http://localhost:5000'
    SIGNUP_ENDPOINT = '/register'

    def test_user_registration(self):
        url = self.BASE_URL + self.SIGNUP_ENDPOINT
        user_data = {
            'email': 'newuser@example.com',
            'password': 'Password123',
            'name': 'New User',
            'contact': '1234567890'
        }
        response = requests.post(url, data=user_data)
        
        self.assertEqual(response.status_code, 200)  

if __name__ == '__main__':
    unittest.main()
