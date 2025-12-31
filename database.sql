-- 1. CLEANUP (Drop old tables if they exist to start fresh)
DROP TABLE IF EXISTS reminder CASCADE;
DROP TABLE IF EXISTS "order" CASCADE; -- "order" must be quoted
DROP TABLE IF EXISTS measurement CASCADE;
DROP TABLE IF EXISTS customer CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;  -- "user" must be quoted
DROP TABLE IF EXISTS shop_profile CASCADE;

-- 2. CREATE TABLES

-- Shop Profile
CREATE TABLE shop_profile (
    id SERIAL PRIMARY KEY,
    shop_name VARCHAR(100) DEFAULT 'My Tailor Shop',
    address TEXT,
    mobile VARCHAR(20),
    gst_no VARCHAR(20),
    terms TEXT,
    upi_id VARCHAR(50),
    logo VARCHAR(200)
);

-- User (Admin/Staff)
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    role VARCHAR(20) DEFAULT 'staff',
    permissions VARCHAR(255) DEFAULT '',
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES "user"(id)
);

-- Category (Shirt, Pant, etc.)
CREATE TABLE category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    is_custom BOOLEAN DEFAULT FALSE,
    fields_json JSON -- PostgreSQL supports native JSON
);

-- Customer
CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(20) UNIQUE NOT NULL,
    alt_mobile VARCHAR(20),
    email VARCHAR(120),
    address TEXT,
    city VARCHAR(100),
    area VARCHAR(100),
    whatsapp BOOLEAN DEFAULT FALSE,
    gender VARCHAR(10),
    photo VARCHAR(200),
    notes TEXT,
    style_pref VARCHAR(200),
    birthday DATE,
    created_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_visit TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Measurement
CREATE TABLE measurement (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    measurements_json JSON NOT NULL,
    remarks TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (customer_id) REFERENCES customer(id),
    FOREIGN KEY (category_id) REFERENCES category(id)
);

-- Order
CREATE TABLE "order" (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    items JSON NOT NULL,
    start_date DATE,
    delivery_date DATE,
    work_status VARCHAR(20) DEFAULT 'Pending',
    payment_status VARCHAR(20) DEFAULT 'Pending',
    total_amt FLOAT DEFAULT 0.0,
    advance FLOAT DEFAULT 0.0,
    balance FLOAT DEFAULT 0.0,
    payment_mode VARCHAR(50),
    trial_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(id)
);

-- Reminder
CREATE TABLE reminder (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_id INTEGER,
    type VARCHAR(50),
    due_date DATE,
    due_time TIME,
    message VARCHAR(255),
    status VARCHAR(20) DEFAULT 'Pending',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer(id),
    FOREIGN KEY (order_id) REFERENCES "order"(id)
);