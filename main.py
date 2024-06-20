from flask import Flask, request, jsonify
import psycopg2
import psycopg2.pool
import logging
from flask_cors import CORS
import logging
import datetime
import pytz
import re
import yaml
import hashlib
import sys
import requests
import json
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s', handlers=[logging.StreamHandler()])
from config import DB_CREDENTIALS, GOOGLE_ADS_CONFIG, LTV_SAAS_GOOGLE_ADS_ID, PC_GOOGLE_ADS_ID, PC_USER_LIST, ICU_GOOGLE_ADS_ID 
from config import ICU_USER_LIST, TFX_GOOGLE_ADS_ID, TFX_USER_LIST, COD_GOOGLE_ADS_ID, COD_USER_LIST
from config import TFX_META_APP_ID, TFX_META_APP_SECRET, TFX_META_LONG_LIVED_TOKEN, TFX_META_AD_ACCOUNT_ID, TFX_META_CUSTOM_AUDIENCE_ID

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

###################### ADD EMAILS TO META ADS ############################
def meta_test_credentials():
    url = f"https://graph.facebook.com/v12.0/act_{TFX_META_AD_ACCOUNT_ID}"
    params = {
        'access_token': TFX_META_LONG_LIVED_TOKEN,
        'fields': 'name,account_status'
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        logging.info(f"Ad Account Name: {data['name']}")
        logging.info(f"Account Status: {data['account_status']}")
        logging.info("Your tokens and credentials are working correctly.")
        return True
    else:
        logging.info("Failed to fetch ad account information.")
        logging.info(f"Status Code: {response.status_code}")
        logging.info(f"Error: {response.json()}")
        return False

# Function to add a user email to the custom audience
def meta_add_user_to_custom_audience(user_email):
    # Hash the email using SHA-256
    hashed_email = hashlib.sha256(user_email.encode('utf-8')).hexdigest()

    url = f"https://graph.facebook.com/v12.0/{TFX_META_CUSTOM_AUDIENCE_ID}/users"
    payload = {
        'payload': json.dumps({
            'schema': 'EMAIL_SHA256',
            'data': [hashed_email]
        }),
        'access_token': TFX_META_LONG_LIVED_TOKEN
    }
    response = requests.post(url, data=payload)
    return response.json()

###################### ADD EMAILS TO GOOGLE ADS ############################
def add_email_to_customer_list(client, customer_id, user_list_id, email_address):
    user_data_service = client.get_service("UserDataService")

    # Hash the email address using SHA-256
    hashed_email = hashlib.sha256(email_address.encode('utf-8')).hexdigest()
    #logging.info(f'Hashed email: {hashed_email}')

    # Create a user identifier with the hashed email
    user_identifier = client.get_type("UserIdentifier")
    user_identifier.hashed_email = hashed_email

    # Create the user data
    user_data = client.get_type("UserData")
    user_data.user_identifiers.append(user_identifier)

    # Create the operation to add the user to the user list
    user_data_operation = client.get_type("UserDataOperation")
    user_data_operation.create = user_data

    # Create the metadata for the user list
    customer_match_user_list_metadata = client.get_type("CustomerMatchUserListMetadata")
    customer_match_user_list_metadata.user_list = f'customers/{customer_id}/userLists/{user_list_id}'

    # Create the request
    request = client.get_type("UploadUserDataRequest")
    request.customer_id = customer_id
    request.operations.append(user_data_operation)
    request.customer_match_user_list_metadata = customer_match_user_list_metadata

    #logging.info(f'Request: {request}')

    try:
        # Make the upload user data request
        response = user_data_service.upload_user_data(request=request)
        logging.info(f'Response: {response}')
        # Check if the operation was successful
        if hasattr(response, 'partial_failure_error') and response.partial_failure_error:
            for error in response.partial_failure_error.errors:
                logging.error(f'Error: {error.error_code} - {error.message}')
            logging.error(f'Failed to add user with email {email_address} to user list {user_list_id}')
        else:
            logging.info(f'Successfully added user with email {email_address} to user list {user_list_id}')
    except GoogleAdsException as ex:
        logging.error(f'Request failed with status {ex.error.code().name}')
        logging.error(f'Error message: {ex.error.message}')
        logging.error('Errors:')
        for error in ex.failure.errors:
            logging.error(f'\t{error.error_code}: {error.message}')

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

###############################INTERCOM NEW USERS TO GOOGLE AND META ADS FOR TFX ################################
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

    logging.info(f"Received {app_name} NEW USER webhook data at {formatted_timestamp} : email: {email} & id: {id}")
    # logging.info(f"Clean PC data: {needed_data}")
    config_string = GOOGLE_ADS_CONFIG
    config_data = yaml.safe_load(config_string)
    googleads_client = GoogleAdsClient.load_from_dict(config_data)
    try:
        # Replace with your actual customer ID and user list ID
        customer_id = PC_GOOGLE_ADS_ID
        user_list_id = PC_USER_LIST
        email_address = email  # Replace with the actual email you want to add
        add_email_to_customer_list(googleads_client, customer_id, user_list_id, email_address)
    except GoogleAdsException as ex:
        logging.error(f'Request failed with status {ex.error.code().name}')
        logging.error(f'Error message: {ex.error.message}')
        logging.error('Errors:')
        for error in ex.failure.errors:
            logging.error(f'\t{error.error_code}: {error.message}')
        sys.exit(1)
    except ValueError as ve:
        logging.error(f'ValueError: {ve}')
        sys.exit(1)

    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/icu-new-intercom-user', methods=['POST'])
def track_new_icu_user():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    app_name = 'ICU'
    id = event_data.get('data', {}).get('item', {}).get('id')
    email = event_data.get('data', {}).get('item', {}).get('email')
    #app_name = re.search(r'^(.*?) -', event_data.get('formName')).group(1)
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    logging.info(f"Received {app_name} NEW USER webhook data at {formatted_timestamp} : email: {email} & id: {id}")
    # logging.info(f"Clean PC data: {needed_data}")
    config_string = GOOGLE_ADS_CONFIG
    config_data = yaml.safe_load(config_string)
    googleads_client = GoogleAdsClient.load_from_dict(config_data)
    try:
        # Replace with your actual customer ID and user list ID
        customer_id = ICU_GOOGLE_ADS_ID
        user_list_id = ICU_USER_LIST
        email_address = email  # Replace with the actual email you want to add
        add_email_to_customer_list(googleads_client, customer_id, user_list_id, email_address)
    except GoogleAdsException as ex:
        logging.error(f'Request failed with status {ex.error.code().name}')
        logging.error(f'Error message: {ex.error.message}')
        logging.error('Errors:')
        for error in ex.failure.errors:
            logging.error(f'\t{error.error_code}: {error.message}')
        sys.exit(1)
    except ValueError as ve:
        logging.error(f'ValueError: {ve}')
        sys.exit(1)

    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/tfx-new-intercom-user', methods=['POST'])
def track_new_tfx_user():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    app_name = 'TFX'
    id = event_data.get('data', {}).get('item', {}).get('id')
    email = event_data.get('data', {}).get('item', {}).get('email')
    #app_name = re.search(r'^(.*?) -', event_data.get('formName')).group(1)
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    logging.info(f"Received {app_name} NEW USER webhook data at {formatted_timestamp} : email: {email} & id: {id}")
    
    # INSERT EMAIL IN GOOGLE ADS SEGMENT:
    # logging.info(f"Clean PC data: {needed_data}")
    config_string = GOOGLE_ADS_CONFIG
    config_data = yaml.safe_load(config_string)
    googleads_client = GoogleAdsClient.load_from_dict(config_data)
    try:
        # Replace with your actual customer ID and user list ID
        customer_id = TFX_GOOGLE_ADS_ID
        user_list_id = TFX_USER_LIST
        email_address = email  # Replace with the actual email you want to add
        add_email_to_customer_list(googleads_client, customer_id, user_list_id, email_address)
    except GoogleAdsException as ex:
        logging.error(f'Request failed with status {ex.error.code().name}')
        logging.error(f'Error message: {ex.error.message}')
        logging.error('Errors:')
        for error in ex.failure.errors:
            logging.error(f'\t{error.error_code}: {error.message}')
        sys.exit(1)
    except ValueError as ve:
        logging.error(f'ValueError: {ve}')
        sys.exit(1)
    
    # INSERT EMAIL IN META ADS AUDIENCE:
    if meta_test_credentials():
        add_response = meta_add_user_to_custom_audience(email)
        logging.info(f"TFX Meta Add User Response: {add_response}")

        # Check if the email was successfully added
        if add_response.get('num_received') == 1 and add_response.get('num_invalid_entries') == 0:
            logging.info(f"The email {email} was successfully inserted into the TFX Active Users List {TFX_META_CUSTOM_AUDIENCE_ID}")
        else:
            logging.info("The email insertion was not successful.")

    return jsonify({"success": "webhook tracked succesfuly"}), 200

@app.route('/cod-new-intercom-user', methods=['POST'])
def track_new_cod_user():
    timestamp = datetime.datetime.now()
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    event_data = request.get_json()
    app_name = 'COD'
    id = event_data.get('data', {}).get('item', {}).get('id')
    email = event_data.get('data', {}).get('item', {}).get('email')
    #app_name = re.search(r'^(.*?) -', event_data.get('formName')).group(1)
    if not event_data:
        return jsonify({"error": "Invalid data"}), 400

    logging.info(f"Received {app_name} NEW USER webhook data at {formatted_timestamp} : email: {email} & id: {id}")
    # logging.info(f"Clean PC data: {needed_data}")
    config_string = GOOGLE_ADS_CONFIG
    config_data = yaml.safe_load(config_string)
    googleads_client = GoogleAdsClient.load_from_dict(config_data)
    try:
        # Replace with your actual customer ID and user list ID
        customer_id = COD_GOOGLE_ADS_ID
        user_list_id = COD_USER_LIST
        email_address = email  # Replace with the actual email you want to add
        add_email_to_customer_list(googleads_client, customer_id, user_list_id, email_address)
    except GoogleAdsException as ex:
        logging.error(f'Request failed with status {ex.error.code().name}')
        logging.error(f'Error message: {ex.error.message}')
        logging.error('Errors:')
        for error in ex.failure.errors:
            logging.error(f'\t{error.error_code}: {error.message}')
        sys.exit(1)
    except ValueError as ve:
        logging.error(f'ValueError: {ve}')
        sys.exit(1)

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
    email_series = event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('series_title')
    app_name_raw = re.search(r'^(.*?) ', email_series).group(1) if email_series else None
    if app_name_raw == 'SATC' or app_name_raw == 'SR':
        app_name = app_name_raw
    else:
        app_name = 'SATC'

    needed_data = {
        'created_at_utc': event_data.get('data',{}).get('item',{}).get('created_at'),
        'content_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('content_type'),
        'stat_type' : event_data.get('data',{}).get('item',{}).get('content_stat',{}).get('stat_type'),
        'email_series' : email_series,
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