from flask import Flask, request, jsonify
import psycopg2
import psycopg2.pool
import logging
from flask_cors import CORS
import logging
import datetime
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s', handlers=[logging.StreamHandler()])
from config import DB_CREDENTIALS

app = Flask(__name__)
CORS(app)  # Enable CORS on the Flask app
logging.basicConfig(level=logging.INFO)

# Set up a connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10,  # minconn, maxconn
                                                     host=DB_CREDENTIALS['host'],
                                                     port=DB_CREDENTIALS['port'],
                                                     dbname=DB_CREDENTIALS['database'],
                                                     user=DB_CREDENTIALS['user'],
                                                     password=DB_CREDENTIALS['password'],
                                                     sslmode=DB_CREDENTIALS['sslmode'])

@app.route('/fillout-free', methods=['POST'])
def track_pc_email_stat():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    # conn = connection_pool.getconn()
    # if conn is None:
    #     logging.error("Failed to connect to the database")
    #     return jsonify({"error": "Database connection error"}), 500
    
    # cur = conn.cursor()
    # try:
    #     cur.execute("""
    #         INSERT INTO coupons_redeemed (created_at_utc,email, name, shop_url, app, coupon_redeemed)
    #         VALUES (%s, %s, %s, %s, %s, %s)
    #     """, (
    #         formatted_timestamp,
    #         event_data.get('email'),
    #         event_data.get('name'),
    #         event_data.get('shop_url'),
    #         event_data.get('app'),
    #         event_data.get('coupon_redeemed')
    #     ))
    #     conn.commit()
    #     logging.info(f"Received webhook data at {formatted_timestamp} : {event_data}")
    # except Exception as e:
    #     logging.error(f"Failed to insert event data: {e}")
    #     conn.rollback()
    #     return jsonify({"error": "Failed to insert event data"}), 500
    # finally:
    #     cur.close()
    #     connection_pool.putconn(conn)
    # needed_data = {
    #     'created_at_utc': event_data.get('data',{}).get('item',{}).get('created_at'),
    #     'content_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_type'),
    # }
    logging.info(f"Received free user survey webhook data at {formatted_timestamp} : {event_data}")
    # logging.info(f"Clean PC data: {needed_data}")
    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/fillout-paid', methods=['POST'])
def track_pc_email_stat():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    logging.info(f"Received paid user survey data at {formatted_timestamp} : {event_data}")
    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/fillout-longtime-paid', methods=['POST'])
def track_pc_email_stat():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    logging.info(f"Received long time paid user survey data at {formatted_timestamp} : {event_data}")
    return jsonify({"success": "webhook tracked succesfuly"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)