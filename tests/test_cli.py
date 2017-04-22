import unittest
from acmagent import cli
from mock import patch
from mock import MagicMock
import urllib2
import argparse
import json
import yaml
import acmagent
from acmagent import confirm
from acmagent import request


def SystemExitStub(status=0, message=None):
    """
    system exit stub
    """

    exit(status)


class NamespaceStub(object):
    """
    argprase namespace stub
    """

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)


class ResponseStub(object):
    """
    urllib2 stub
    """

    def __init__(self, filename):
        self.response = filename

    def read(self):
        return self.response


class Urllib2ExceptionStub(object):
    """
    urllib2 exception stub
    """
    def __init__(self, filename):
        self.response = filename

    def read(self):
        raise urllib2.URLError(self.response)

    def __str__(self):
        return self.response


class TestParseJsonInput(unittest.TestCase):
    def setUp(self):
        self.json_string = '{"name": "test"}'
        self.namespace_stub = NamespaceStub()

    @patch("urllib2.urlopen")
    def test_ParseJsonInput_object_sets_json_content_for_cli_input_json_arg(self, urllib2_mock):
        urllib2_mock.side_effect = ResponseStub
        parser_mock = MagicMock()
        cli_input = cli.ParseJsonInput([], 'cli_input_json')
        cli_input(parser_mock, self.namespace_stub, self.json_string, '--cli-input-json')

        self.assertDictEqual(json.loads(self.json_string), self.namespace_stub.cli_input_json)

    @patch("urllib2.urlopen")
    def test_file_is_not_readable_when_urllib2_URLError_exception_is_raised(self, urllib2_mock):
        urllib2_mock.side_effect = Urllib2ExceptionStub
        parser_mock = MagicMock()
        cli_input = cli.ParseJsonInput([], 'cli_input_json')
        cli_input(parser_mock, self.namespace_stub, 'file://input.json', '--cli-input-json')
        parser_mock.error.assert_called_once()
        called_args = parser_mock.error.call_args
        error_message = called_args[0][0]
        assert error_message.endswith('is not readable')

    @patch("urllib2.urlopen")
    def test_file_is_missing_protocol_when_Value_exception_is_raised(self, urllib2_mock):
        urllib2_mock.side_effect = ValueError
        parser_mock = MagicMock()
        cli_input = cli.ParseJsonInput([], 'cli_input_json')
        cli_input(parser_mock, self.namespace_stub, 'input.json', '--cli-input-json')
        parser_mock.error.assert_called_once()
        called_args = parser_mock.error.call_args
        error_message = called_args[0][0]
        assert error_message.endswith('missing file URL scheme')

    @patch("urllib2.urlopen")
    def test_file_is_not_valid_json__when_Value_exception_is_raised(self, urllib2_mock):
        urllib2_mock.side_effect = ValueError
        parser_mock = MagicMock()
        cli_input = cli.ParseJsonInput([], 'cli_input_json')
        cli_input(parser_mock, self.namespace_stub, 'file://input.json', '--cli-input-json')
        parser_mock.error.assert_called_once()
        called_args = parser_mock.error.call_args
        error_message = called_args[0][0]
        assert error_message.endswith('is not valid json')


class TestParseIMAPCredentials(unittest.TestCase):
    def setUp(self):
        self.yaml_string = """
server: imap.example.com
username: user@example.com
password: mypassword
"""
        self.namespace_stub = NamespaceStub()

    @patch("urllib2.urlopen")
    def test_ParseIMAPCredentials_sets_imap_credentials_from_yaml_to_credentials_arg(self, urllib2_mock):
        urllib2_mock.side_effect = ResponseStub
        parser_mock = MagicMock()
        cli_input = cli.ParseIMAPCredentials([], 'credentials')
        cli_input(parser_mock, self.namespace_stub, self.yaml_string, '--credentials')

        self.assertDictEqual(yaml.load(self.yaml_string), self.namespace_stub.credentials)

    @patch("urllib2.urlopen")
    def test_file_is_not_readable_when_urllib2_URLError_exception_is_raised(self, urllib2_mock):
        urllib2_mock.side_effect = Urllib2ExceptionStub
        parser_mock = MagicMock()
        cli_input = cli.ParseIMAPCredentials([], 'credentials')
        cli_input(parser_mock, self.namespace_stub, 'file://creds.yaml', '--credentials')

        parser_mock.error.assert_called_once()
        called_args = parser_mock.error.call_args
        error_message = called_args[0][0]
        assert error_message.endswith('is not readable')

    @patch("urllib2.urlopen")
    def test_file_is_missing_protocol_when_Value_exception_is_raised(self, urllib2_mock):
        urllib2_mock.side_effect = ValueError
        parser_mock = MagicMock()

        cli_input = cli.ParseIMAPCredentials([], 'credentials')
        cli_input(parser_mock, self.namespace_stub, 'creds.yaml', '--credentials')

        parser_mock.error.assert_called_once()
        called_args = parser_mock.error.call_args
        error_message = called_args[0][0]
        assert error_message.endswith('missing file URL scheme')

    @patch("urllib2.urlopen")
    def test_file_is_not_valid_json__when_Value_exception_is_raised(self, urllib2_mock):
        urllib2_mock.side_effect = ValueError
        parser_mock = MagicMock()

        cli_input = cli.ParseIMAPCredentials([], 'credentials')
        cli_input(parser_mock, self.namespace_stub, 'file://creds.yaml', '--credentials')

        parser_mock.error.assert_called_once()
        called_args = parser_mock.error.call_args
        error_message = called_args[0][0]
        assert error_message.endswith('is not valid YAML')


class TestConfirmCert(unittest.TestCase):
    """
    Tests for confirm_cert function
    """

    def setUp(self):
        self.certificate_id = 'test'
        self.credentials = None
        self.wait = 5
        self.attempts=1
        self.server = 'imap.example.com'
        self.username = 'user@example.com'
        self.password = 'mypassword'

    @patch("acmagent.cli.confirm.ConfirmCertificate")
    @patch("acmagent.load_imap_credentials")
    @patch("time.sleep")
    def test_confirm_cert_exists_with_error_if_email_not_found(self, sleep_mock, load_imap_credentials_mock, confirm_certificate_mock):

        args = NamespaceStub(certificate_id=self.certificate_id,
            credentials=self.credentials,
            attempts=self.attempts,
            wait=self.wait)

        parser_mock = MagicMock()

        confirm_certificate_mock.return_value.__enter__.return_value.confirm_certificate.side_effect = acmagent.NoEmailsFoundException('exception')
        cli._confirm_cert(args, parser_mock)
        parser_mock.error.assert_called_once_with('exception')

    @patch("acmagent.cli.confirm.ConfirmCertificate")
    @patch("acmagent.load_imap_credentials")
    @patch("time.sleep")
    def test_confirm_cert_function_happy_path(self, sleep_mock, load_imap_credentials_mock, confirm_certificate_mock):

        args = NamespaceStub(certificate_id=self.certificate_id,
            credentials=self.credentials,
            attempts=self.attempts,
            wait=self.wait)

        parser_mock = MagicMock()

        load_imap_credentials_mock.return_value = {
            'server': self.server,
            'username': self.username,
            'password': self.password,
        }

        confirm_certificate_mock.return_value.__enter__.return_value.confirm_certificate.return_value = True
        cli._confirm_cert(args, parser_mock)

        # sleep is called with wait param
        sleep_mock.assert_called_once_with(self.wait)

        # credentials are loaded from load_imap_credentials function
        load_imap_credentials_mock.assert_called_once()

        # exit code is 0 with success error message
        parser_mock.exit.assert_called_once_with(0, "Success: certificate has been confirmed\n")

        # __enter__ method is called
        confirm_certificate_mock.return_value.__enter__.assert_called_once()

        # confirm certificate method is called
        confirm_certificate_mock.return_value.__enter__.return_value.confirm_certificate.assert_called_once_with(self.certificate_id)

        # __exit__ method is called
        confirm_certificate_mock.return_value.__exit__.assert_called_once()


class TestRequestCert(unittest.TestCase):
    """
    Tests for the _request_cert function
    """
    def setUp(self):
        self.domain_name = 'www.example.com'
        self.subject_alternative_names = 'ftp.example.com'
        self.domain_validation_options = 'example.com'
        self.generate_cli_skeleton = False
        self.cli_input_json = False
        self.certificate_arn = 'arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012'

    @patch("acmagent.cli.request.RequestCertificate")
    def test_request_cert_generates_skeleton_when_generate_cli_skeleton_is_set(self, request_certificate_mock):
        args = NamespaceStub(generate_cli_skeleton=True)
        parser_mock = MagicMock()
        parser_mock.exit.side_effect = SystemExitStub

        with self.assertRaises(SystemExit):
            cli._request_cert(args, parser_mock)

        parser_mock.exit.assert_called_once_with(0, request.Certificate.template() + "\n")

    @patch("acmagent.cli.request.RequestCertificate")
    def test_request_cert_happy_path(self, request_certificate_mock):
        args = NamespaceStub(domain_name=self.domain_name,
            subject_alternative_names=self.subject_alternative_names,
            domain_validation_options=self.domain_validation_options,
            generate_cli_skeleton=False,
            cli_input_json=False
        )
        parser_mock = MagicMock()

        certificate = dict(request.Certificate(args.__dict__))
        request_certificate_mock.return_value.request_certificate.return_value = {
            'CertificateArn': self.certificate_arn
        }
        cli._request_cert(args, parser_mock)

        # request_certificate method was called with certificate
        certificate_id = self.certificate_arn.split('/')[-1]
        request_certificate_mock.return_value.request_certificate.assert_called_once_with(certificate)
        parser_mock.exit.assert_called_once_with(0, "{}\n".format(certificate_id))


class TestArguments(unittest.TestCase):
    @patch("acmagent.cli.argparse.ArgumentParser.exit")
    def test_version_argument_uses_setup_file_value(self, argparse_mock):
        parser = cli._setup_argparser()
        parser.parse_args(['--version'])
        argparse_mock.assert_any_call(message=acmagent.VERSION+'\n')


if __name__ == '__main__':
    unittest.main()