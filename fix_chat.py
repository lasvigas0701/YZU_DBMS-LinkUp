import mysql.connector
import time
import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')


db_config = {
    'user': config['mysql']['user'],
    'password': config['mysql']['password'],
    'host': config['mysql']['host'],
    'database': config['mysql']['database']
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT user_id, user_name FROM User LIMIT 2")
    users = cursor.fetchall()

    if len(users) < 2:
        print("error: Not enough users in the database.")
        exit()

    user_a = users[0]
    user_b = users[1]
    print(f"found two users: {user_a['user_name']} (ID:{user_a['user_id']}) and {user_b['user_name']} (ID:{user_b['user_id']})")

    id1, id2 = sorted([user_a['user_id'], user_b['user_id']])
    cursor.execute("SELECT match_id FROM `Match` WHERE user1_id = %s AND user2_id = %s", (id1, id2))
    match_record = cursor.fetchone()

    match_id = None
    if match_record:
        match_id = match_record['match_id']
        cursor.execute("UPDATE `Match` SET match_status='matched', matched_at=DATE_SUB(NOW(), INTERVAL %s MINUTE) WHERE match_id=%s", (15, match_id))
        print("Matched")
    else:
        cursor.execute("""
            INSERT INTO `Match` (user1_id, user2_id, user1_like, user2_like, match_status, matched_at) 
            VALUES (%s, %s, TRUE, TRUE, 'matched', DATE_SUB(NOW(), INTERVAL %s MINUTE))
        """, (id1, id2, 15))
        match_id = cursor.lastrowid
        print("Created Match")

    cursor.execute("SELECT room_id FROM ChatRoom WHERE match_id = %s", (match_id,))
    room_record = cursor.fetchone()
    
    room_id = None
    if room_record:
        room_id = room_record['room_id']
    else:
        cursor.execute("INSERT INTO ChatRoom (match_id, created_at) VALUES (%s, DATE_SUB(NOW(), INTERVAL %s MINUTE))", (match_id, 15))
        room_id = cursor.lastrowid

    print("room_id:", room_id)
    
    cursor.execute("DELETE FROM Message WHERE room_id = %s", (room_id,))

    messages = [
        (user_a['user_id'], f"嗨！{user_b['user_name']}，很高興認識你！"),
        (user_b['user_id'], "嗨嗨！我也很高興認識你 😊"),
        (user_a['user_id'], "我看你的自介說你喜歡爬山？"),
        (user_b['user_id'], "對啊！我上週末才去爬象山，超累但風景很好！"),
        (user_a['user_id'], "真假！我也超愛象山的夜景，下次一起去？"),
        (user_b['user_id'], "好啊！等你約 👍"),
    ]


    for i, (sender_id, content) in enumerate(messages):
        cursor.execute("""
            INSERT INTO Message (room_id, sender_id, content, sent_at) 
            VALUES (%s, %s, %s, DATE_SUB(NOW(), INTERVAL %s MINUTE))
        """, (room_id, sender_id, content, 10 - i))
    
    conn.commit()

except Exception as e:
    print(f"error: {e}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()