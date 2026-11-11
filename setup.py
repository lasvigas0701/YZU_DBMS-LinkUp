import mysql.connector
import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')


db_config = {
    'user': config['mysql']['user'],
    'password': config['mysql']['password'],
    'host': config['mysql']['host']
}

sql_commands = [
    "DROP DATABASE IF EXISTS social_app_db",
    "CREATE DATABASE IF NOT EXISTS social_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
    "USE social_app_db",


    """CREATE TABLE IF NOT EXISTS User (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        user_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        gender ENUM('Male', 'Female', 'Non-binary', 'Other') NOT NULL,
        age INT,
        bio TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",


    """CREATE TABLE IF NOT EXISTS Interest (
        interest_id INT AUTO_INCREMENT PRIMARY KEY,
        interest_name VARCHAR(50) NOT NULL UNIQUE
    )""",


    """CREATE TABLE IF NOT EXISTS User_Interest (
        user_id INT,
        interest_id INT,
        PRIMARY KEY (user_id, interest_id),
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
        FOREIGN KEY (interest_id) REFERENCES Interest(interest_id) ON DELETE CASCADE
    )""",


    """CREATE TABLE IF NOT EXISTS Block (
        blocker_id INT,
        blocked_id INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (blocker_id, blocked_id),
        FOREIGN KEY (blocker_id) REFERENCES User(user_id) ON DELETE CASCADE,
        FOREIGN KEY (blocked_id) REFERENCES User(user_id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS Event (
        event_id INT AUTO_INCREMENT PRIMARY KEY,
        creator_id INT NOT NULL,
        title VARCHAR(100) NOT NULL,
        description TEXT,
        event_date DATETIME NOT NULL,
        max_participants INT DEFAULT 10,
        FOREIGN KEY (creator_id) REFERENCES User(user_id) ON DELETE CASCADE
    )""",


    """CREATE TABLE IF NOT EXISTS Event_Participant (
        event_id INT,
        user_id INT,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (event_id, user_id),
        FOREIGN KEY (event_id) REFERENCES Event(event_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS `Match` (
        match_id INT AUTO_INCREMENT PRIMARY KEY,
        user1_id INT NOT NULL,
        user2_id INT NOT NULL,
        user1_like BOOLEAN DEFAULT FALSE,
        user2_like BOOLEAN DEFAULT FALSE,
        match_status ENUM('pending', 'matched', 'rejected') DEFAULT 'pending',
        matched_at DATETIME DEFAULT NULL,
        FOREIGN KEY (user1_id) REFERENCES User(user_id) ON DELETE CASCADE,
        FOREIGN KEY (user2_id) REFERENCES User(user_id) ON DELETE CASCADE,
        CHECK (user1_id < user2_id)
    )""",

    """CREATE TABLE IF NOT EXISTS ChatRoom (
        room_id INT AUTO_INCREMENT PRIMARY KEY,
        match_id INT NOT NULL UNIQUE, 
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (match_id) REFERENCES `Match`(match_id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS Message (
        message_id INT AUTO_INCREMENT PRIMARY KEY,
        room_id INT NOT NULL,
        sender_id INT NOT NULL,
        content TEXT NOT NULL,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES ChatRoom(room_id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES User(user_id) ON DELETE CASCADE
    )""",

    """INSERT IGNORE INTO User (user_name, email, gender, age, bio, created_at) VALUES
    ('Alice Chen', 'alice@example.com', 'Female', 25, '喜愛攝影與旅行的工程師', '2026-01-01 10:00:00'),
    ('Bob Wang', 'bob@example.com', 'Male', 28, '健身狂熱者，週末喜歡爬山', '2026-01-02 11:30:00'),
    ('Charlie Lee', 'charlie@example.com', 'Male', 24, '剛畢業的新鮮人，喜歡打電動', '2026-01-03 09:15:00'),
    ('Diana Lin', 'diana@example.com', 'Female', 27, '美食部落客，尋找飯友', '2026-01-04 14:20:00'),
    ('Evan Wu', 'evan@example.com', 'Non-binary', 26, '藝術家，喜歡參觀畫廊', '2026-01-05 16:45:00')""",

    """INSERT IGNORE INTO Interest (interest_name) VALUES
    ('Photography'), ('Hiking'), ('Gaming'), ('Foodie'), ('Art')""",

    """INSERT IGNORE INTO User_Interest (user_id, interest_id) VALUES
    (1, 1), (1, 2), (2, 2), (3, 3),
    (4, 4), (5, 5)"""
]


try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    
    for command in sql_commands:

        if command.strip():
            cursor.execute(command)
    
    conn.commit()

except mysql.connector.Error as err:
    print(f"❌ Error: {err}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()