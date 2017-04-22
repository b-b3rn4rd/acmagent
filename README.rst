.. image:: https://travis-ci.org/b-b3rn4rd/acmagent.svg?branch=master
    :target: https://travis-ci.org/b-b3rn4rd/acmagent

.. image:: https://coveralls.io/repos/github/b-b3rn4rd/acmagent/badge.svg?branch=master
    :target: https://coveralls.io/github/b-b3rn4rd/acmagent?branch=master


======================================
ACMagent - automates ACM certificates
======================================
ACM agents provides functionality to request and confirm ACM certificates using the CLI interface

Installation
############

::

    $ pip install acmagent


Configuration
#############
In order to approve ACM certificates, create and configure acmagent IMAP credentials file. By default ``acmagent`` loads configuration ``.acmagent`` file from the user's home folder for example: `/home/john.doe/.acmagent`. However, you have an option to specify a custom path to the credentials file.

::

    # /home/john.doe/.acmagent

    username: username@example.com
    server: imap.example.com
    password: mysecretpassword

Usage
#####

Issuing ACM certificates
------------------------

The simplest option to request ACM certificate is to specify ``--domain-name`` and/or ``--validation-domain`` parameters.

::

    $ acmagent request-certificate --domain-name *.dev.example.com
    12345678-1234-1234-1234-123456789012


::

    $ acmagent request-certificate --domain-name *.dev.example.com --validation-domain example.com
    12345678-1234-1234-1234-123456789012


Optionally, if you need to generate a certificate for multiple domain names you can provide the ``--alternative-names`` parameter to specify **space separated** alternative domain names.

::

    $ acmagent request-certificate --domain-name dev.example.com --validation-domain example.com --alternative-names  www.dev.example.com ftp.dev.example.com
    12345678-1234-1234-1234-123456789012

ACMAgent offers an option to specify JSON input file instead of typing them at the command line using ``--cli-input-json`` parameter.

- Generate CLI skeleton output

::

    $ acmagent request-certificate --generate-cli-skeleton &> certificate.json


::

    $ cat certificate.json
    {
        "DomainName": "",
        "SubjectAlternativeNames": [],
        "ValidationDomain": ""
    }


- Modify generated skeleton file using your preferred method
- Using ``--cli-input-json`` parameter specify path fo the ``certificate.json`` file

::

    $ acmagent request-certificate --cli-input-json file:./certificate.json


**Output**

The `request-certificate` outputs ACM certificate id, it's the last part of the ARN arn:aws:acm:us-east-1:123456789012:certificate/**12345678-1234-1234-1234-123456789012** you will need that id for a certificate approval process.

Approving ACM certificates
--------------------------

*Before approving ACM issued certificate, please ensure that the credentials file has been setup.*
*For gmail and yahoo enable access for 'less secure apps' (https://support.google.com/accounts/answer/6010255?hl=en-GB&authuser=1)*

confirm-certificate
^^^^^^^^^^^^^^^^^^^

::

    $ acmagent confirm-certificate --help
    usage: acmagent confirm-certificate [-h] --certificate-id CERTIFICATE_ID
                                    [--wait WAIT] [--attempts ATTEMPTS]
                                    [--debug] [--credentials CREDENTIALS]
    optional arguments:
    -h, --help                      show this help message and exit
    --certificate-id CERTIFICATE_ID Certificate id
    --wait WAIT                     Timeout in seconds between querying IMAP server
    --attempts ATTEMPTS             Number of attempts to query IMAP server
    --debug (boolean)               Send logging to standard output
    --credentials CREDENTIALS       Explicitly provide IMAP credentials file

Examples
^^^^^^^^
Confirming a certificate using the default settings:

::

    $ acmagent confirm-certificate --certificate-id 12345678-1234-1234-1234-123456789012


However, for most scenarios the recommended approach to specify custom values for ``--wait`` and ``--attempts`` parameters tailored for your IMAP server.

::

    $ acmagent confirm-certificate --wait 10 --attempts 6 --certificate-id 12345678-1234-1234-1234-123456789012


In the situations when you can't use the default IMAP credentials file provide the ``--credentials`` parameter

::

    $ acmagent confirm-certificate --certificate-id 12345678-1234-1234-1234-123456789012 --credentials file:///var/lib/jenkins/.acmagent


