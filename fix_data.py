import mysql.connector
import random
import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

db_config = {
    'user': config['mysql']['user'],
    'password': config['mysql']['password'],
    'host': config['mysql']['host'],
    'database': 'social_app_db'
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT user_id, user_name FROM User")
    users = cursor.fetchall()

    if not users:
        print("error: No users found in the database. Please run setup.py first.")
        exit()

    print(f"found {len(users)} users in the database.")
    
    creator1 = users[0]['user_id'] 
    creator2 = users[1]['user_id'] if len(users) > 1 else users[0]['user_id'] 


    cursor.execute("DELETE FROM Event_Participant") 
    cursor.execute("DELETE FROM Event")           
    conn.commit()
    
    events_sql = """
    INSERT INTO Event (creator_id, title, description, event_date, max_participants) VALUES
    (%s, '週末外拍團', '去大安森林公園拍照，歡迎新手！', '2026-06-01 14:00:00', 5),
    (%s, '象山夜景團', '爬象山看101，結束後去吃消夜。', '2026-06-05 19:00:00', 10),
    (%s, '期末舒壓聚餐', '考完試了！一起去吃燒肉吧！', '2026-06-10 18:30:00', 4)
    """

    val = (creator1, creator2, creator1)
    
    cursor.execute(events_sql, val)
    conn.commit()
    print("Sample events inserted.")

except Exception as e:
    print(f"error: {e}")

finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()