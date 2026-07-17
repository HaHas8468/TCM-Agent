ALTER TABLE api_doctor ADD COLUMN username VARCHAR(150) NOT NULL UNIQUE AFTER doctor_id;
ALTER TABLE api_doctor ADD COLUMN password VARCHAR(128) NOT NULL AFTER username;
ALTER TABLE api_doctor ADD INDEX idx_doctor_username (username);

ALTER TABLE api_patient ADD COLUMN username VARCHAR(150) NOT NULL UNIQUE AFTER patient_id;
ALTER TABLE api_patient ADD COLUMN password VARCHAR(128) NOT NULL AFTER username;
ALTER TABLE api_patient ADD INDEX idx_patient_username (username);

ALTER TABLE api_doctor DROP COLUMN user_id;
ALTER TABLE api_patient DROP COLUMN user_id;

UPDATE api_doctor SET username='doctor.lin', password='Prototype123' WHERE doctor_id='D001';
UPDATE api_doctor SET username='doctor.zhou', password='Prototype123' WHERE doctor_id='D002';
UPDATE api_doctor SET username='doctor.zhang', password='Prototype123' WHERE doctor_id='D003';
UPDATE api_doctor SET username='doctor.chen', password='Prototype123' WHERE doctor_id='D004';

SELECT 'Schema updated successfully!' AS message;