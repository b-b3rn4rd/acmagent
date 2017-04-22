from __future__ import print_function
import os
import sys
import argparse
import json
import urllib2
import time
import yaml
import acmagent
import pkg_resources
from acmagent import request
from acmagent import confirm


logger = acmagent.configure_logger('acmagent')

class ParseJsonInput(argparse.Action):
    """
    Parse json input file for the request-certificate command
    """
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(ParseJsonInput, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        try:
            logger.debug('Opening input json file'.format(value))
            certificate_args = json.loads(urllib2.urlopen(value).read())
            setattr(namespace, self.dest, certificate_args)
        except urllib2.URLError:
            logger.exception('Failed reading json input')
            parser.error('Specified file "{}" is not readable'.format(value))
        except ValueError:
            if not value.startswith('file:'):
                logger.exception('Input json file is missing file scheme')
                parser.error('Specified file "{}" is missing file URL scheme'.format(value))
            else:
                logger.exception('Input json file is not valid json')
                parser.error('Specified file "{}" is not valid json'.format(value))


class ParseIMAPCredentials(argparse.Action):
    """
    Parse YAML IMAP credentials file for the confirm-certificate command
    """
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(ParseIMAPCredentials, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        try:
            logger.debug('Opening IMAP credentials file'.format(value))
            imap_credentials = yaml.load(urllib2.urlopen(value).read())
            setattr(namespace, self.dest, imap_credentials)
        except urllib2.URLError as e:
            logger.exception('Failed reading json input')
            parser.error('Specified file "{}" is not readable'.format(value))
        except ValueError as e:
            if not value.startswith('file:'):
                logger.exception('Input json file is missing file scheme')
                parser.error('Specified file "{}" is missing file URL scheme'.format(value))
            else:
                logger.exception('Input json file is not valid YAML')
                parser.error('Specified file "{}" is not valid YAML'.format(value))


def _confirm_cert(args, parser):
    """
    Confirm ACM issued certificate

    :param args: cli arguments
    :return: None
    """
    try:
        imap_credentials = args.credentials if args.credentials else acmagent.load_imap_credentials()
        with confirm.ConfirmCertificate(imap_credentials) as acm_certificate_confirm:
            attempts_left = args.attempts
            while attempts_left:
                logger.debug('Starting ACM request for {} certificate, attempts left: {}, pause: {} seconds'.format(
                    args.certificate_id, attempts_left, args.wait))
                attempts_left -= 1
                time.sleep(args.wait)
                try:
                    success = acm_certificate_confirm.confirm_certificate(args.certificate_id)
                    if success:
                        parser.exit(0, 'Success: certificate has been confirmed\n')
                except acmagent.NoEmailsFoundException as e:
                    if attempts_left:
                        continue
                    parser.error(str(e))
                except acmagent.ACManagerException as e:
                    parser.error(str(e))
    except acmagent.ACManagerException as e:
        parser.error(str(e))


def _request_cert(args, parser):
    """
    Send a request to the ACM to issue SSL certificate

    :param args: cli arguments
    :return: None
    """
    if args.generate_cli_skeleton:
        json_file = request.Certificate.template()
        logger.debug('Generating json input file: {}'.format(json_file))
        parser.exit(0, "{}\n".format(json_file))

    if args.cli_input_json:
        try:
            certificate = request.Certificate.from_json_input(args.cli_input_json)
            acm_certificate = dict(certificate)
        except acmagent.InvalidCertificateJsonFileException as e:
            parser.error(str(e))
    else:
        if not args.domain_name:
            parser.error('--domain-name is required')

        certificate = request.Certificate(args.__dict__)
        acm_certificate = dict(certificate)

    acm_certificate_request = request.RequestCertificate()

    try:
        logger.debug('Requesting certificate: {}'.format(json.dumps(acm_certificate)))
        response = acm_certificate_request.request_certificate(acm_certificate)
    except Exception as e:
        logger.exception('Boto3 exception')
        parser.error(str(e))

    certificate_id = (response['CertificateArn'].split('/')[-1])
    logger.debug('Success, {} certificate was issued, id: {}'.format(acm_certificate['DomainName'], certificate_id))
    parser.exit(0, "{}\n".format(certificate_id))


def _setup_argparser():
    """
    Argparse factory

    :return: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description='ACM agent')
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=pkg_resources.get_distribution("acmagent").version,
        help='print acmagent version'
    )

    subparsers = parser.add_subparsers(
        title='ACM agent - automates ACM certificates',
        description='ACM agents provides functionality to request and confirm ACM certificates using the CLI interface')

    request_cert_parser = subparsers.add_parser('request-certificate')
    request_cert_parser.set_defaults(func=_request_cert)
    request_cert_parser.add_argument('--domain-name',
        dest='domain_name',
        required=False,
        help='Fully qualified domain name (FQDN), such as www.example.com')
    request_cert_parser.add_argument('--validation-domain',
        dest='domain_validation_options',
        required=False,
        help='The domain name that you want ACM to use to send you emails to validate your ownership of the domain')
    request_cert_parser.add_argument('--alternative-names',
        default=[],
        dest='subject_alternative_names',
        required=False,
        nargs='+',
        help='Additional FQDNs to be included in the Subject Alternative Name extension of the ACM Certificate')
    request_cert_parser.add_argument('--generate-cli-skeleton',
        required=False,
        action='store_true',
        default=False,
        dest='generate_cli_skeleton',
        help='(boolean) Prints a sample input JSON  to  standard output')

    request_cert_parser.add_argument('--cli-input-json',
        required=False,
        action=ParseJsonInput,
        dest='cli_input_json',
        help='(boolean) Prints a sample input JSON  to  standard output')

    request_cert_parser.add_argument('--debug',
        required=False,
        action='store_true',
        default=False,
        help='(boolean) Send logging to standard output')

    confirm_cert_parser = subparsers.add_parser('confirm-certificate')
    confirm_cert_parser.set_defaults(func=_confirm_cert)
    confirm_cert_parser.add_argument('--certificate-id',
        dest='certificate_id',
        required=True,
        help='Certificate id')
    confirm_cert_parser.add_argument('--wait',
        dest='wait',
        default=5,
        type=int,
        required=False,
        help='Timeout in seconds between querying IMAP server')
    confirm_cert_parser.add_argument('--attempts',
        dest='attempts',
        type=int,
        default=1,
        required=False,
        help='Number of attempts to query IMAP server')

    confirm_cert_parser.add_argument('--debug',
        required=False,
        action='store_true',
        default=False,
        help='(boolean) Send logging to standard output')

    confirm_cert_parser.add_argument('--credentials',
        required=False,
        action=ParseIMAPCredentials,
        help='Explicitly provide IMAP credentials file')

    return parser


def main():
    is_debug = '--debug' in sys.argv[1:]

    if is_debug:
        acmagent.add_stream_log_handler(logger)
    else:
        acmagent.add_file_log_handler(logger, 'acmagent')

    parser = _setup_argparser()
    args = parser.parse_args()
    args.func(args, parser)

if __name__ == "__main__":
    main()
