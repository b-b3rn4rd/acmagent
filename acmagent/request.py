import json
import acmagent
import logging
import botocore
import botocore.session

logger = logging.getLogger('acmagent')


class Certificate(object):
    """
    acmagent - maps passed cli arguments to the certificate object attributes
    """
    def __init__(self, certificate_attrs):
        try:
            self.domain_name = certificate_attrs['domain_name']
            self.subject_alternative_names = certificate_attrs['subject_alternative_names']
            self.domain_validation_options = certificate_attrs['domain_validation_options']
        except KeyError as e:
            mappings = Certificate._json_mappings()
            map = {'cli': map['cli'] for name, map in mappings.items() if map['attr'] == e.args[0]}
            logger.exception('Missing certificate attribute')
            raise acmagent.MissingCertificateArgException('{} is required'.format(map['cli']))

    @classmethod
    def from_json_input(cls, cli_input_json):
        try:
            mappings = Certificate._json_mappings()
            certificate_attrs = {mappings[k]['attr']: v for k,v in cli_input_json.items()}
            return cls(certificate_attrs)
        except KeyError as e:
            logger.exception('Unknown certificate property')
            raise acmagent.InvalidCertificateJsonFileException('Unknown property {} in the specified json file'.format(e.args[0]))

    @property
    def domain_name(self):
        return self._domain_name

    @domain_name.setter
    def domain_name(self, domain_name):
        self._domain_name = domain_name

    @property
    def subject_alternative_names(self):
        return self._subject_alternative_names

    @subject_alternative_names.setter
    def subject_alternative_names(self, subject_alternative_names):
        self._subject_alternative_names = subject_alternative_names

    @property
    def domain_validation_options(self):
        return self._domain_validation_options

    @domain_validation_options.setter
    def domain_validation_options(self, domain_validation_options):
        acm_domain_validation_options = None

        if domain_validation_options:
            acm_domain_validation_options = [
                {'DomainName': alternative_name, 'ValidationDomain': domain_validation_options}
                for alternative_name in self.subject_alternative_names
            ]
            acm_domain_validation_options.append({
                    'DomainName': self.domain_name,
                    'ValidationDomain': domain_validation_options
            })

        self._domain_validation_options = acm_domain_validation_options

    @staticmethod
    def _json_mappings():
        return {
            'DomainName': {
                'attr': 'domain_name',
                'default': '',
                'cli': '--domain-name'
            },
            'ValidationDomain': {
                'attr': 'domain_validation_options',
                'default': '',
                'cli': '--validation-domain'
            },
            'SubjectAlternativeNames': {
                'attr': 'subject_alternative_names',
                'default': [],
                'cli': '--alternative-names'
            }
        }

    @staticmethod
    def template():
        template = {k: v['default'] for k,v in Certificate._json_mappings().items()}
        return json.dumps(template, sort_keys=True, indent=4, separators=(',', ': '))

    def __iter__(self):
        acm_certificate = {
            'DomainName': self.domain_name
        }

        if self.domain_validation_options:
            acm_certificate['DomainValidationOptions'] = self.domain_validation_options

        if self.subject_alternative_names:
            acm_certificate['SubjectAlternativeNames'] = self.subject_alternative_names

        for k,v in acm_certificate.items():
            yield (k, v)


class RequestCertificate(object):
    """
    Sends actual request to AWS
    """
    def __init__(self):
        self._acm_client = self._setup_acm_client()

    def request_certificate(self, certificate):
        return self._acm_client.request_certificate(**certificate)

    def _setup_acm_client(self):
        session = botocore.session.get_session()
        return session.create_client('acm')
