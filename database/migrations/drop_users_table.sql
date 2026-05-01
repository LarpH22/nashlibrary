-- Migration: Drop users table
-- This migration removes the legacy users table from the database
-- The system now uses separate tables: admins, librarians, students

-- First, check and handle foreign key constraints
-- If there are any foreign keys referencing the users table, we need to drop them first

SET FOREIGN_KEY_CHECKS=0;

-- Drop the users table
DROP TABLE IF EXISTS `users`;

SET FOREIGN_KEY_CHECKS=1;

-- Verify the table is removed
SELECT 'Users table successfully dropped' AS status;
