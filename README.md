# Project Title: LoveJoy

## Description
LoveJoy is a Flask web application designed for the evaluation and management of antiques. It offers features like user authentication, antique evaluation submissions, admin management, and more.

## Features
- User Registration and Login
- Email Verification and Password Reset
- Admin Dashboard for User and Antique Management
- Antique Evaluation Submission
- Image Upload and Validation
- Two-Factor Authentication
- Rate Limiting and CSRF Protection
- Captcha Implementation for Registration

## Installation
To set up the LoveJoy application, follow these steps:

1. **Clone the Repository**
   ```sh
  

   git clone [repository URL]
   cd [repository directory]
   ```

2. **Set Up a Virtual Environment (Optional)**
   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Set up the necessary environment variables:
   - `GMAIL_USERNAME`: Your Gmail username for mailing services.
   - `GMAIL_PASSWORD`: Your Gmail password.
   - `FERNET_KEY`: A key for cryptographic operations.

5. **Initialize the Database**
   ```sh
   flask init-db
   ```

## Usage
To run the Love

Joy application:

1. **Start the Application**
   ```sh
   flask run
   ```

2. **Access the Application**
   Open your web browser and navigate to `http://127.0.0.1:5000/` to view the application.

## Administration
To perform administrative tasks:

- Use the Flask CLI commands to promote or remove admin rights:
  ```sh
  flask promote-admin [email]
  flask remove-admin [email]
  ```

- Access the admin dashboard at `http://127.0.0.1:5000/admin/` after logging in as an admin.

## Contributing
Contributions to LoveJoy are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Open a Pull Request.

## License
Include details about the project's license here.

## Contact
For support or queries, contact ramzi.daher@gmail.com.

---

