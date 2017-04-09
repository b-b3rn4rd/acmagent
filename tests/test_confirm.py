import unittest
import json
import acmagent
import imaplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from acmagent import confirm
from mock import patch
import mock


class CertificateFailedApprovalFormStub(object):
    def __init__(self, url, headers, data):
        self.ok = False

class CertificateApprovalFormStub(object):
    def __init__(self, url, headers, data):
        self.ok = True

class CertificateExpiredApprovalPageStub(object):
    def __init__(self, url, headers):
        self.content = """\
        <html>
            <body>
                <p></p>
            </body>
        </html>
        """

class CertificateApprovalPageStub(object):
    def __init__(self, url, headers):
        self.content = """\
        <html>
            <body>
                <form>
                    <input type="input" name="test_input" value="test_value" />
                </form>
            </body>
        </html>
        """


class TestConfirmCertificate(unittest.TestCase):
    def setUp(self):
        self.server = 'imap.example.com'
        self.username = 'test@example.com'
        self.password = 'my_imap_password'
        self.certificate_id = '12345678-1234-1234-1234-123456789012'
        self.email_id = '1'
        self.approval_url = 'test.com'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Link"
        msg['From'] = 'admin@example.com'
        msg['To'] = 'user@example.com'
        html = """\
        <html>
          <head></head>
          <body>
            <a href="{}" id="approval_url"></a>
          </body>
        </html>
        """.format(self.approval_url)
        msg.attach(MIMEText(html, 'html'))

        self.email_body = str(msg)

    @patch("imaplib.IMAP4_SSL")
    def test_confirm_certificate_connects_to_imap_using_provided_credentials(self, imap_mock):
        confirm_certificate = confirm.ConfirmCertificate({
            'server': self.server,
            'username': self.username,
            'password': self.password
        })
        confirm_certificate._mail.login.assert_called_once_with(self.username, self.password)

    @patch("acmagent.confirm.requests.get", side_effect=CertificateApprovalPageStub)
    @patch("acmagent.confirm.requests.post", side_effect=CertificateApprovalFormStub)
    @patch("imaplib.IMAP4_SSL")
    def test_confirm_certificate_happy_path(self, imap_mock, post_mock, get_mock):
        confirm_certificate = confirm.ConfirmCertificate({
            'server': self.server,
            'username': self.username,
            'password': self.password
        })
        confirm_certificate._mail.search.return_value = ('OK', [self.email_id])
        confirm_certificate._mail.fetch.return_value = ('OK', [['', self.email_body]])

        # successful request returns True
        self.assertTrue(confirm_certificate.confirm_certificate(self.certificate_id))

        # specific IMAP folder was selected
        confirm_certificate._mail.select.assert_called_once_with(confirm.ConfirmCertificate.EMAIL_FOLDER)

        # message were searched using expected search query
        confirm_certificate._mail.search.assert_called_once_with(None, confirm.ConfirmCertificate._search_query(self.certificate_id))

        # message was fetched
        confirm_certificate._mail.fetch.assert_called_once_with(self.email_id, '(RFC822)')

        # message was marked as read
        confirm_certificate._mail.store.assert_called_once_with(self.email_id, '+FLAGS', '\\Seen')

        # confirm url was requested using GET
        get_mock.assert_called_once_with(self.approval_url, headers=acmagent.UserHeaders)

        # confirm form was requested using POST
        post_mock.assert_called_once_with(confirm.ConfirmCertificate.APPROVAL_FORM_URL, headers=acmagent.UserHeaders, data={
            'test_input': 'test_value'
        })

    @patch("imaplib.IMAP4_SSL")
    def test_confirm_certificate_raises_exception_if_email_is_not_found(self, imap_mock):
        confirm_certificate = confirm.ConfirmCertificate({
            'server': self.server,
            'username': self.username,
            'password': self.password
        })
        confirm_certificate._mail.search.return_value = ('OK', [''])
        with self.assertRaises(acmagent.NoEmailsFoundException):
            confirm_certificate.confirm_certificate(self.certificate_id)    \

    @patch("imaplib.IMAP4_SSL")
    def test_confirm_certificate_raises_exception_if_email_is_not_html(self, imap_mock):
        confirm_certificate = confirm.ConfirmCertificate({
            'server': self.server,
            'username': self.username,
            'password': self.password
        })

        confirm_certificate._mail.search.return_value = ('OK', [self.email_id])
        confirm_certificate._mail.fetch.return_value = ('OK', [['', '']])

        with self.assertRaises(acmagent.EmailBodyUnknownContentType):
            confirm_certificate.confirm_certificate(self.certificate_id)

    @patch("imaplib.IMAP4_SSL")
    def test_confirm_certificate_raises_exception_if_email_is_missing_confirmation_url(self, imap_mock):
        confirm_certificate = confirm.ConfirmCertificate({
            'server': self.server,
            'username': self.username,
            'password': self.password
        })

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Link"
        msg['From'] = 'admin@example.com'
        msg['To'] = 'user@example.com'
        html = """\
        <html>
          <head></head>
          <body></body>
        </html>
        """.format(self.approval_url)
        msg.attach(MIMEText(html, 'html'))

        email_with_missing_approval_url = str(msg)

        confirm_certificate._mail.search.return_value = ('OK', [self.email_id])
        confirm_certificate._mail.fetch.return_value = ('OK', [['', email_with_missing_approval_url]])

        with self.assertRaises(acmagent.EmailBodyConfirmLinkIsMissingException):
            confirm_certificate.confirm_certificate(self.certificate_id)

    @patch("acmagent.confirm.requests.get", side_effect=CertificateExpiredApprovalPageStub)
    @patch("imaplib.IMAP4_SSL")
    def test_confirm_certificate_raises_exception_if_confirmation_page_is_missing_form(self, imap_mock, get_mock):
        confirm_certificate = confirm.ConfirmCertificate({
            'server': self.server,
            'username': self.username,
            'password': self.password
        })

        confirm_certificate._mail.search.return_value = ('OK', [self.email_id])
        confirm_certificate._mail.fetch.return_value = ('OK', [['', self.email_body]])

        with self.assertRaises(acmagent.ConfirmPageIsMissingFormException):
            confirm_certificate.confirm_certificate(self.certificate_id)


    @patch("acmagent.confirm.requests.get", side_effect=CertificateApprovalPageStub)
    @patch("acmagent.confirm.requests.post", side_effect=CertificateFailedApprovalFormStub)
    @patch("imaplib.IMAP4_SSL")
    def test_confirm_certificate_raises_exception_if_form_submission_failed(self, imap_mock, post_mock, get_mock):
        confirm_certificate = confirm.ConfirmCertificate({
            'server': self.server,
            'username': self.username,
            'password': self.password
        })

        confirm_certificate._mail.search.return_value = ('OK', [self.email_id])
        confirm_certificate._mail.fetch.return_value = ('OK', [['', self.email_body]])

        with self.assertRaises(acmagent.ACManagerException):
            confirm_certificate.confirm_certificate(self.certificate_id)

if __name__ == '__main__':
    unittest.main()