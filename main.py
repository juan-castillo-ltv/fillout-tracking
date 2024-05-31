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

##########################FILLOUT SURVEYS#################################
@app.route('/fillout-free', methods=['POST'])
def track_free_user_survey():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    est_tz = pytz.timezone('America/New_York')
    cst_tz = pytz.timezone('America/Chicago')
    event_data = request.get_json()
    app_name = re.search(r'^(.*?) -', event_data.get('formName')).group(1)
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    logging.info('test ' + str(event_data.get('submission',{}).get('questions',[])[0].get('value')))
    logging.info(f"Received {app_name} webhook data at {formatted_timestamp} : {event_data}")

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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            event_data.get('submission',{}).get('urlParameters',[])[0].get('value'),
            None,
            f"https://build.fillout.com/editor/6zF5G3axRfus/results?sessionId={event_data.get('submission',{}).get('submissionId')}",
            None,
            app_name,
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
    
    
    # logging.info(f"Clean PC data: {needed_data}")
    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/fillout-paid', methods=['POST'])
def track_paid_user_survey():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    est_tz = pytz.timezone('America/New_York')
    cst_tz = pytz.timezone('America/Chicago')
    event_data = request.get_json()
    app_name = re.search(r'^(.*?) -', event_data.get('formName')).group(1)
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400
    
    #Insert to DB template #
    conn = connection_pool.getconn()
    if conn is None:
        logging.error("Failed to connect to the database")
        return jsonify({"error": "Database connection error"}), 500
    
    logging.info('test ' + str(event_data.get('submission',{}).get('questions',[])[0].get('value')))
    logging.info(f"Received {app_name} webhook data at {formatted_timestamp} : {event_data}")

    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fillout_surveys (submission_id, submission_dt_utc, submission_dt_est, submission_dt_cst, submission_started_utc, submission_started_est,
                    submission_started_cst, status, current_step, enrichment_info, features_rating, cs_rating, proposed_app_changes, email, email2, errors,
                    url, network_id, app, survey_type, plan_upgrade_requests)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            event_data.get('submission',{}).get('urlParameters',[])[0].get('value'),
            None,
            f"https://build.fillout.com/editor/6zF5G3axRfus/results?sessionId={event_data.get('submission',{}).get('submissionId')}",
            None,
            app_name,
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

    
    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/fillout-longtime-paid', methods=['POST'])
def track_longtime_paid_user_survey():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    est_tz = pytz.timezone('America/New_York')
    cst_tz = pytz.timezone('America/Chicago')
    event_data = request.get_json()
    app_name = re.search(r'^(.*?) -', event_data.get('formName')).group(1)
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400
    
    logging.info(f"Received {app_name} webhook data at {formatted_timestamp} : {event_data}")

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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            event_data.get('submission',{}).get('urlParameters',[])[0].get('value'),
            None,
            f"https://build.fillout.com/editor/6zF5G3axRfus/results?sessionId={event_data.get('submission',{}).get('submissionId')}",
            None,
            app_name,
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

    
    return jsonify({"success": "webhook tracked succesfuly"}), 200

###############################INTERCOM NEW USERS################################
@app.route('/pc-new-intercom-user', methods=['POST'])
def track_new_pc_user():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    app_name = 'PC'
    id = event_data.get('data', {}).get('item', {}).get('id')
    email = event_data.get('data', {}).get('item', {}).get('email')
    #app_name = re.search(r'^(.*?) -', event_data.get('formName')).group(1)
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    logging.info(f"Received {app_name} webhook data at {formatted_timestamp} : email: {email} & id: {id}")
    # logging.info(f"Clean PC data: {needed_data}")
    return jsonify({"success": "webhook tracked succesfuly"}), 200

###############################EMAIL STATS################################
@app.route('/pc-email-stats', methods=['POST'])
def track_pc_email_stat():
    #timestamp = datetime.datetime.now()
    #formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    needed_data = {
        'created_at_utc': event_data.get('data',{}).get('item',{}).get('created_at'),
        'content_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_type'),
        'stat_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('stat_type'),
        'email_series' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('series_title'),
        'email_title' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_title'),
        'name' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('name'),
        'email' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('email'),
        'shop_url' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('custom_attributes',{}).get('shop_url')
    }
    #logging.info(f"Received PC webhook data at {event_data.get('data',{}).get('item',{}).get('created_at',{})} : {event_data}")
    logging.info(f"Email stat webhook received. Clean PC data: {needed_data}")
    
    conn = connection_pool.getconn()
    if conn is None:
        logging.error("Failed to connect to the database")
        return jsonify({"error": "Database connection error"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO intercom_email_stats (created_at_utc,content_type,stat_type,email_series,email_title,name,email,shop_url,app)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            needed_data['created_at_utc'],
            needed_data['content_type'],
            needed_data['stat_type'],
            needed_data['email_series'],
            needed_data['email_title'],
            needed_data['name'],
            needed_data['email'],
            needed_data['shop_url'],
            "PC"
        ))
        conn.commit()
        logging.info(f"Inserted webhook data into DB table.")
    except Exception as e:
        logging.error(f"Failed to insert event data: {e}")
        conn.rollback()
        return jsonify({"error": "Failed to insert event data"}), 500
    finally:
        cur.close()
        connection_pool.putconn(conn)

    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/icu-email-stats', methods=['POST'])
def track_icu_email_stat():
    #timestamp = datetime.datetime.now()
    #formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    needed_data = {
        'created_at_utc': event_data.get('data',{}).get('item',{}).get('created_at'),
        'content_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_type'),
        'stat_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('stat_type'),
        'email_series' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('series_title'),
        'email_title' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_title'),
        'name' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('name'),
        'email' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('email'),
        'shop_url' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('custom_attributes',{}).get('shop_url')
    }
    #logging.info(f"Received ICU webhook data at {event_data.get('data',{}).get('item',{}).get('created_at',{})} : {event_data}")
    logging.info(f"Email stat webhook received. Clean ICU data: {needed_data}")

    conn = connection_pool.getconn()
    if conn is None:
        logging.error("Failed to connect to the database")
        return jsonify({"error": "Database connection error"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO intercom_email_stats (created_at_utc,content_type,stat_type,email_series,email_title,name,email,shop_url,app)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            needed_data['created_at_utc'],
            needed_data['content_type'],
            needed_data['stat_type'],
            needed_data['email_series'],
            needed_data['email_title'],
            needed_data['name'],
            needed_data['email'],
            needed_data['shop_url'],
            "ICU"
        ))
        conn.commit()
        logging.info(f"Inserted webhook data into DB table.")
    except Exception as e:
        logging.error(f"Failed to insert event data: {e}")
        conn.rollback()
        return jsonify({"error": "Failed to insert event data"}), 500
    finally:
        cur.close()
        connection_pool.putconn(conn)

    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/tfx-email-stats', methods=['POST'])
def track_tfx_email_stat():
    #timestamp = datetime.datetime.now()
    #formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    needed_data = {
        'created_at_utc': event_data.get('data',{}).get('item',{}).get('created_at'),
        'content_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_type'),
        'stat_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('stat_type'),
        'email_series' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('series_title'),
        'email_title' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_title'),
        'name' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('name'),
        'email' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('email'),
        'shop_url' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('custom_attributes',{}).get('shop_url')
    }
    #logging.info(f"Received TFX webhook data at {event_data.get('data',{}).get('item',{}).get('created_at',{})} : {event_data}")
    logging.info(f"Email stat webhook received. Clean TFX data: {needed_data}")

    conn = connection_pool.getconn()
    if conn is None:
        logging.error("Failed to connect to the database")
        return jsonify({"error": "Database connection error"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO intercom_email_stats (created_at_utc,content_type,stat_type,email_series,email_title,name,email,shop_url,app)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            needed_data['created_at_utc'],
            needed_data['content_type'],
            needed_data['stat_type'],
            needed_data['email_series'],
            needed_data['email_title'],
            needed_data['name'],
            needed_data['email'],
            needed_data['shop_url'],
            "TFX"
        ))
        conn.commit()
        logging.info(f"Inserted webhook data into DB table.")
    except Exception as e:
        logging.error(f"Failed to insert event data: {e}")
        conn.rollback()
        return jsonify({"error": "Failed to insert event data"}), 500
    finally:
        cur.close()
        connection_pool.putconn(conn)

    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/cod-email-stats', methods=['POST'])
def track_cod_email_stat():
    #timestamp = datetime.datetime.now()
    #formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400
    app_name = re.search(r'^(.*?) -', event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('series_title')).group(1)
    needed_data = {
        'created_at_utc': event_data.get('data',{}).get('item',{}).get('created_at'),
        'content_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_type'),
        'stat_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('stat_type'),
        'email_series' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('series_title'),
        'email_title' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_title'),
        'name' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('name'),
        'email' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('email'),
        'shop_url' : event_data.get('data',{}).get('item',{}).get('contact',{}).get('custom_attributes',{}).get('shop_url')
    }
    #logging.info(f"Received SATC webhook data at {event_data.get('data',{}).get('item',{}).get('created_at',{})} : {event_data}")
    logging.info(f"Email stat webhook received. Clean {app_name} data: {needed_data}")

    conn = connection_pool.getconn()
    if conn is None:
        logging.error("Failed to connect to the database")
        return jsonify({"error": "Database connection error"}), 500
    
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO intercom_email_stats (created_at_utc,content_type,stat_type,email_series,email_title,name,email,shop_url,app)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            needed_data['created_at_utc'],
            needed_data['content_type'],
            needed_data['stat_type'],
            needed_data['email_series'],
            needed_data['email_title'],
            needed_data['name'],
            needed_data['email'],
            needed_data['shop_url'],
            app_name
        ))
        conn.commit()
        logging.info(f"Inserted webhook data into DB table.")
    except Exception as e:
        logging.error(f"Failed to insert event data: {e}")
        conn.rollback()
        return jsonify({"error": "Failed to insert event data"}), 500
    finally:
        cur.close()
        connection_pool.putconn(conn)

    return jsonify({"success": "webhook tracked succesfuly"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)