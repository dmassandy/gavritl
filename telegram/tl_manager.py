import os
import hashlib
from time import sleep
from django.core.exceptions import ObjectDoesNotExist
from telethon import TelegramClient
from telethon.utils import find_user_or_chat
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import (UpdateShortChatMessage, UpdateShortMessage, User, InputPeerUser, InputUser,
                                InputPhoneContact, UpdatesTg, UpdateContactLink, PeerUser, UpdateNewMessage)

from telethon.tl.functions.contacts import GetContactsRequest, ImportContactsRequest
from telethon.tl.types.contacts import Contacts, ImportedContacts
from telethon.tl.functions.users import GetUsersRequest
from telethon.errors import (PhoneNumberInvalidError, PhoneCodeEmptyError, PhoneCodeExpiredError, PhoneCodeInvalidError, FirstNameInvalidError, LastNameInvalidError)

from django.conf import settings
from .models import TLUser, TLContact
from .utils import phone_norm,phone_number_only
import logging


def bytes_to_string(byte_count):
    """Converts a byte count to a string (in KB, MB...)"""
    suffix_index = 0
    while byte_count >= 1024:
        byte_count /= 1024
        suffix_index += 1

    return '{:.2f}{}'.format(byte_count,
                             [' bytes', 'KB', 'MB', 'GB', 'TB'][suffix_index])

class GavriTLClient(TelegramClient):
    def __init__(self, api_id, api_hash, phone_number,
                proxy=None, session_base_path=None, user_media_base_path=None):
        session_user_id = phone_number.replace('+','')
        logging.info('Initializing GavriTLClient %s', phone_number)
        super().__init__(session_user_id, api_id, api_hash, proxy=proxy, session_base_path=session_base_path)
        self.user_phone =  phone_number
        self.user_media_base_path = user_media_base_path
        logging.info('Connecting to Telegram servers...')
        self.is_success_connect = True
        if not self.connect():
            logging.info('Initial connection failed. Retrying...')
            if not self.connect():
                logging.info('Could not connect to Telegram servers. %s', phone_number)
                self.is_success_connect = False
                return
        if self.is_success_connect:
            self.add_update_handler(self.update_handler)
    
    def do_sign_in(self, code, pw=None):
        """ Do sign in with code and password if needed
            Return values 0 : failed sign in, 1 : normal sign in, 2 : sign in with password
        """
        self_user = None
        result_code = 0
        try:
            self_user = self.sign_in(self.user_phone, code)
            result_code = 1 if self_user is not None else 0
        # Two-step verification may be enabled
        except SessionPasswordNeededError:
            logging.info('Two step verification is enabled for %s. Sign in with password.', self.user_phone)

            self_user = self.sign_in(password=pw)
            result_code = 2 if self_user is not None else 0

        # save state user
        logging.info(self_user)
        userModel = None
        try:
            userModel = TLUser.objects.get(phone=self.user_phone)
            userModel.state = 'authorized' if result_code != 0 and self_user != None else 'unauthorized'
            if self_user is not None:
                userModel.username = self_user.username
                userModel.user_id = self_user.id
                userModel.access_hash = self_user.access_hash
            userModel.save()
        except ObjectDoesNotExist:
            logging.info('No user in db %s', self.user_phone)

        return result_code

    def do_sign_up(self, code, first_name, last_name=''):
        """ Do sign in with code and password if needed
            Return values 0 : failed sign in, 1 : normal sign in, 2 : sign in with password
        """
        self_user = None
        signup_error = None
        try:
            self.sign_up(self.user_phone, code, first_name, last_name)
            self_user = self.session.user
        except (PhoneNumberInvalidError, PhoneCodeEmptyError, PhoneCodeExpiredError, 
                PhoneCodeInvalidError, FirstNameInvalidError, LastNameInvalidError) as err:
            logging.error("Error signup : %s", err.message)
            signup_error = err.message

        # save state user
        logging.info(self_user)
        userModel = None
        try:
            userModel = TLUser.objects.get(phone=self.user_phone)
            userModel.state = 'authorized' if self_user != None else 'unauthorized'
            if self_user is not None:
                userModel.username = self_user.username
                userModel.user_id = self_user.id
                userModel.access_hash = self_user.access_hash
            userModel.save()
        except ObjectDoesNotExist:
            logging.info('No user in db %s', self.user_phone)

        return signup_error
    
    def get_or_create_new_contact(self, phone, first_name, last_name=None):
        contactModel = None
        try:
            contactModel = TLContact.objects.get(owner=self.user_phone,phone=phone)
        except ObjectDoesNotExist:
            logging.info('No contact exits in %s, adding new contact %s', self.user_phone, phone)
            inputContact = InputPhoneContact(0, phone, first_name, '' if last_name is None else last_name)
            result = self.invoke(ImportContactsRequest([inputContact], True))
            logging.info(result)
            if type(result) is ImportedContacts and len(result.users) > 0 :
                logging.info('New contact added : {}'.format(str(len(result.users))))
                for user in result.users:
                    if type(user) is User:
                        contact = TLContact(owner=self.user_phone,phone=phone_norm(user.phone),
                                            username=user.username,first_name=user.first_name,last_name=user.last_name,
                                            access_hash=user.access_hash,user_id=user.id)
                        contact.save()
                        contactModel = contact
            sleep(0.5)

        return contactModel

    def send_text_message(self, to, body, first_name, last_name=None):
        contactModel = self.get_or_create_new_contact(to, first_name, last_name=last_name)
        if contactModel is None:
            return None
        
        peer_user = InputPeerUser(int(contactModel.user_id), int(contactModel.access_hash))
        msg_id = self.send_message(peer_user, body, no_web_page=True)
        logging.info('Send message id {}'.format(msg_id))
        return msg_id

    def send_photo(self, path, to, caption, first_name, last_name=None):
        contactModel = self.get_or_create_new_contact(to, first_name, last_name=last_name)
        if contactModel is None:
            return None
        
        peer_user = InputPeerUser(int(contactModel.user_id), int(contactModel.access_hash))

        logging.info('Uploading {}...'.format(path))
        input_file = self.upload_file(
            path, progress_callback=self.upload_progress_callback)

        # After we have the handle to the uploaded file, send it to our peer
        msg_id = self.send_photo_file(input_file, peer_user, caption=caption)
        logging.info('Photo sent!')
        logging.info('Send message id {}'.format(msg_id))
        return msg_id
    
    def send_document(self, path, to, caption, first_name, last_name=None):
        contactModel = self.get_or_create_new_contact(to, first_name, last_name=last_name)
        if contactModel is None:
            return None
        
        peer_user = InputPeerUser(int(contactModel.user_id), int(contactModel.access_hash))

        logging.info('Uploading {}...'.format(path))
        input_file = self.upload_file(
            path, progress_callback=self.upload_progress_callback)

        # After we have the handle to the uploaded file, send it to our peer
        msg_id = self.send_document_file(input_file, peer_user, caption=caption)
        logging.info('Document sent!')
        logging.info('Send message id {}'.format(msg_id))
        return msg_id

    def sync_contacts(self):
        contact_hash = ""
        contacts = TLContact.objects.filter(owner=self.user_phone).order_by('user_id')
        if contacts is not None and len(contacts) > 0:
            for contact in contacts:
                contact_hash = contact_hash + contact.user_id + ","
            contact_hash = contact_hash[:-1]
            contact_hash = hashlib.md5(contact_hash.encode('utf-8')).hexdigest()

        logging.info('Sync contact hash :  {}...'.format(contact_hash))
        result = self.invoke(GetContactsRequest(contact_hash))
        # logging.info(result)
        if type(result) is Contacts and len(result.users) > 0 :
            logging.info('New contact added : {}'.format(str(len(result.users))))
            for user in result.users:
                if type(user) is User:
                    contact = TLContact(owner=self.user_phone,phone=phone_norm(user.phone),
                                        username=user.username,first_name=user.first_name,last_name=user.last_name,
                                        access_hash=user.access_hash,user_id=user.id)
                    contact.save()

    @staticmethod
    def download_progress_callback(downloaded_bytes, total_bytes):
        GavriTLClient.print_progress('Downloaded',
                                                 downloaded_bytes, total_bytes)

    @staticmethod
    def upload_progress_callback(uploaded_bytes, total_bytes):
        GavriTLClient.print_progress('Uploaded', uploaded_bytes,
                                                 total_bytes)

    @staticmethod
    def print_progress(progress_type, downloaded_bytes, total_bytes):
        logging.info('{} {} out of {} ({:.2%})'.format(progress_type, bytes_to_string(
            downloaded_bytes), bytes_to_string(total_bytes), downloaded_bytes /
                                                total_bytes))

    def update_handler(self, update_object):
        logging.info('{} received update: {}'.format(self.user_phone, type(update_object).__name__))
        logging.info(str(update_object))
        new_messages = []
        if type(update_object) is UpdateShortMessage:
            # ignore outgoint chat
            if update_object.out:
                logging.info('You sent {} to user #{}'.format(
                    update_object.message, update_object.user_id))
            else:
                logging.info('[User #{} sent {}]'.format(
                    update_object.user_id, update_object.message))
                m = {}
                m['type'] = 'text'
                m['id'] = str(update_object.id)
                m['from'] = update_object.user_id
                m['to'] = self.user_phone
                m['body'] = update_object.message
                new_messages.append(m)

        elif type(update_object) is UpdateShortChatMessage:
            #ignore group chat
            if update_object.out:
                logging.info('You sent {} to chat #{}'.format(
                    update_object.message, update_object.chat_id))
            else:
                logging.info('[Chat #{}, user #{} sent {}]'.format(
                       update_object.chat_id, update_object.from_id,
                       update_object.message))
        elif type(update_object) is UpdatesTg:
            new_contacts = []
            media_list = []
            logging.info('UpdatesTg updates count %s', str(len(update_object.updates)))
            for update in update_object.updates:
                if type(update) is UpdateContactLink:
                    new_contacts.append(update.user_id)
                elif type(update) is UpdateNewMessage:
                    logging.info('update new message')
                    if update.message.out: # pass if our outgoing message
                        continue
                    if type(update.message.to_id) is not PeerUser: #ignore if to group chat
                        continue
                    if getattr(update.message, 'media', None):
                        # media message, auto download
                        logging.info('media')
                        media_list.append(update.message)
                        # The media may or may not have a caption
                        # caption = getattr(update.message.media, 'caption', '')
                    elif hasattr(update.message, 'message'):
                        # chat normal message
                        logging.info('message text')
                        m = {}
                        m['type'] = 'text'
                        m['id'] = str(update.message.id)
                        m['from'] = update.message.from_id
                        m['to'] = self.user_phone
                        m['body'] = update.message.message
                        new_messages.append(m)
                    else:
                        # Unknown message, simply print its class name
                        content = type(update.message).__name__
                        logging.info('Received unknown message type {} - ID={}'.format(content, update.message.id))
            if len(new_contacts) > 0 :
                logging.info('New contact added : {}'.format(str(len(new_contacts))))
                for user in update_object.users:
                    if type(user) is User and user.id in new_contacts:
                        # check if there is existing record or not
                        isContactExist = TLContact.objects.filter(owner=self.user_phone,phone=phone_norm(user.phone)).exists()
                        if not isContactExist:
                            contact = TLContact(owner=self.user_phone,phone=phone_norm(user.phone),
                                            username=user.username,first_name=user.first_name,last_name=user.last_name,
                                            access_hash=user.access_hash,user_id=user.id)
                            contact.save()
            
            if len(media_list) > 0 :
                logging.info('Media message to download: {}'.format(str(len(media_list))))
                # download media
                for msg in media_list:
                    output = phone_number_only(self.user_phone) + "_" + str(msg.id)
                    output = os.path.join(settings.TELETHON_USER_MEDIA_DIR, output)
                    logging.info('Downloading media to {}...'.format(output))
                    output = self.download_msg_media(
                        msg.media,
                        file_path=output,
                        progress_callback=self.download_progress_callback)
                    logging.info('Media downloaded to {}!'.format(output))
                    m = {}
                    m['type'] = 'media'
                    m['id'] = str(msg.id)
                    m['from'] = msg.from_id
                    m['to'] = self.user_phone
                    m['caption'] = getattr(msg.media, 'caption', '')
                    m['file_path'] = output
                    new_messages.append(m)

        for new_message in new_messages:
            # get from phone number
            contactModel = None
            try:
                contactModel = TLContact.objects.get(owner=self.user_phone,user_id=new_message['from'])
            except ObjectDoesNotExist:
                logging.error("Cannot find contact with user id %s.", new_message['from'])
                
            new_message['from'] = contactModel.phone
            logging.info(str(new_message))

        # handle TG containing : contact update, sent media

class GavriTLManager():
    def __init__(self, api_id, api_hash, session_base_path=None):
        self.tl_clients = {}
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_base_path = session_base_path

    def add_user(self, phone_number, first_name=None, last_name=None):
        if phone_number in self.tl_clients:
            return 'User already added'
        client = GavriTLClient(self.api_id, self.api_hash, phone_number, session_base_path = self.session_base_path)
        logging.info('Is Success connect : %s', client.is_success_connect)
        if client.is_success_connect:
            me_obj = client.get_me()
            is_authorized = client.session and me_obj is not None
            logging.info('Is Client Authorized : %s', is_authorized)
            logging.info(me_obj)
            self.tl_clients[phone_number] = client

            # add/update user
            userModel = None
            try:
                userModel = TLUser.objects.get(phone=phone_number)
            except ObjectDoesNotExist:
                pass
            user_state = 'authorized' if is_authorized else 'request-code sent'
            if userModel:
                userModel.isConnected = True
                userModel.state = user_state
                if me_obj:
                    userModel.access_hash = me_obj.access_hash
                    userModel.user_id = me_obj.id
                    userModel.username = me_obj.username
                userModel.save()
            else:
                userModel = TLUser(phone=phone_number, state=user_state, isConnected=True, 
                                first_name=first_name, last_name=last_name)
                if me_obj:
                    userModel.access_hash = me_obj.access_hash
                    userModel.user_id = me_obj.id
                    userModel.username = me_obj.username
                userModel.save()

            if not is_authorized:
                # need to request code
                client.send_code_request(phone_number)
                return 'Request code sent by SMS. Please sign in using the code.'
            return None
        else:
            return 'Failed adding user: Cannot connect to Telegram servers'

    def get_user(self, phone_number):
        if phone_number in self.tl_clients:
            return self.tl_clients[phone_number]
        
        return None

    def disconnect_user(self, phone_number):
        if phone_number in self.tl_clients:
            self.tl_clients[phone_number].disconnect()
            del self.tl_clients[phone_number]
            return None
        
        return 'User does not Exist.'
