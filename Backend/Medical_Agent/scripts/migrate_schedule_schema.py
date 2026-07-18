"""为已有 MySQL 卷补齐排班优化所需的表；可安全重复执行。"""
import os
import sys

import pymysql
from dotenv import load_dotenv


load_dotenv()


def main() -> int:
    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DB", "traditional_medical"),
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_schedule_override (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    doctor_id BIGINT NOT NULL,
                    date DATE NOT NULL,
                    period VARCHAR(10) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'closed',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_schedule_override_doctor_date_period (doctor_id, date, period),
                    FOREIGN KEY (doctor_id) REFERENCES api_doctor(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_booking_slot (
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            # 仅回填具有关联排班的订单；其他历史订单仍由主服务读取 api_order 防止重新放号。
            cursor.execute("""
                INSERT IGNORE INTO api_booking_slot (doctor_id, schedule_id, order_id, date, time)
                SELECT doctor_id, schedule_id, id, date, time
                FROM api_order
                WHERE doctor_id IS NOT NULL
                  AND schedule_id IS NOT NULL
                  AND date IS NOT NULL
                  AND time IS NOT NULL
                  AND status <> 'cancelled'
            """)
        connection.commit()
        print("schedule schema migration completed")
        return 0
    except Exception as exc:
        connection.rollback()
        print(f"schedule schema migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
