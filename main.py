from flask import Flask, request, jsonify
import psycopg2
import psycopg2.pool
import logging
from flask_cors import CORS
import logging
import datetime
import pytz
import re
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
def track_free_user_survey():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    est_tz = pytz.timezone('America/New_York')
    cst_tz = pytz.timezone('America/Chicago')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    logging.info('test ' + str(event_data.get('submission',{}).get('questions',[])[0].get('value')))
    logging.info(f"Received webhook data at {formatted_timestamp} : {event_data}")

    #Insert to DB template #
    conn = connection_pool.getconn()
    if conn is None:
        logging.error("Failed to connect to the database")
        return jsonify({"error": "Database connection error"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fillout_surveys (submission_id, submission_dt_utc, submission_dt_est, submission_dt_cst, submission_started_utc, submission_started_est,
                    submission_started_cst, status, current_step, enrichment_info, features_rating, cs_rating, proposed_app_changes, email, email2, errors,
                    url, network_id, app, survey_type, plan_upgrade_requests)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            event_data.get('submission',{}).get('submissionId'),
            event_data.get('submission',{}).get('submissionTime'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('submissionTime'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(est_tz).strftime('%Y-%m-%d %H:%M:%S'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('submissionTime'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(cst_tz).strftime('%Y-%m-%d %H:%M:%S'),
            event_data.get('submission',{}).get('lastUpdatedAt'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('lastUpdatedAt'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(est_tz).strftime('%Y-%m-%d %H:%M:%S'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('lastUpdatedAt'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(cst_tz).strftime('%Y-%m-%d %H:%M:%S'),
            "finished",
            "Ending",
            None,
            str(event_data.get('submission',{}).get('questions',[])[0].get('value')),
            str(event_data.get('submission',{}).get('questions',[])[1].get('value')),
            None,
            event_data.get('submission',{}).get('questions',[])[3].get('value'),
            event_data.get('submission',{}).get('calculations',{}).get('urlParameters',{}).get('value'),
            None,
            f"https://build.fillout.com/editor/6zF5G3axRfus/results?sessionId={event_data.get('submission',{}).get('submissionId')}",
            None,
            re.search(r'^(.*?) -', event_data.get('formName')).group(1),
            "Free User",
            event_data.get('submission',{}).get('questions',[])[2].get('value')
        ))
        conn.commit()
        
    except Exception as e:
        logging.error(f"Failed to insert event data: {e}")
        conn.rollback()
        return jsonify({"error": "Failed to insert event data"}), 500
    finally:
        cur.close()
        connection_pool.putconn(conn)
    
    logging.info(f"Received free user survey webhook data at {formatted_timestamp} : {event_data}")
    # logging.info(f"Clean PC data: {needed_data}")
    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/fillout-paid', methods=['POST'])
def track_paid_user_survey():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    est_tz = pytz.timezone('America/New_York')
    cst_tz = pytz.timezone('America/Chicago')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400
    
    #Insert to DB template #
    conn = connection_pool.getconn()
    if conn is None:
        logging.error("Failed to connect to the database")
        return jsonify({"error": "Database connection error"}), 500
    
    logging.info('test ' + str(event_data.get('submission',{}).get('questions',[])[0].get('value')))
    logging.info(f"Received webhook data at {formatted_timestamp} : {event_data}")

    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fillout_surveys (submission_id, submission_dt_utc, submission_dt_est, submission_dt_cst, submission_started_utc, submission_started_est,
                    submission_started_cst, status, current_step, enrichment_info, features_rating, cs_rating, proposed_app_changes, email, email2, errors,
                    url, network_id, app, survey_type, plan_upgrade_requests)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            event_data.get('submission',{}).get('submissionId'),
            event_data.get('submission',{}).get('submissionTime'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('submissionTime'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(est_tz).strftime('%Y-%m-%d %H:%M:%S'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('submissionTime'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(cst_tz).strftime('%Y-%m-%d %H:%M:%S'),
            event_data.get('submission',{}).get('lastUpdatedAt'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('lastUpdatedAt'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(est_tz).strftime('%Y-%m-%d %H:%M:%S'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('lastUpdatedAt'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(cst_tz).strftime('%Y-%m-%d %H:%M:%S'),
            "finished",
            "Ending",
            None,
            str(event_data.get('submission',{}).get('questions',[])[0].get('value')),
            str(event_data.get('submission',{}).get('questions',[])[1].get('value')),
            event_data.get('submission',{}).get('questions',[])[2].get('value'),
            event_data.get('submission',{}).get('questions',[])[3].get('value'),
            event_data.get('submission',{}).get('calculations',{}).get('urlParameters',{}).get('value'),
            None,
            f"https://build.fillout.com/editor/6zF5G3axRfus/results?sessionId={event_data.get('submission',{}).get('submissionId')}",
            None,
            re.search(r'^(.*?) -', event_data.get('formName')).group(1),
            "Paid User",
            None
        ))
        conn.commit()
    except Exception as e:
        logging.error(f"Failed to insert event data: {e}")
        conn.rollback()
        return jsonify({"error": "Failed to insert event data"}), 500
    finally:
        cur.close()
        connection_pool.putconn(conn)

    logging.info(f"Received paid user survey data at {formatted_timestamp} : {event_data}")
    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/fillout-longtime-paid', methods=['POST'])
def track_longtime_paid_user_survey():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    est_tz = pytz.timezone('America/New_York')
    cst_tz = pytz.timezone('America/Chicago')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400
    
    logging.info(f"Received webhook data at {formatted_timestamp} : {event_data}")

    #Insert to DB template #
    conn = connection_pool.getconn()
    if conn is None:
        logging.error("Failed to connect to the database")
        return jsonify({"error": "Database connection error"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fillout_surveys (submission_id, submission_dt_utc, submission_dt_est, submission_dt_cst, submission_started_utc, submission_started_est,
                    submission_started_cst, status, current_step, enrichment_info, features_rating, cs_rating, proposed_app_changes, email, email2, errors,
                    url, network_id, app, survey_type, plan_upgrade_requests)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            event_data.get('submission',{}).get('submissionId'),
            event_data.get('submission',{}).get('submissionTime'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('submissionTime'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(est_tz).strftime('%Y-%m-%d %H:%M:%S'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('submissionTime'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(cst_tz).strftime('%Y-%m-%d %H:%M:%S'),
            event_data.get('submission',{}).get('lastUpdatedAt'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('lastUpdatedAt'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(est_tz).strftime('%Y-%m-%d %H:%M:%S'),
            datetime.datetime.strptime(event_data.get('submission',{}).get('lastUpdatedAt'), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC).astimezone(cst_tz).strftime('%Y-%m-%d %H:%M:%S'),
            "finished",
            "Ending",
            None,
            str(event_data.get('submission',{}).get('questions',[])[0].get('value')),
            str(event_data.get('submission',{}).get('questions',[])[1].get('value')),
            event_data.get('submission',{}).get('questions',[])[2].get('value'),
            event_data.get('submission',{}).get('questions',[])[3].get('value'),
            event_data.get('submission',{}).get('calculations',{}).get('urlParameters',{}).get('value'),
            None,
            f"https://build.fillout.com/editor/6zF5G3axRfus/results?sessionId={event_data.get('submission',{}).get('submissionId')}",
            None,
            re.search(r'^(.*?) -', event_data.get('formName')).group(1),
            "Long Time Paid",
            None
        ))
        conn.commit()
        
    except Exception as e:
        logging.error(f"Failed to insert event data: {e}")
        conn.rollback()
        return jsonify({"error": "Failed to insert event data"}), 500
    finally:
        cur.close()
        connection_pool.putconn(conn)

    logging.info(f"Received long time paid user survey data at {formatted_timestamp} : {event_data}")
    return jsonify({"success": "webhook tracked succesfuly"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)