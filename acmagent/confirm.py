import imaplib
import email
from bs4 import BeautifulSoup
import requests
import logging
import acmagent
import json

logger = logging.getLogger('acmagent')


class ConfirmCertificate(object):
    """
    Certificate confirmation class, tried to confirm certificate with given id by connecting to IMAP server
    """
    APPROVAL_URL_ID = 'approval_url'
    APPROVAL_FORM_URL = 'https://certificates.amazon.com/approvals'
    EMAIL_FOLDER = 'Inbox'

    def __enter__(self):
        return self

    def __init__(self, imap_credentials):
        try:
            self._server = imap_credentials['server']
            self._username = imap_credentials['username']
            self._password = imap_credentials['password']
        except TypeError as e:
            logger.exception('IMAP credentials file is not well formatted')
            raise acmagent.InvaliIMAPCredentailsFileException('IMAP credentials file is empty or not well formatted')
        except KeyError as e:
            logger.exception('IMAP credentials missing property')
            raise acmagent.IMAPCredentialFileMissingPropertyException(
                'Missing IMAP property "{}", check the credentials file'.format(e.args[0]))

        self._connect_to_imap()

    def _connect_to_imap(self):
        try:
            logger.info('Establishing connection with {} server'.format(self._server))
            self._mail = imaplib.IMAP4_SSL(self._server)
            self._mail.login(self._username, self._password)
        except Exception as e:
            logger.exception('Failed establish IMAP connection: {}'.format(e))
            raise acmagent.SMTPConnectionFailedException('Can\'t login to the "{}" server'.format(self._server))

    @staticmethod
    def _search_query(certificate_id):
        search_query = (
            'UNSEEN',
            'FROM "Amazon Certificates"',
            'BODY "Certificate identifier: {}"'.format(certificate_id)
        )

        return "({})".format(" ".join(search_query))

    def _call_confirm_url(self, url):
        logger.info('Sending GET: {}'.format(url))
        response = requests.get(url, headers=acmagent.UserHeaders)

        try:
            confirm_body = BeautifulSoup(response.content, "html.parser")
            confirm_form = confirm_body.body.find('form').find_all('input')
            payload = {input.get('name'): input.get('value') for input in confirm_form}
            logger.debug('Found confirmation form: {}'.format(json.dumps(payload)))
            return self._call_confirm_form(payload)
        except AttributeError as e:
            logger.exception('Failed to extract confirmation form')
            raise acmagent.ConfirmPageIsMissingFormException('The certificate has been confirmed or the confirmation link: "{}" has expired'.format(url))

    def _call_confirm_form(self, payload):
        logger.info('Sending POST: {} PAYLOAD: {}'.format(ConfirmCertificate.APPROVAL_FORM_URL, json.dumps(payload)))
        response = requests.post(ConfirmCertificate.APPROVAL_FORM_URL, headers=acmagent.UserHeaders, data=payload)

        if not response.ok:
            logger.exception('Failed to submit confirmation form')
            raise acmagent.ACManagerException('An unknown error has occurred while requesting url:"{}"'.format(ConfirmCertificate.APPROVAL_FORM_URL))

        logger.info('Success! The certificate has been confirmed')
        return True

    def _fetch_message(self, message_id):
        type, response = self._mail.fetch(message_id,'(RFC822)')
        email_message = email.message_from_string(response[0][1])
        logger.debug('Opening email: {}'.format(email_message['subject']))
        self._mail.store(message_id, '+FLAGS', '\\Seen')
        logger.debug('Marking email: {} as read'.format(email_message['subject']))
        email_body = ''
        if email_message.is_multipart():
            for multipart in email_message.get_payload():
                if 'text/html' == multipart.get_content_type():
                    email_body = multipart.get_payload(decode=True)
                    break
        if not email_body:
            logger.exception('Email is missing HTML')
            raise acmagent.EmailBodyUnknownContentType('Email "{}" is not in the text/html Content-Type'.format(message_id))

        try:
            logger.debug('Reading email: {} HTML body'.format(email_message['subject']))
            html = BeautifulSoup(email_body, "html.parser")
            approval_url = html.body.find('a', attrs={'id': ConfirmCertificate.APPROVAL_URL_ID}).get('href')
            logger.debug('Found confirmation url: {}'.format(approval_url))
            return self._call_confirm_url(approval_url)
        except AttributeError as e:
            logger.exception('Failed to parse email html')
            raise acmagent.EmailBodyConfirmLinkIsMissingException('Url with "id={}" is not found in the email'.format(ConfirmCertificate.APPROVAL_URL_ID))

    def confirm_certificate(self, certificate_id):
        try:
            self._mail.select(ConfirmCertificate.EMAIL_FOLDER)
            imap_search = ConfirmCertificate._search_query(certificate_id)
            logger.debug('Scan {} folder with {} condition'.format(ConfirmCertificate.EMAIL_FOLDER, imap_search))
            success, messages = self._mail.search(None, imap_search)
            if success == 'OK':
                message_ids = [message_id for message_id in messages[0].split(' ') if message_id]

                if not message_ids:
                    logger.info('Have not found email for requested certificate')
                    raise acmagent.NoEmailsFoundException('Failed to find email for certificate {} in {} folder'.format(
                        certificate_id, ConfirmCertificate.EMAIL_FOLDER))

                logger.debug('Found {} email(s)'.format(len(message_ids)))
                for message_id in message_ids:
                    success = self._fetch_message(message_id)
                    if success:
                        return True
            else:
                logger.exception('Unknown error')
                raise acmagent.ACManagerException('An unknown error has occurred while reading emails, state={}'.format(success))
        except imaplib.IMAP4.error as e:
            if str(e).startswith('FETCH'):
                raise acmagent.FailedToFetchEmailException('Failed to fetch emails')
            elif str(e).startswith('command EXAMINE illegal'):
                raise acmagent.SMTPConnectionFailedException('Can\'t establish connection with "{}" server'.format(self._server))

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info('Closing connection with {} server'.format(self._server))
        self._mail.close()
