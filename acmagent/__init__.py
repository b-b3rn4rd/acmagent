import logging
import os
import yaml
from logging.handlers import RotatingFileHandler


VERSION = '1.0.2'


def load_imap_credentials(file='.acmagent'):
    home = os.path.expanduser('~')
    filename = '{}/{}'.format(home, file)

    try:
        with open(filename, 'r') as ymlfile:
            return yaml.load(ymlfile)
    except IOError as e:
        raise MissingIMAPCredentailsException('IMAP credentials file: {} is not found'.format(filename))
    except yaml.scanner.ScannerError as e:
        raise InvalidIMAPCredentailsFileException('IMAP credentials file: {} is not valid YAML'.format(filename))


def _create_log_filename(filename):
    if os.name == 'nt':
        logdir = os.path.expandvars(r'${SystemDrive}\cfn\log')
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        return logdir + os.path.sep + filename

    return '/tmp/%s' % filename


def add_stream_log_handler(logger):
    """
    Add StreamHandler to the logger

    :param logger: existing logger
    :return: None
    """
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
    logger.addHandler(handler)


def add_file_log_handler(logger, name):
    """
    Add RotatingFileHandler to the logger

    :param logger: existing logger
    :param name: filename
    :return: None
    """
    handler = RotatingFileHandler(
        backupCount=3, maxBytes=1000000, filename=_create_log_filename('{}.log'.format(name))
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
    logger.addHandler(handler)


def configure_logger(name):
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)

    return logger


class ACManagerException(Exception):
    """Basic ACManager exception"""


class MissingIMAPCredentailsException(ACManagerException):
    """Missing IMAP credentails file"""


class InvalidIMAPCredentailsFileException(ACManagerException):
    """IMAP credentails file is not valid YAML"""


class MissingCertificateArgException(ACManagerException):
    """Missing required CLI argument exception"""


class IMAPCredentialFileMissingPropertyException(ACManagerException):
    """IMAP credential file is missing required property"""


class InvalidCertificateJsonFileException(ACManagerException):
    """Missing required CLI argument exception"""


class SMTPConnectionFailedException(ACManagerException):
    """Raised when failed to establish connection with SMTP server"""


class FailedToFetchEmailException(SMTPConnectionFailedException):
    """Raised when failed to fetch email"""


class NoEmailsFoundException(ACManagerException):
    """Raised when emails are not found"""


class EmailBodyUnknownContentType(ACManagerException):
    """Raised when certificate body is not in html format"""


class EmailBodyConfirmLinkIsMissingException(ACManagerException):
    """Raised when certificate email is missing confirmation url"""


class ConfirmPageIsMissingFormException(ACManagerException):
    """Raised when confirm page is missing the actual form"""

UserHeaders = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}
