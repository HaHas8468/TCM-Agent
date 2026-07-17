CREATE TABLE api_department (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    department_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    parent_department_id BIGINT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_department_name (name),
    FOREIGN KEY (parent_department_id) REFERENCES api_department(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


。


CREATE TABLE api_doctor (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    doctor_id VARCHAR(50) NOT NULL UNIQUE,
    username VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    name VARCHAR(100) NOT NULL,
    title VARCHAR(50) NULL,
    hospital VARCHAR(100) NULL,
    department_id BIGINT NULL,
    license_number VARCHAR(50) NULL,
    specialty VARCHAR(100) NULL,
    experience INT NULL,
    phone VARCHAR(20) NULL,
    duty_time VARCHAR(100) NULL,
    bio TEXT NULL,
    description TEXT NULL,
    default_landing VARCHAR(50) NOT NULL DEFAULT 'queue',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doctor_name (name),
    INDEX idx_doctor_username (username),
    INDEX idx_doctor_department (department_id),
    FOREIGN KEY (department_id) REFERENCES api_department(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE api_schedule (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    schedule_id VARCHAR(50) NOT NULL UNIQUE,
    doctor_id BIGINT NOT NULL,
    department_id BIGINT NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    morning_afternoon VARCHAR(10) NOT NULL,
    total_slots INT NOT NULL DEFAULT 30,
    available_slots INT NOT NULL DEFAULT 30,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_schedule_doctor (doctor_id),
    INDEX idx_schedule_department (department_id),
    INDEX idx_schedule_date (date),
    INDEX idx_schedule_status (status),
    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES api_department(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE api_order (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL UNIQUE,
    patient_id BIGINT NOT NULL,
    doctor_id BIGINT NULL,
    department_id BIGINT NULL,
    department VARCHAR(100) NULL,
    schedule_id BIGINT NULL,
    order_type VARCHAR(20) NOT NULL DEFAULT 'online',
    source VARCHAR(20) NOT NULL DEFAULT 'direct',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    visit_time DATETIME NULL,
    date DATE NULL,
    time VARCHAR(20) NULL,
    waiting_number INT NULL,
    amount DECIMAL(10,2) NULL,
    payment_time DATETIME NULL,
    qr_code VARCHAR(200) NULL,
    scanned TINYINT(1) NOT NULL DEFAULT 0,
    chief_complaint TEXT NULL,
    present_illness TEXT NULL,
    tongue VARCHAR(200) NULL,
    pulse VARCHAR(200) NULL,
    symptoms JSON NULL,
    signs VARCHAR(200) NULL,
    other TEXT NULL,
    syndrome VARCHAR(200) NULL,
    prescription VARCHAR(200) NULL,
    ingredients JSON NULL,
    advice TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_patient (patient_id),
    INDEX idx_order_doctor (doctor_id),
    INDEX idx_order_status (status),
    INDEX idx_order_created_at (created_at),
    FOREIGN KEY (patient_id) REFERENCES api_patient(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES api_department(id) ON DELETE SET NULL,
    FOREIGN KEY (schedule_id) REFERENCES api_schedule(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE api_chat (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL UNIQUE,
    patient_id BIGINT NOT NULL,
    doctor_id BIGINT NULL,
    order_id BIGINT NULL,
    messages JSON NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_chat_patient (patient_id),
    INDEX idx_chat_doctor (doctor_id),
    INDEX idx_chat_session (session_id),
    FOREIGN KEY (patient_id) REFERENCES api_patient(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE SET NULL,
    FOREIGN KEY (order_id) REFERENCES api_order(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE api_chatmessage (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    sender_type VARCHAR(20) NOT NULL,
    sender_id INT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    INDEX idx_chatmessage_chat (chat_id),
    INDEX idx_chatmessage_created_at (created_at),
    FOREIGN KEY (chat_id) REFERENCES api_chat(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE api_clinicrecord (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    record_id VARCHAR(50) NOT NULL UNIQUE,
    patient_id BIGINT NOT NULL,
    doctor_id BIGINT NULL,
    order_id BIGINT NULL,
    visit_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    chief_complaint TEXT NOT NULL,
    history_of_present_illness TEXT NULL,
    past_history TEXT NULL,
    physical_examination TEXT NULL,
    tongue VARCHAR(200) NULL,
    pulse VARCHAR(200) NULL,
    other_signs TEXT NULL,
    zheng_type VARCHAR(100) NULL,
    zheng_description TEXT NULL,
    diagnosis TEXT NULL,
    treatment_principle TEXT NULL,
    treatment_plan TEXT NULL,
    prescription VARCHAR(200) NULL,
    herbs JSON NULL,
    ingredients JSON NULL,
    dosage TEXT NULL,
    decoction_method TEXT NULL,
    advice TEXT NULL,
    notes TEXT NULL,
    follow_up VARCHAR(100) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_clinicrecord_patient (patient_id),
    INDEX idx_clinicrecord_doctor (doctor_id),
    INDEX idx_clinicrecord_visit_date (visit_date),
    FOREIGN KEY (patient_id) REFERENCES api_patient(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE SET NULL,
    FOREIGN KEY (order_id) REFERENCES api_order(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE api_collection (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    collection_type VARCHAR(20) NOT NULL,
    target_id VARCHAR(100) NOT NULL,
    target_name VARCHAR(200) NOT NULL,
    extra_info JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_collection_user_target (user_id, collection_type, target_id),
    INDEX idx_collection_user (user_id),
    INDEX idx_collection_type (collection_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE api_diagnosissession (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    doctor_id BIGINT NULL,
    symptoms TEXT NOT NULL,
    tongue VARCHAR(200) NULL,
    pulse VARCHAR(200) NULL,
    other_signs TEXT NULL,
    zheng_type VARCHAR(100) NULL,
    zheng_description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_diagnosissession_patient (patient_id),
    FOREIGN KEY (patient_id) REFERENCES api_patient(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE api_prescription (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    diagnosis_session_id BIGINT NOT NULL,
    doctor_id BIGINT NULL,
    main_formula VARCHAR(200) NOT NULL,
    formula_description TEXT NULL,
    herbs TEXT NOT NULL,
    dosage TEXT NOT NULL,
    decoction_method TEXT NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prescription_diagnosis_session (diagnosis_session_id),
    FOREIGN KEY (diagnosis_session_id) REFERENCES api_diagnosissession(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;




INSERT INTO api_department (department_id, name, description) VALUES
('DEPT001', '中医科', '中医内科、外科、妇科、儿科等综合科室'),
('DEPT002', '中医内科', '诊治内科疾病，如感冒、咳嗽、脾胃病等'),
('DEPT003', '中医外科', '诊治外科疾病，如疮疡、皮肤病等'),
('DEPT004', '中医妇科', '诊治妇科疾病，如月经不调、痛经等'),
('DEPT005', '中医儿科', '诊治儿科疾病，如小儿发热、咳嗽等'),
('DEPT006', '针灸科', '针灸治疗各种疾病'),
('DEPT007', '推拿科', '推拿按摩治疗各种疾病'),
('DEPT008', '中药房', '中药调配与发放');

UPDATE api_department SET parent_department_id = 1 WHERE id IN (2, 3, 4, 5);


INSERT INTO api_doctor (doctor_id, username, password, name, title, hospital, department_id, license_number, specialty, experience, phone, duty_time, bio) VALUES
('D001', 'doctor.lin', 'Prototype123', '林青和', '主任医师', '中医院', 2, 'LIC001', '呼吸系统疾病', 20, '13900001111', '周一至周五 8:00-17:00', '从事中医临床20年，擅长呼吸系统疾病诊治'),
('D002', 'doctor.zhou', 'Prototype123', '周闻素', '副主任医师', '中医院', 2, 'LIC002', '脾胃病', 15, '13900002222', '周一至周六 8:00-17:00', '从事中医临床15年，擅长脾胃病诊治'),
('D003', 'doctor.zhang', 'Prototype123', '张医生', '主治医师', '中医院', 6, 'LIC003', '针灸', 10, '13900003333', '周二至周日 9:00-18:00', '从事针灸临床10年'),
('D004', 'doctor.chen', 'Prototype123', '陈医生', '主任医师', '中医院', 3, 'LIC004', '中医外科', 25, '13900004444', '周一至周五 8:00-17:00', '从事中医外科25年');


INSERT INTO api_schedule (schedule_id, doctor_id, department_id, date, start_time, end_time, morning_afternoon, total_slots, available_slots) VALUES
('SCH20260710001', 1, 2, '2026-07-10', '08:00:00', '12:00:00', '上午', 30, 25),
('SCH20260710002', 1, 2, '2026-07-10', '14:00:00', '18:00:00', '下午', 30, 30),
('SCH20260710003', 2, 2, '2026-07-10', '08:00:00', '12:00:00', '上午', 30, 28),
('SCH20260711001', 1, 2, '2026-07-11', '08:00:00', '12:00:00', '上午', 30, 30),
('SCH20260711002', 3, 6, '2026-07-11', '14:00:00', '18:00:00', '下午', 30, 20);

SELECT 'MySQL tables created successfully!' AS message;