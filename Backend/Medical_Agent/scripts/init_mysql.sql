-- Docker MySQL 镜像的初始化客户端默认可能为 latin1；种子数据文件为 UTF-8。
SET NAMES utf8mb4;

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


CREATE TABLE api_patient (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(50) NULL UNIQUE,
    username VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    birth_date DATE NULL,
    age INT NOT NULL,
    phone VARCHAR(20) NULL,
    address VARCHAR(200) NULL,
    id_card VARCHAR(20) NULL UNIQUE,
    blood_type VARCHAR(10) NULL,
    health_info TEXT NULL,
    allergy_history JSON NULL,
    emergency_contact VARCHAR(100) NULL,
    emergency_phone VARCHAR(20) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient_username (username),
    INDEX idx_patient_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;




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


CREATE TABLE api_schedule_override (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    doctor_id BIGINT NOT NULL,
    date DATE NOT NULL,
    period VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'closed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_schedule_override_doctor_date_period (doctor_id, date, period),
    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE CASCADE
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


CREATE TABLE api_booking_slot (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    doctor_id BIGINT NOT NULL,
    schedule_id BIGINT NOT NULL,
    order_id BIGINT NOT NULL,
    date DATE NOT NULL,
    time VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_booking_slot_doctor_date_time (doctor_id, date, time),
    UNIQUE KEY uq_booking_slot_order (order_id),
    INDEX idx_booking_slot_schedule (schedule_id),
    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES api_schedule(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES api_order(id) ON DELETE CASCADE
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
('D003', 'doctor.zhang', 'Prototype123', '张砚秋', '主治医师', '中医院', 6, 'LIC003', '针灸', 10, '13900003333', '周二至周日 9:00-18:00', '从事针灸临床10年'),
('D004', 'doctor.chen', 'Prototype123', '陈修远', '主任医师', '中医院', 3, 'LIC004', '中医外科', 25, '13900004444', '周一至周五 8:00-17:00', '从事中医外科25年'),
('D005', 'doctor.shen', 'Prototype123', '沈书安', '主任医师', '中医院', 1, 'LIC005', '中医体质调理', 22, '13900005555', '周一至周五 8:00-17:00', '擅长中医体质辨识与慢病调理'),
('D006', 'doctor.luo', 'Prototype123', '罗清妍', '副主任医师', '中医院', 1, 'LIC006', '亚健康调理', 16, '13900006666', '周二至周日 9:00-18:00', '擅长睡眠、疲劳与亚健康状态调理'),
('D007', 'doctor.gu', 'Prototype123', '顾承泽', '主治医师', '中医院', 2, 'LIC007', '心血管与内分泌', 12, '13900007777', '周一至周六 8:00-17:00', '擅长高血压、眩晕等内科疾病调治'),
('D008', 'doctor.xia', 'Prototype123', '夏知微', '副主任医师', '中医院', 2, 'LIC008', '消化系统疾病', 14, '13900008888', '周一至周五 8:00-17:00', '擅长胃肠疾病与脾胃功能调理'),
('D009', 'doctor.he', 'Prototype123', '何景川', '主治医师', '中医院', 3, 'LIC009', '皮肤与疮疡', 11, '13900009999', '周二至周日 9:00-18:00', '擅长皮肤病、疮疡及术后调理'),
('D010', 'doctor.su', 'Prototype123', '苏婉宁', '主任医师', '中医院', 4, 'LIC010', '月经病与妇科炎症', 21, '13900010010', '周一至周六 8:00-17:00', '擅长月经不调、痛经等妇科疾病诊治'),
('D011', 'doctor.jiang', 'Prototype123', '江月岚', '主治医师', '中医院', 4, 'LIC011', '孕产调理', 9, '13900010011', '周二至周日 9:00-18:00', '擅长备孕、产后恢复及妇科调理'),
('D012', 'doctor.tang', 'Prototype123', '唐予安', '副主任医师', '中医院', 5, 'LIC012', '小儿呼吸系统疾病', 17, '13900010012', '周一至周六 8:00-17:00', '擅长儿童咳嗽、发热等常见病诊治'),
('D013', 'doctor.qiao', 'Prototype123', '乔思远', '主治医师', '中医院', 5, 'LIC013', '小儿脾胃调理', 10, '13900010013', '周二至周日 9:00-18:00', '擅长儿童积食、厌食及体质调理'),
('D014', 'doctor.wen', 'Prototype123', '闻屿川', '副主任医师', '中医院', 6, 'LIC014', '针灸康复', 15, '13900010014', '周一至周六 8:00-17:00', '擅长颈肩腰腿痛与运动损伤针灸康复'),
('D015', 'doctor.fang', 'Prototype123', '方允和', '主任医师', '中医院', 7, 'LIC015', '推拿正骨', 23, '13900010015', '周一至周五 8:00-17:00', '擅长脊柱相关疾病与推拿正骨治疗'),
('D016', 'doctor.ye', 'Prototype123', '叶舒然', '主治医师', '中医院', 7, 'LIC016', '小儿推拿', 8, '13900010016', '周二至周日 9:00-18:00', '擅长小儿推拿与常见病外治'),
('D017', 'doctor.bai', 'Prototype123', '白芷宁', '副主任药师', '中医院', 8, 'LIC017', '中药调剂', 18, '13900010017', '周一至周六 8:00-17:00', '负责中药处方审核与用药咨询'),
('D018', 'doctor.lan', 'Prototype123', '兰若衡', '主管药师', '中医院', 8, 'LIC018', '中药煎煮指导', 13, '13900010018', '周二至周日 9:00-18:00', '擅长中药煎煮、服药方法与用药指导');


INSERT INTO api_schedule (schedule_id, doctor_id, department_id, date, start_time, end_time, morning_afternoon, total_slots, available_slots) VALUES
('SCH_DEMO_001', 1, 2, CURDATE(), '08:00:00', '12:00:00', '上午', 30, 25),
('SCH_DEMO_002', 1, 2, CURDATE(), '14:00:00', '18:00:00', '下午', 30, 30),
('SCH_DEMO_003', 2, 2, CURDATE(), '08:00:00', '12:00:00', '上午', 30, 28),
('SCH_DEMO_004', 1, 2, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '08:00:00', '12:00:00', '上午', 30, 30),
('SCH_DEMO_005', 3, 6, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '14:00:00', '18:00:00', '下午', 30, 20),
('SCH_DEMO_006', 4, 3, CURDATE(), '08:00:00', '12:00:00', '上午', 25, 22),
('SCH_DEMO_007', 5, 1, CURDATE(), '08:00:00', '12:00:00', '上午', 30, 26),
('SCH_DEMO_008', 6, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '14:00:00', '18:00:00', '下午', 30, 30),
('SCH_DEMO_009', 7, 2, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '08:00:00', '12:00:00', '上午', 30, 24),
('SCH_DEMO_010', 8, 2, CURDATE(), '14:00:00', '18:00:00', '下午', 30, 27),
('SCH_DEMO_011', 9, 3, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '08:00:00', '12:00:00', '上午', 25, 21),
('SCH_DEMO_012', 10, 4, CURDATE(), '08:00:00', '12:00:00', '上午', 30, 25),
('SCH_DEMO_013', 11, 4, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '14:00:00', '18:00:00', '下午', 30, 29),
('SCH_DEMO_014', 12, 5, CURDATE(), '08:00:00', '12:00:00', '上午', 30, 23),
('SCH_DEMO_015', 13, 5, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '14:00:00', '18:00:00', '下午', 30, 30),
('SCH_DEMO_016', 14, 6, CURDATE(), '08:00:00', '12:00:00', '上午', 25, 20),
('SCH_DEMO_017', 15, 7, CURDATE(), '14:00:00', '18:00:00', '下午', 25, 22),
('SCH_DEMO_018', 16, 7, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '08:00:00', '12:00:00', '上午', 25, 24),
('SCH_DEMO_019', 17, 8, CURDATE(), '08:00:00', '12:00:00', '上午', 30, 28),
('SCH_DEMO_020', 18, 8, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '14:00:00', '18:00:00', '下午', 30, 30);

SELECT 'MySQL tables created successfully!' AS message;
