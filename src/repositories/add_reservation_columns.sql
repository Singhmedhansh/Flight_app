-- SQL Migration Script to add seat_number and booking_reference columns
-- Run this script in your MySQL database to update the FlightReservation table

USE flight;

-- Add seat_number column
ALTER TABLE FlightReservation 
ADD COLUMN seat_number VARCHAR(5) DEFAULT NULL 
AFTER flight_id;

-- Add booking_reference column
ALTER TABLE FlightReservation 
ADD COLUMN booking_reference VARCHAR(10) DEFAULT NULL 
AFTER seat_number;

-- Add index for faster lookups
CREATE INDEX idx_booking_reference ON FlightReservation(booking_reference);

-- Verify the changes
DESCRIBE FlightReservation;

-- Optional: Update existing reservations with mock data
UPDATE FlightReservation 
SET seat_number = CONCAT(FLOOR(1 + RAND() * 30), SUBSTRING('ABCDEF', FLOOR(1 + RAND() * 6), 1)),
    booking_reference = CONCAT(
        SUBSTRING('ABCDEFGHIJKLMNOPQRSTUVWXYZ', FLOOR(1 + RAND() * 26), 1),
        SUBSTRING('ABCDEFGHIJKLMNOPQRSTUVWXYZ', FLOOR(1 + RAND() * 26), 1),
        FLOOR(RAND() * 10),
        FLOOR(RAND() * 10),
        FLOOR(RAND() * 10),
        FLOOR(RAND() * 10)
    )
WHERE seat_number IS NULL OR booking_reference IS NULL;

SELECT * FROM FlightReservation LIMIT 5;
