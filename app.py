import mysql.connector
import configparser 
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)


config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

try:
    db_config = {
        'user': config['mysql']['user'],
        'password': config['mysql']['password'],
        'host': config['mysql']['host'],
        'database': config['mysql']['database']
    }
except KeyError:
    print("error in config.ini!!")
    exit()

def get_db_connection():
    return mysql.connector.connect(**db_config)


def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/users', methods=['GET'])
def get_users():
    current_user_id = request.args.get('current_user_id', 1) 
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    

    sql = """
        SELECT u.user_id, u.user_name, u.bio, u.gender,
               GROUP_CONCAT(i.interest_name) as interests
        FROM User u
        LEFT JOIN User_Interest ui ON u.user_id = ui.user_id
        LEFT JOIN Interest i ON ui.interest_id = i.interest_id
        WHERE u.user_id != %s
        AND NOT EXISTS (
            SELECT 1 FROM Block b 
            WHERE (b.blocker_id = %s AND b.blocked_id = u.user_id) 
               OR (b.blocker_id = u.user_id AND b.blocked_id = %s)
        )
        GROUP BY u.user_id
    """
    cursor.execute(sql, (current_user_id, current_user_id, current_user_id))
    users = cursor.fetchall()
    
    # turn interests string into list
    for user in users:
        if user['interests']:
            user['interests'] = user['interests'].split(',')
        else:
            user['interests'] = []
            
    conn.close()
    return jsonify(users)

#block user API
@app.route('/api/block', methods=['POST'])
def block_user():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT IGNORE INTO Block (blocker_id, blocked_id) VALUES (%s, %s)", 
                       (data['blocker_id'], data['blocked_id']))
        

        
        conn.commit()
        return jsonify({"message": "already blocked", "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/matches/like', methods=['POST'])
def like_user():
    data = request.json
    source_id, target_id = data.get('source_id'), data.get('target_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        id1, id2 = sorted([source_id, target_id])
        cursor.execute("SELECT * FROM `Match` WHERE user1_id = %s AND user2_id = %s", (id1, id2))
        match = cursor.fetchone()

        if match:
            field = "user1_like" if source_id == id1 else "user2_like"
            other = match['user2_like'] if source_id == id1 else match['user1_like']
            cursor.execute(f"UPDATE `Match` SET {field} = TRUE WHERE match_id = %s", (match['match_id'],))
            
            if other: 
                cursor.execute("UPDATE `Match` SET match_status = 'matched', matched_at = NOW() WHERE match_id = %s", (match['match_id'],))
                cursor.execute("INSERT IGNORE INTO ChatRoom (match_id) VALUES (%s)", (match['match_id'],))
                conn.commit()
                return jsonify({"message": "It's a Match!", "status": "matched"})
            
            conn.commit()
            return jsonify({"message": "Liked!", "status": "pending"})
        else:
            is_user1 = (source_id == id1)
            vals = (id1, id2, True, False) if is_user1 else (id1, id2, False, True)
            cursor.execute("INSERT INTO `Match` (user1_id, user2_id, user1_like, user2_like, match_status) VALUES (%s, %s, %s, %s, 'pending')", vals)
            conn.commit()
            return jsonify({"message": "Liked sent!", "status": "pending"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

#event APIs
@app.route('/api/events', methods=['GET'])
def get_events():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT e.*, u.user_name as creator_name,
        (SELECT COUNT(*) FROM Event_Participant ep WHERE ep.event_id = e.event_id) as current_count
        FROM Event e JOIN User u ON e.creator_id = u.user_id ORDER BY e.event_date
    """
    cursor.execute(sql)
    events = cursor.fetchall()
    conn.close()
    return jsonify(events)

@app.route('/api/events/join', methods=['POST'])
def join_event():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Event WHERE event_id = %s", (data['event_id'],))
        event = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as c FROM Event_Participant WHERE event_id=%s", (data['event_id'],))
        if cursor.fetchone()['c'] >= event['max_participants']:
            return jsonify({"message": "已額滿", "status": "full"})
        cursor.execute("INSERT IGNORE INTO Event_Participant (event_id, user_id) VALUES (%s, %s)", (data['event_id'], data['user_id']))
        conn.commit()
        return jsonify({"message": "報名成功", "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

#chat APIs
@app.route('/api/my_matches', methods=['GET'])
def get_my_matches():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT m.match_id, 
               CASE WHEN m.user1_id = %s THEN u2.user_name ELSE u1.user_name END as friend_name,
               c.room_id
        FROM `Match` m
        JOIN User u1 ON m.user1_id = u1.user_id
        JOIN User u2 ON m.user2_id = u2.user_id
        JOIN ChatRoom c ON m.match_id = c.match_id
        WHERE (m.user1_id = %s OR m.user2_id = %s) AND m.match_status = 'matched'
    """
    cursor.execute(sql, (user_id, user_id, user_id))
    matches = cursor.fetchall()
    conn.close()
    return jsonify(matches)

@app.route('/api/messages', methods=['GET', 'POST'])
def messages():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'GET':
        room_id = request.args.get('room_id')
        sql = "SELECT msg.*, u.user_name FROM Message msg JOIN User u ON msg.sender_id = u.user_id WHERE room_id = %s ORDER BY sent_at"
        cursor.execute(sql, (room_id,))
        msgs = cursor.fetchall()
        conn.close()
        return jsonify(msgs)
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO Message (room_id, sender_id, content) VALUES (%s, %s, %s)",
                       (data['room_id'], data['sender_id'], data['content']))
        conn.commit()
        conn.close()
        return jsonify({"status": "sent"})

if __name__ == '__main__':
    app.run(debug=True)