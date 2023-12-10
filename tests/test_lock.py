import unittest
import requests
import time
from bs4 import BeautifulSoup

class AuthTestCase(unittest.TestCase):
    BASE_URL = 'http://localhost:5000'
    LOGIN_ENDPOINT = '/login'
    RATE_LIMIT = 5  
    DELAY = 1  # One second delay between requests

    def get_csrf_token(self, response_text):
        soup = BeautifulSoup(response_text, 'html.parser')
        token = soup.find('input', {'name': 'csrf_token'})['value']
        return token

    def test_login_rate_limit(self):
        session = requests.Session()  
        login_page_response = session.get(self.BASE_URL + self.LOGIN_ENDPOINT)
        csrf_token = self.get_csrf_token(login_page_response.text)

        url = self.BASE_URL + self.LOGIN_ENDPOINT
        for i in range(self.RATE_LIMIT + 1):  # Attempt to reach the limit
            response = session.post(url, data={
                'username': 'ramzi.j.daher@gmail.com',
                'password': 'testpass',
                'csrf_token': csrf_token
            })
            if i < self.RATE_LIMIT - 1:
                self.assertNotEqual(response.status_code, 429, f"Rate limit hit too early at attempt {i+1}")
            else:
                self.assertEqual(response.status_code, 429, f"Rate limit not enforced at attempt {i+1}")
            time.sleep(self.DELAY)

if __name__ == '__main__':
    unittest.main()
