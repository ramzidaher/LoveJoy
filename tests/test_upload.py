# import io
# import pytest
# from flask.testing import FlaskClient
# from main import create_app 

# @pytest.fixture
# def client():
#     app = create_app()  # Create your Flask app
#     app.config['TESTING'] = True  # Set the app to testing mode
#     client = app.test_client()  # Create the test client
#     yield client  # Provide the client to the tests

# def test_allowed_file_upload(client, app):
#     # Simulate a valid file upload
#     data = {
#         'antique_name': 'Test Antique',
#         'antique_description': 'Description',
#         'antique_request': 'Request',
#         'antique_est_age': '100',
#         'preferred_contact_method': 'email',
#         'antique_image': (io.BytesIO(b'my file contents'), 'test.jpg')
#     }
#     response = client.post('/evaluation', data=data, content_type='multipart/form-data')
#     assert response.status_code == 200  # Or appropriate success code

# def test_disallowed_file_extension(client, app):
#     # Simulate an upload with a disallowed file extension
#     data = {
#         'antique_image': (io.BytesIO(b'my file contents'), 'test.exe')
#     }
#     response = client.post('/evaluation', data=data, content_type='multipart/form-data')
#     assert 'Invalid file type' in response.data.decode('utf-8')

# def test_file_size_exceeded(client, app):
#     # Simulate an upload with a file size larger than the allowed limit
#     large_file = io.BytesIO(b'a' * (app.config['MAX_FILE_SIZE'] + 1))
#     data = {
#         'antique_image': (large_file, 'test.png')
#     }
#     response = client.post('/evaluation', data=data, content_type='multipart/form-data')
#     assert 'File size exceeds limit' in response.data.decode('utf-8')
