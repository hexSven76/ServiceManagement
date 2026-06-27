# ServiceManagement — Service Booking and Management System

A Streamlit + SQLAlchemy demo project for managing service providers, customer bookings, mock payments, reviews, notifications, dashboards, and PDF reports.

## Features

- Role-based login/register: Admin, Provider, Customer
- Customer flow: browse services, inspect details, book free slots, cancel before deadline, mock pay, download receipt PDF, submit reviews
- Provider flow: create/edit/toggle/delete services, upload service images, create duration-matched schedule slots, approve/reject/cancel bookings, view dashboard/reviews, export PDF
- Admin flow: dashboard KPIs/charts, user management, provider/customer tabs, service management, booking control, review inspection, PDF exports
- Notifications panel with unread count, mark-one-read, mark-all-read, and manual refresh
- Seeded demo data and demo credentials

## Libraries

- Streamlit
- SQLAlchemy
- ReportLab
- Pandas
- Plotly-ready dependency
- Pytest-ready dependency

## Folder structure

```text
ServiceManagement/
  app/
    db.py, models.py, seed.py, security.py
    services/
    utils/pdf_utils.py
  frontend/
    *_ui.py, *_helpers.py, navigation.py
  data/
    service_booking.db
  reports/
  assets/uploads/services/
  main.py
  streamlit_app.py
  requirements.txt
```

## Windows setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
streamlit run streamlit_app.py
```

## Demo credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Provider | `provider` | `provider123` |
| Customer | `customer` | `customer123` |

## Notes and limitations

- Payment is a mock/simulated flow; no real gateway is connected.
- Notifications are simulated with database rows and manual refresh, not WebSockets.
- PDF reports are generated with ReportLab into the `reports/` directory.
- The app uses SQLite for a simple classroom/demo setup.
