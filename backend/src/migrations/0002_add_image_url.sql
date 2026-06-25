-- 0002_add_image_url.sql
-- Add image_url column to questions table for question-related images
-- (road signs, diagrams, traffic situation photos)

ALTER TABLE questions ADD COLUMN image_url VARCHAR(500);
