import unittest
import requests

class AuthTestCase(unittest.TestCase):
    BASE_URL = 'http://localhost:5000'  # Update this with your application's base URL
    LOGIN_ENDPOINT = '/login'
    RATE_LIMIT = 5  # Set this to your rate limit value

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
