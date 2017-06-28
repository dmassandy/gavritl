import os
import logging
import traceback
from time import sleep
import django
import redis
import boto3
import json
import requests
from threading import Thread
from gavritl import settings

from telegram.utils import phone_norm,get_filename

# needed for setting up django standalone apps
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gavritl.settings')
django.setup()

INCOMING_THREAD_RUN = True

def sendJsonToMoobiDesk(prefix, url, data):
    if prefix == '':
        return True
    # logging.debug(data)
    response = requests.post(prefix + url, json=data)
    logging.info("Sending to moobidesk %s - %s"%(response.status_code,response.text))
    response_data = json.loads(response.text)
    return response_data['status'].lower() == "ok"

def send_incoming_message(message, s3_client):
    # send incoming message to Moobidesk
    logging.info("Received incoming message")
    payload = {
        "phone_from" : message["from"],
        "phone_to" : message["to"],
        "message_id" : message["id"],
        "type" :  message["message_type"],
        "sender_first_name" : message["sender_first_name"]
    }
    if "sender_last_name" in message:
        payload["sender_last_name"] = message["sender_last_name"]
    
    if message["message_type"] == "text" :
        payload["message"] = message["body"]
    elif message["message_type"] == "location":
        payload["lat"] = message["lat"]
        payload["long"] = message["long"]
        if "title" in message:
            payload['title'] = message['title']
        if "address" in message:
            payload['address'] = message['address']
        if "provider" in message:
            payload['provider'] = message['provider']
        if "venue_id" in message:
            payload['venue_id'] = message['venue_id']
    elif message["message_type"] == "url":
        payload['url'] = message["url"]
        if "site_type" in message :
            payload['site_type'] = message['site_type']
        if "site_name" in message:
            payload['site_name'] = message['site_name']
        if "title" in message:
            payload['title'] = message['title']
        if "description" in message:
            payload['description'] = message['description']
    else:
        # TO DO : upload media to s3 here
        file_name = get_filename(message["file_path"])
        logging.info("Uploading to s3 %s", file_name)
        with open(message["file_path"], "rb") as in_file:
            s3_response = s3_client.put_object(
                Body=in_file,
                Bucket=settings.S3_BUCKET,
                Key=file_name,
                ACL='public-read')
        bucket_location = s3_client.get_bucket_location(Bucket=settings.S3_BUCKET)
        payload["url"] = "https://s3-{0}.amazonaws.com/{1}/{2}".format(
                    bucket_location['LocationConstraint'],
                    settings.S3_BUCKET,
                    file_name)
        payload["caption"] = message.get("caption", "")
        # TO DO : remove file if uploaded successfully to s3
        try:
            os.remove(message["file_path"])
        except OSError as e:
            logging.warning("Cannot remove downloaded file {} : ".format(message["file_path"], str(e)))
    
    logging.info(str(payload))
    sendJsonToMoobiDesk(settings.MOOBIDESK_ENDPOINT, '/telegram/incoming', payload)

def send_message_sent_update(message):
    # send message outgoing id/status to Moobidesk
    logging.info("Received message update")
    payload = {
        "phone_from" : message["phone_from"],
        "phone_to" : message["phone_to"],
        "message" : message["message"],
        "status" : message["status"]
    }
    if "message_id" in message:
        payload["message_id"] = message["message_id"]
    if "internal_id" in message:
        payload["internal_id"] = message["internal_id"]
    if "max_id" in message:
        payload["max_id"] = message["max_id"]
    
    logging.info(str(payload))
    sendJsonToMoobiDesk(settings.MOOBIDESK_ENDPOINT, '/telegram/outgoing', payload)

def send_user_update(message):
    # send update : 
    # - Request code has been sent/or not
    # - Sign in success/Failed
    # - Sign up success/Failed
    logging.info("Received user update:")
    payload = {
        "phone_number" : message["phone_number"],
        "message" : message["message"],
        "status" : message["status"]
    }

    logging.info(str(payload))
    sendJsonToMoobiDesk(settings.MOOBIDESK_ENDPOINT, '/telegram/user', payload)


def do_send_request_code(gavriTLManager, message, redisClient):
    msg = gavriTLManager.add_user(phone_norm(message['phone_number']), 
                                    first_name=message.get('first_name'), 
                                    last_name=message.get('last_name', ''),
                                    replace=message.get('force', False))

    response = {
        "phone_number": message['phone_number']
    }
    if msg:
        if 'Request code sent' in msg:
            response["message"] = "Request code has been sent to {}".format(message['phone_number'])
            response["status"] = "Ok"
        else:
            response["message"] = msg
            response["status"] = "Failed"
    else:
        response["message"]  = "User {} already authorized. Use force params to request new session".format(message['phone_number'])
        response["status"] = "Ok"
    
    response['type'] = 'user_update'
    redisClient.publish(settings.REDIS_INCOMING_JOB_QUEUE, json.dumps(response))

def do_sign_in(gavriTLManager, message, redisClient):
    response = {
        "phone_number": message['phone_number']
    }
    client = gavriTLManager.get_user(message['phone_number'])
    if client is None:
        response["message"] = "Request code has not been sent to {}".format(message['phone_number'])
        response["status"] = "Failed"
    else:
        result_code = client.do_sign_in(message['code'], pw=message.get('pw', None))
        if result_code == 0:
            response["message"]  = "User {} sign in failed!".format(message['phone_number'])
            response["status"] = "Failed"
        else:
            response["message"] = "User {} sign in success!".format(message['phone_number'])
            response["status"] = "Ok"
            sleep(0.5)
            # sync contacts
            client.sync_contacts()

    response['type'] = 'user_update'
    redisClient.publish(settings.REDIS_INCOMING_JOB_QUEUE, json.dumps(response))

def do_sign_up(gavriTLManager, message, redisClient):
    response = {
        "phone_number": message['phone_number']
    }
    client = gavriTLManager.get_user(message['phone_number'])
    if client is None:
        response["message"] = "Request code has not been sent to {}".format(message['phone_number'])
        response["status"] = "Failed"
    else:
        error = client.do_sign_up(message['code'], message['first_name'], last_name=message.get('last_name', ''))
        if error is not None:
            response["message"] = "User {} sign up failed! Error : {}".format(message['phone_number'], error)
            response["status"] = "Failed"
        else:
            response["message"] = "User {} sign up success!".format(message['phone_number'])
            response["status"] = "Ok"

    response['type'] = 'user_update'
    redisClient.publish(settings.REDIS_INCOMING_JOB_QUEUE, json.dumps(response))

def do_set_presence(gavriTLManager, message, redisClient):
    response = {}
    client = gavriTLManager.get_user(message['phone_number'])
    if client is None:
        response = {"message":"User {} has not been authorized yet".format(message['phone_number']), "status":"Failed"}
    # else:
    #     error = client.do_sign_up(message['code'], message['first_name'], last_name=message.get('last_name', ''))
    #     if error is not None:
    #         response = {"message":"User {} sign up failed! Error : {}".format(message['phone_number'], error), "status":"Failed"}
    #     else:
    #         response = {"message":"User {} sign up success!".format(message['phone_number']), "status":"Ok"}

    # response['type'] = 'user_update'
    # redisClient.publish(settings.REDIS_INCOMING_JOB_QUEUE, json.dumps(response))

def do_send_text(gavriTLManager, message, redisClient):
    response = {
        "phone_from": message['phone_from'],
        "phone_to": message['phone_to'],
        "internal_id": message['internal_id']
    }
    client = gavriTLManager.get_user(message['phone_from'])
    if client is None:
        response["message"] = "User {} has not been authorized yet".format(message['phone_from'])
        response["status"] = "Failed"
    else:
        message_id = client.send_text_message(message['phone_to'], message['body'], message['first_name'], last_name=message.get('last_name', ''))
        if message_id is None:
            response["message"] = "Failed sent message from {} to {}".format(message['phone_from'], message['phone_to'])
            response["status"] = "Failed"
        else:
            response["message"] = "Success sending message from {} to {}".format(message['phone_from'], message['phone_to'])
            response["message_id"] = message_id
            response["status"] = "Sent"

    response['type'] = 'message_update'
    redisClient.publish(settings.REDIS_INCOMING_JOB_QUEUE, json.dumps(response))

def do_send_media(gavriTLManager, message, redisClient):
    response = {
        "phone_from": message['phone_from'],
        "phone_to": message['phone_to'],
        "internal_id": message['internal_id']
    }
    client = gavriTLManager.get_user(message['phone_from'])
    if client is None:
        response["message"] = "User {} has not been authorized yet".format(message['phone_from'])
        response["status"] = "Failed"
    else:
        if message['media_type'] == "image":
            message_id = client.send_photo(message['file_path'], message['phone_to'], message.get('caption', None), message['first_name'], last_name=message.get('last_name', ''))
        else:
            message_id = client.send_document(message['file_path'], message['phone_to'], message.get('caption', None), message['first_name'], last_name=message.get('last_name', ''))
        
        if message_id is None:
            response["message"] = "Failed sent message from {} to {}".format(message['phone_from'], message['phone_to'])
            response["status"] = "Failed"
        else:
            response["status"] = "Sent"
            response["message"] = "Success sending message from {} to {}".format(message['phone_from'], message['phone_to'])
            response["message_id"] = message_id

    response['type'] = 'message_update'
    redisClient.publish(settings.REDIS_INCOMING_JOB_QUEUE, json.dumps(response))

def do_status_read(gavriTLManager, message, redisClient):
    client = gavriTLManager.get_user(message['phone_number'])
    if client is None:
        logging.info('Error client is None {} in do_status_read'.format(message['phone_number']))
    else:
        client.do_status_read(message['phone_from'], int(message['max_id']))

def stop_incoming_thread(redisClient):
    INCOMING_THREAD_RUN = False
    redisClient.publish(settings.REDIS_INCOMING_JOB_QUEUE, 'done')

def incoming_thread():
    logging.info('Running incoming thread')
    # setup s3 client
    session = boto3.session.Session()
    s3_client = session.client(
        's3',
        aws_access_key_id=settings.S3_ACCESSKEY,
        aws_secret_access_key=settings.S3_SECRETKEY,
    )
    # setup redis client
    redisClient = redis.StrictRedis(host=settings.REDIS_CLIENT_HOST, port=settings.REDIS_CLIENT_PORT, db=0, decode_responses=True)
    redisPubSub = redisClient.pubsub(ignore_subscribe_messages=True)
    redisPubSub.subscribe(settings.REDIS_INCOMING_JOB_QUEUE)
    while INCOMING_THREAD_RUN:
        try:
            message = redisPubSub.get_message()
            if message and message['data'] != 'done':
                obj = message['data']
                if type(obj) is str:
                    obj = json.loads(message['data'])
                if 'type' not in obj:
                    continue
                if obj['type'] == 'incoming':
                    send_incoming_message(obj, s3_client)
                elif obj['type'] == 'message_update':
                    send_message_sent_update(obj)
                elif obj['type'] == 'user_update':
                    send_user_update(obj)
                else:
                    logging.info('Unknown incoming message type: %s', obj['type'])
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(str(e))
        finally:
            sleep(0.001)
    redisPubSub.close()
    logging.info('Incoming thread has been stopped')


if __name__ == "__main__":
    # setup redis client
    redisClient = redis.StrictRedis(host=settings.REDIS_CLIENT_HOST, port=settings.REDIS_CLIENT_PORT, db=0, decode_responses=True)
    redisPubSub = redisClient.pubsub(ignore_subscribe_messages=True)
    redisPubSub.subscribe(settings.REDIS_OUTGOING_JOB_QUEUE)

    from telegram.tl_manager import GavriTLManager
    logging.info('Executing standalone code')
    gavriTLManager = GavriTLManager(settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH, redisClient, session_base_path=settings.TELETHON_SESSIONS_DIR)

    # init authorized clients do automatically sign in
    gavriTLManager.init_users()

    # setup incoming thread
    incomingThread = Thread(target = incoming_thread, args=[])
    incomingThread.start()

    while True:
        try:
            message = redisPubSub.get_message()
            if message:
                obj = message['data']
                if type(obj) is str:
                    obj = json.loads(message['data'])
                if 'type' not in obj:
                    continue
                if obj['type'] == 'request_code' :
                    do_send_request_code(gavriTLManager, obj, redisClient)
                elif obj['type'] == 'sign_in':
                    do_sign_in(gavriTLManager, obj, redisClient)
                elif obj['type'] == 'sign_up':
                    do_sign_up(gavriTLManager, obj, redisClient)
                elif obj['type'] == 'set_presence':
                    do_set_presence(gavriTLManager, obj, redisClient)
                elif obj['type'] == 'send_text':
                    do_send_text(gavriTLManager, obj, redisClient)
                elif obj['type'] == 'send_media':
                    do_send_media(gavriTLManager, obj, redisClient)
                elif obj['type'] == 'status_read':
                    do_status_read(gavriTLManager, obj, redisClient)
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(str(e))
        finally:
            sleep(0.001)

    stop_incoming_thread(redisClient)
    incomingThread.join()
    redisPubSub.close()