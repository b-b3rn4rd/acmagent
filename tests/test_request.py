import unittest
import json
import acmagent
import mock
from botocore.stub import Stubber
import botocore.session
from acmagent import request


class TestCertificate(unittest.TestCase):
    def setUp(self):
        self.domain_name = 'test.example.com'
        self.subject_alternative_names = ['dev.example.com']
        self.subject_no_alternative_names = []
        self.domain_validation_options = 'example.com'
        self.no_domain_validation_options = None

        self.expected_certificate_with_alternative_names = {
            'DomainName': self.domain_name,
            'SubjectAlternativeNames': self.subject_alternative_names,
            'DomainValidationOptions': [
                {
                    'DomainName': self.subject_alternative_names[0],
                    'ValidationDomain': self.domain_validation_options
                },
                {
                    'DomainName': self.domain_name,
                    'ValidationDomain': self.domain_validation_options
                }
            ]
        }
        self.expected_certificate_wo_alternative_names = {
            'DomainName': self.domain_name,
            'DomainValidationOptions': [
                {
                    'DomainName': self.domain_name,
                    'ValidationDomain': self.domain_validation_options
                }
            ]
        }

        self.expected_certificate_with_only_domain_name = {
            'DomainName': self.domain_name
        }

    def test_certificate_transformation_with_domain_name_only(self):
        certificate = request.Certificate({
            'domain_name': self.domain_name,
            'subject_alternative_names': self.subject_no_alternative_names,
            'domain_validation_options': self.no_domain_validation_options
        })

        certificate_actual_dict = dict(certificate)

        self.assertDictEqual(self.expected_certificate_with_only_domain_name, certificate_actual_dict)

    def test_certificate_transformation_with_alternative_names(self):
        certificate = request.Certificate({
            'domain_name': self.domain_name,
            'subject_alternative_names': self.subject_alternative_names,
            'domain_validation_options': self.domain_validation_options
        })

        certificate_actual_dict = dict(certificate)

        self.assertDictEqual(self.expected_certificate_with_alternative_names, certificate_actual_dict)

    def test_certificate_transformation_wo_alternative_names(self):
        certificate = request.Certificate({
            'domain_name': self.domain_name,
            'subject_alternative_names': self.subject_no_alternative_names,
            'domain_validation_options': self.domain_validation_options
        })

        certificate_actual_dict = dict(certificate)
        self.assertDictEqual(self.expected_certificate_wo_alternative_names, certificate_actual_dict)

    def test_certificate_transformation_using_json_with_alternative_names(self):
        json_input = {
            'DomainName': self.domain_name,
            'ValidationDomain': self.domain_validation_options,
            'SubjectAlternativeNames': self.subject_alternative_names
        }

        certificate = request.Certificate.from_json_input(json_input)
        certificate_actual_dict = dict(certificate)
        self.assertDictEqual(self.expected_certificate_with_alternative_names, certificate_actual_dict)

    def test_certificate_transformation_using_json_wo_alternative_names(self):
        json_input = {
            'DomainName': self.domain_name,
            'ValidationDomain': self.domain_validation_options,
            'SubjectAlternativeNames': self.subject_no_alternative_names
        }

        certificate = request.Certificate.from_json_input(json_input)
        certificate_actual_dict = dict(certificate)
        self.assertDictEqual(self.expected_certificate_wo_alternative_names, certificate_actual_dict)

    def test_certificate_transformation_using_json_triggers_exception_if_properties_are_missing(self):
        json_input = {
            'DomainName': self.domain_name,
            'ValidationDomain': self.domain_validation_options
        }

        with self.assertRaises(acmagent.MissingCertificateArgException) as context:
            request.Certificate.from_json_input(json_input)

    def test_certificate_transformation_using_json_triggers_exception_if_unkown_property_is_given(self):
        json_input = {
            'DomainName': self.domain_name,
            'ValidationDomain': self.domain_validation_options,
            'blabla': False
        }

        with self.assertRaises(acmagent.InvalidCertificateJsonFileException) as context:
            request.Certificate.from_json_input(json_input)

    def test_certificate_template_method_returns_required_structure(self):
        string = request.Certificate.template()
        certificate_template = json.loads(string)
        certificate_template_expected = {
            'DomainName': '',
            'ValidationDomain': '',
            'SubjectAlternativeNames': []
        }
        self.assertDictEqual(certificate_template_expected, certificate_template)


class TestRequestCertificate(unittest.TestCase):
    def test_certificate_is_valid_for_boto3_request_certificate_method(self):
        certificate = request.Certificate({
            'domain_name': 'www.example.com',
            'domain_validation_options': 'example.com',
            'subject_alternative_names': []
        })

        certificate_params = dict(certificate)

        certificate_acm_params = {
            'DomainName': 'www.example.com',
            'DomainValidationOptions': [{
                'DomainName': 'www.example.com',
                'ValidationDomain': 'example.com'
            }]
        }

        request_certificate = request.RequestCertificate()

        response = {
            'CertificateArn': 'arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012'
        }

        with Stubber(request_certificate._acm_client) as stubber:
            stubber.add_response('request_certificate', response, certificate_acm_params)
            acm_response = request_certificate.request_certificate(certificate_params)

        self.assertDictEqual(acm_response, response)


if __name__ == '__main__':
    unittest.main()
