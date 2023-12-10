import unittest
import requests

class AuthTestCase(unittest.TestCase):
    BASE_URL = 'http://localhost:5000'  
    LOGIN_ENDPOINT = '/login'
    RATE_LIMIT = 5  

    def test_login_rate_limit(self):
        url = self.BASE_URL + self.LOGIN_ENDPOINT
        for i in range(self.RATE_LIMIT + 2):  # Exceed the limit
            response = requests.post(url, data={'username': 'testuser', 'password': 'testpass'})
            if i < self.RATE_LIMIT:
                self.assertNotEqual(response.status_code, 429, "Rate limit hit too early")
            else:
                self.assertEqual(response.status_code, 429, "Rate limit not enforced")

if __name__ == '__main__':
    unittest.main()
