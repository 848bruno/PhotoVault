PhotoVault - Professional Photo Delivery Platform
https://img.shields.io/badge/PhotoVault-Professional_Photo_Delivery-green
https://img.shields.io/badge/Django-4.2+-green
https://img.shields.io/badge/Python-3.9+-blue
https://img.shields.io/badge/Bootstrap-5.3-purple

PhotoVault is a modern, full-stack photo delivery and e-commerce platform designed for professional photographers to securely sell and deliver photos to clients. The platform enables photographers to manage their business, process payments, and deliver both digital and physical prints through an intuitive interface.

✨ Features
👥 Authentication System
Admin Login: Secure authentication for photographers/business owners

Client Registration & Login: Self-service account creation for end-clients

Role-based Access Control: Different permissions for admins vs. clients

Secure Session Management: JWT-based sessions with proper security

📊 Admin Dashboard
Photo Upload Interface: Bulk upload with drag-and-drop support

Client Assignment: Assign photos to specific client accounts

Order Management: Process digital downloads and physical print orders

Client Management: View and manage all client accounts

Sales Analytics: Comprehensive revenue and performance metrics

Payment Status Tracking: Monitor transaction statuses

🛍️ Customer Portal
Personalized Gallery: Browse assigned photos in organized gallery view

Digital Purchase: Buy digital copies with instant download access

Print Ordering: Select sizes, quantities, and framing options

Order History: Complete purchase history with download links

Order Tracking: Real-time status updates for physical prints

Shopping Cart: Multi-item cart with save-for-later functionality

💳 Payment System
Stripe Integration: Secure payment processing

Digital Delivery: Automatic download links upon successful payment

Print Order Processing: Integration with print labs/shipping services

Receipt Generation: Automated email receipts and invoices

Refund Management: Handle refunds and disputes

🏗️ Technical Architecture
Backend Stack
Framework: Django 4.2+

Database: PostgreSQL

Authentication: Custom User Model with JWT

File Storage: AWS S3 / Local Storage

Caching: Redis

Task Queue: Celery

Frontend Stack
HTML5, CSS3, JavaScript

Bootstrap 5.3 for responsive design

Font Awesome icons

Chart.js for analytics

Modern CSS with CSS Variables

Database Schema
sql
User (AbstractBaseUser)          # Extended user model
Profile                          # User-specific information (customer/photographer)
Photo                            # Photo metadata and file info
Order                            # Main order table
OrderItem                        # Individual items within orders
Payment                          # Payment transaction records
🚀 Quick Start
Prerequisites
Python 3.9+

PostgreSQL 14+

Redis (for caching)

Virtual Environment

Installation
Clone the repository

bash
git clone https://github.com/yourusername/photovault.git
cd photovault
Create and activate virtual environment

bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
Install dependencies

bash
pip install -r requirements.txt
Configure environment variables

bash
cp .env.example .env
# Edit .env with your configuration
Apply database migrations

bash
python manage.py makemigrations
python manage.py migrate
Create superuser

bash
python manage.py createsuperuser
Run development server

bash
python manage.py runserver
Access the application

Open browser to: http://localhost:8000

Admin panel: http://localhost:8000/admin

📁 Project Structure
text
photovault/
├── photovault/           # Main Django project
│   ├── settings.py       # Project settings
│   ├── urls.py          # URL configuration
│   └── wsgi.py          # WSGI configuration
├── accounts/             # Authentication app
│   ├── models.py        # Custom User & Profile models
│   ├── views.py         # Auth views
│   ├── forms.py         # Registration forms
│   └── urls.py          # Auth URLs
├── gallery/              # Photo management app
│   ├── models.py        # Photo model
│   ├── views.py         # Gallery views
│   └── urls.py          # Gallery URLs
├── orders/               # Order processing app
├── payments/             # Payment integration app
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── home.html        # Home page
│   ├── register.html    # Registration page
│   ├── login.html       # Login page
│   └── admin_dashboard.html  # Admin dashboard
├── static/               # Static files
├── media/                # Uploaded media files
├── requirements.txt      # Python dependencies
└── README.md            # This file
🔧 Configuration
Environment Variables
Create a .env file in the project root:

env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=photovault
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# Email Settings (for production)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe (for payment processing)
STRIPE_PUBLIC_KEY=pk_test_xxxxxxxxxxxxxx
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxx

# AWS S3 (for file storage - optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
Database Setup
Install PostgreSQL

Create database

sql
CREATE DATABASE photovault;
CREATE USER photovault_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE photovault TO photovault_user;
👤 User Roles
Photographer/Admin
Upload and manage photos

Assign photos to clients

Set pricing for digital and print copies

View sales analytics

Manage client accounts

Process orders

Customer/Client
Register for an account

View assigned photos

Purchase digital copies

Order physical prints

Track order status

View purchase history

📱 Pages & Templates
Static Pages
Home Page (/) - Marketing landing page

About Us - Company information

Services - Platform features

Contact - Contact form and information

Authentication Pages
Login (/login/) - User authentication

Register (/register/) - New account creation

Profile (/profile/) - User profile management

Client Portal
Client Dashboard - Assigned photos gallery

Shopping Cart - Cart management

Order History - Purchase records

Order Tracking - Status updates

Admin Portal
Admin Dashboard - Analytics and overview

Photo Management - Upload and assign photos

Client Management - User administration

Order Management - Process orders

🎨 Design System
Color Palette
css
--pv-deep-green: #1b5e20;     /* Deep Green */
--pv-medium-green: #2e7d32;   /* Medium Green */
--pv-light-green: #4caf50;    /* Light Green */
--pv-very-light-green: #c8e6c9; /* Very Light Green */
Theme Support
Light Mode: White backgrounds with dark text

Dark Mode: Dark backgrounds with light text

Smooth transitions between themes

Responsive Design
Mobile: < 768px

Tablet: 768px - 992px

Desktop: > 992px

🔐 Security Features
Authentication Security
Password hashing with bcrypt

Session timeout management

CSRF protection

Rate limiting on login attempts

HTTPS enforcement

Data Security
Database encryption for sensitive data

Secure file upload validation

SQL injection prevention

XSS protection

File permission management

Payment Security
PCI DSS compliance through Stripe

Never store raw payment information

Webhook signature verification

Fraud detection integration

🧪 Testing
Test Types
bash
# Run unit tests
python manage.py test accounts.tests

# Run integration tests
python manage.py test gallery.tests

# Run all tests
python manage.py test

# Test coverage
coverage run manage.py test
coverage report
Testing Tools
Django Test Framework

pytest for Python tests

Selenium for browser automation

Locust for load testing

Coverage.py for code coverage

📈 API Endpoints
Authentication
POST /api/auth/register/ - Client registration

POST /api/auth/login/ - User login

POST /api/auth/logout/ - User logout

GET /api/auth/profile/ - Profile management

Gallery
GET /api/photos/ - List photos (with filters)

POST /api/photos/upload/ - Admin upload

PUT /api/photos/assign/ - Assign photos to clients

GET /api/photos/{id}/ - Photo details

Orders
POST /api/orders/create/ - Create new order

GET /api/orders/ - List user orders

GET /api/orders/{id}/ - Order details

PUT /api/orders/{id}/status/ - Update order status

Payments
POST /api/payments/create-intent/ - Create payment intent

POST /api/payments/confirm/ - Confirm payment

GET /api/payments/history/ - Payment history

🚢 Deployment
Production Checklist
Environment setup

Python 3.9+

PostgreSQL 14+

Redis 6+

Nginx/Apache

Configuration

Environment variables

Database migrations

Static files collection

Media storage setup

Security

SSL certificate

Firewall configuration

Regular backups

Monitoring setup

Maintenance

Regular updates

Log rotation

Performance monitoring

Backup verification

Docker Deployment
dockerfile
# Dockerfile
FROM python:3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "photovault.wsgi:application", "--bind", "0.0.0.0:8000"]
📊 Development Roadmap
Phase 1: Core Infrastructure (Complete)
✅ Django project setup

✅ User authentication system

✅ Basic models and admin

✅ Home page design

Phase 2: Client Portal (In Progress)
✅ Gallery interface

✅ Shopping cart

✅ Basic checkout

✅ Order history

Phase 3: Admin Dashboard (In Progress)
✅ Analytics dashboard

✅ Client management

✅ Photo upload system

⏳ Order processing

Phase 4: Advanced Features (Planned)
⏳ Payment integration

⏳ Email notifications

⏳ Print order processing

⏳ Advanced analytics

Phase 5: Testing & Deployment (Planned)
⏳ Comprehensive testing

⏳ Performance optimization

⏳ Security audit

⏳ Production deployment

🤝 Contributing
Fork the repository

Create a feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

Development Guidelines
Follow PEP 8 style guide

Write tests for new features

Update documentation

Use meaningful commit messages

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

👏 Acknowledgments
Django - The web framework used

Bootstrap - Frontend framework

Font Awesome - Icons

Stripe - Payment processing

📞 Support
For support, email ambalebruno@gmail.com or create an issue in the GitHub repository.

PhotoVault - Making professional photo delivery simple and secure. 📸✨