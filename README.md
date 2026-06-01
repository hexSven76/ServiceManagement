# Service & Booking System

A role-based service booking platform developed with Python and SQLAlchemy.

The system supports three user roles:

* Admin
* Service Provider
* Customer

Customers can browse services, reserve available time slots, pay for bookings, and leave reviews. Providers can manage their services and schedules. Admins have full control over the platform and access to reports and dashboards.

---

# Features

## Authentication & Authorization

* User registration
* User login
* Role-based permissions
* Account activation status

## Service Management

Providers can:

* Create services
* Update services
* Delete services
* Set service categories
* Configure service duration and pricing

## Schedule Management

Providers can:

* Create available time slots
* Edit time slots
* Delete time slots
* Activate or deactivate slots

Validation rules:

* End time must be after start time
* Slot duration must exactly match the service duration
* Overlapping slots are not allowed

## Booking Management

Customers can:

* Book available slots
* View their bookings
* Cancel bookings before the cancellation deadline

Providers can:

* Confirm bookings
* Reject bookings

Admins can:

* Force approve bookings
* Force cancel bookings

## Payment System

* One payment per booking
* Prevents duplicate payments
* Tracks payment status
* Stores payment references

## Reviews

Customers can:

* Leave reviews for completed services
* Rate services
* Submit comments

## Notifications

The system supports notifications for:

* Booking creation
* Booking confirmation
* Booking rejection
* Booking cancellation
* Successful payments
* System messages

## Dashboard & Reporting

Admin features include:

* Booking statistics
* Revenue reports
* User activity information
* System-wide monitoring

---

# Technology Stack

Backend:

* Python 3
* SQLAlchemy ORM

Testing:

* Pytest

Database:

* SQLite (development/testing)

---

# Database Model Overview

## User

Stores account information.

Fields:

* username
* email
* password_hash
* role
* is_active

Relationships:

* One Profile
* Many Services
* Many Bookings
* Many Notifications
* Many Reviews

---

## Profile

Stores optional user information.

Fields:

* full_name
* phone
* bio
* image_path

---

## Service

Created by providers.

Fields:

* title
* description
* category
* duration_minutes
* price
* status

---

## TimeSlot

Represents an available booking time.

Fields:

* service_id
* start_time
* end_time
* status

---

## Booking

Represents a reservation.

Fields:

* customer_id
* provider_id
* service_id
* slot_id
* status
* payment_status
* confirmed_at
* rejected_at
* canceled_at
* cancel_deadline

Booking statuses:

* PENDING
* CONFIRMED
* REJECTED
* CANCELED

Payment statuses:

* PAID
* UNPAID

---

## Payment

Stores payment information.

Fields:

* booking_id
* amount
* payment_reference
* status
* paid_at

---

## Review

Stores customer feedback.

Fields:

* booking_id
* customer_id
* provider_id
* service_id
* rating
* comment

---

## Notification

Stores system notifications.

Fields:

* user_id
* type
* title
* message
* is_read

---

# Business Workflow

## Booking Flow

Customer
→ Create Booking
→ PENDING

Provider
→ Confirm Booking
→ CONFIRMED

Customer
→ Pay
→ PAID

Customer
→ Submit Review

Alternative outcomes:

PENDING
→ REJECTED

PENDING / CONFIRMED
→ CANCELED

---

# Role Permissions

## Customer

Can:

* Register
* Login
* Browse services
* Create bookings
* Cancel own bookings
* Pay for bookings
* Leave reviews
* View own bookings

Cannot:

* Create services
* Manage schedules
* Confirm bookings

---

## Provider

Can:

* Create services
* Update services
* Delete services
* Manage schedules
* Confirm bookings
* Reject bookings
* View bookings for own services

Cannot:

* Pay for bookings
* Review own services

---

## Admin

Can:

* Manage all users
* Manage all services
* Manage all bookings
* Force approve bookings
* Force cancel bookings
* Access reports and dashboards

---

# Running Tests

Run all tests:

python -m pytest -vv

Run a specific test file:

python -m pytest tests/test_auth.py -vv
