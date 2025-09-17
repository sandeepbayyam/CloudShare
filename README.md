# CloudShare
A Django application for managing and sharing datasets, connecting sources and destinations, and handling secure data transfers seamlessly across multiple cloud platforms

# 🌐 CloudShare – Destination Management API

A **Django REST Framework (DRF)** project for managing **destinations across multiple cloud providers**.  
This API validates **cloud, product, region, and authentication methods** specific to each provider.  

📌 Repo: [CloudShare](https://github.com/sandeepbayyam/CloudShare.git)

---

## 🚀 Features

- CRUD APIs for **Destinations**
- Cloud & product-specific **validation rules**
- Multiple **auth methods** per product
- Supports **pagination, filtering, and ordering**
- Partial updates with **PATCH**
- Error handling with clear validation messages
- Ready-to-use with **Docker** or **local environment**

---

## ⚙️ Local Setup

### Step-by-step (manual)
```bash
# 1. Clone repo
git clone https://github.com/sandeepbayyam/CloudShare.git
cd CloudShare

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py migrate

# 5. Run server
python manage.py runserver
