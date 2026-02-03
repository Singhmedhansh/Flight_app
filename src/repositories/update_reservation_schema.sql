-- SQL Migration Script to update FlightReservation table schema
-- Run this script in your MySQL database

USE flight;

-- Step 1: Check current structure
DESCRIBE FlightReservation;

-- Step 2: Add missing columns if they don't exist
-- Add flight_id column (if using flight_no, rename it)
ALTER TABLE FlightReservation 
CHANGE COLUMN flight_no flight_id INT;

-- Add seat_number column
ALTER TABLE FlightReservation 
ADD COLUMN IF NOT EXISTS seat_number VARCHAR(5) DEFAULT NULL;

-- Add booking_reference column
ALTER TABLE FlightReservation 
ADD COLUMN IF NOT EXISTS booking_reference VARCHAR(10) DEFAULT NULL;

-- Add price column (use existing payment_amount or add new)
ALTER TABLE FlightReservation 
ADD COLUMN IF NOT EXISTS price DECIMAL(10, 2) DEFAULT NULL;

-- Update price from payment_amount if it exists
UPDATE FlightReservation 
SET price = payment_amount 
WHERE price IS NULL AND payment_amount IS NOT NULL;

-- Step 3: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_booking_reference ON FlightReservation(booking_reference);
CREATE INDEX IF NOT EXISTS idx_user_id ON FlightReservation(user_id);
CREATE INDEX IF NOT EXISTS idx_flight_id ON FlightReservation(flight_id);

-- Step 4: Verify the updated structure
DESCRIBE FlightReservation;

-- Step 5: Check data
SELECT * FROM FlightReservation LIMIT 5;
