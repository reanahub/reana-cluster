# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA cluster utils."""

import json
import logging
import random
import string
import subprocess
import sys
from getpass import getpass

import yaml
from jsonschema import ValidationError, validate

from reana_cluster.config import (DEFAULT_REANA_CERN_GITLAB_SECRET_NAME,
                                  DEFAULT_REANA_CERN_SSO_SECRET_NAME,
                                  DEFAULT_REANA_DB_SECRET_NAME,
                                  DEFAULT_REANA_DB_USER,
                                  DEFAULT_REANA_SECRETS_LIST,
                                  cluster_spec_schema_file_path)


def load_spec_file(filepath, skip_validation=False):
    """Load and validate REANA cluster specification file.

    :param filepath: Filepath where to load REANA cluster spec file.
    :param skip_validation: If set, loaded specifications is not validated
        against schema
    :raises IOError: Error reading REANA cluster spec file from given filepath.
    :raises ValidationError: Given REANA cluster spec file does not validate
        against REANA cluster specification schema.
    """
    try:
        with open(filepath) as f:
            cluster_spec = yaml.load(f.read(), Loader=yaml.FullLoader)

        if not (skip_validation):
            logging.info('Validating REANA cluster specification file: {0}'
                         .format(filepath))
            if _validate_cluster_spec(cluster_spec):
                logging.info('{0} is a valid REANA cluster specification.'
                             .format(filepath))

        return cluster_spec
    except IOError as e:
        logging.info(
            'Something went wrong when reading specifications file from '
            '{filepath} : \n'
            '{error}'.format(filepath=filepath, error=e.strerror))
        raise e
    except Exception as e:
        raise e


def _validate_cluster_spec(cluster_spec):
    """Validate REANA cluster specification file according to jsonschema.

    :param cluster_spec: Dictionary representing REANA cluster spec file.
    :raises ValidationError: Given REANA cluster spec file does not validate
        against REANA cluster specification schema.
    """
    try:
        with open(cluster_spec_schema_file_path, 'r') as f:
            cluster_spec_schema = json.loads(f.read())

            validate(cluster_spec, cluster_spec_schema)

    except IOError as e:
        logging.info(
            'Something went wrong when reading REANA cluster validation '
            'schema from {filepath} : \n'
            '{error}'.format(filepath=cluster_spec_schema_file_path,
                             error=e.strerror))
        raise e
    except ValidationError as e:
        logging.info('Invalid REANA cluster specification: {error}'
                     .format(error=e.message))
        raise e

    return True


def build_component_url(host, ports, insecure=False):
    """Build component URL, choosing the right URI scheme.

    :param host: Host domain name or ip.
    :type host: str
    :param ports: List of possible ports where to contact the host.
    :type ports: list of strings
    :param insecure: Whether to use an insecure URI scheme or not.
    :type insecure: bool
    :returns: Full URL to the component.
    :rtype: str
    """
    def _discover_https_port(ports):
        https_ports = [443, 30443]
        https_port_index = None
        for https_port in https_ports:
            try:
                https_port_index = ports.index(https_port)
            except ValueError:
                continue
        return ports[https_port_index] if https_port_index else None

    ports.sort()
    https_port = _discover_https_port(ports)
    if https_port and not insecure:
        scheme = 'https'
        port = https_port
    else:
        scheme = 'http'
        port = ports[0]

    return '{scheme}://{host}:{port}'.format(
        scheme=scheme, host=host, port=port)


def is_secret_created(secret_name):
    """Check if the secret is created."""
    try:
        cmd = 'kubectl describe secret {0}'.format(secret_name)
        result = subprocess.check_output(cmd, shell=True,
                                         stderr=subprocess.STDOUT)
        output = result.decode('utf-8')
        if secret_name in output:
            return True
    except subprocess.CalledProcessError as err:
        logging.info('Secret {0} does not exist:'
                     ' {1}'.format(secret_name, err))
        return False


def create_secret(secret_name, secrets_mapping):
    """Create a Kubernetes secret."""
    try:
        cmd = 'kubectl create secret generic  {}'.format(secret_name)
        for key, value in secrets_mapping.items():
            cmd += ' --from-literal={0}={1}'.format(key, value)
        result = subprocess.check_output(cmd, shell=True)
        logging.info(result)
    except subprocess.CalledProcessError as err:
        logging.error('Secret {0} could not be created:'
                      ' {1}'.format(secret_name, err))
        sys.exit(err.returncode)


def create_reana_db_secret(secret_name, interactive):
    """Create a REANA DB secret with defaults."""
    user = ''
    password = ''
    if interactive:
        msg = 'Please enter the user for the DB, if ' \
              'left empty default will be used ({}): '.format(
                  DEFAULT_REANA_DB_USER)
        user = input(msg)
        msg = 'Please enter the password for the DB, if ' \
              'left empty it will be autogenerated: '
        password = getpass(prompt=msg)
    secrets_mapping = {
        'user': user or DEFAULT_REANA_DB_USER,
        'password': password or generate_password()
    }
    create_secret(secret_name, secrets_mapping)


def create_reana_cern_sso_secret(secret_name, interactive):
    """Create secrets for the CERN SSO integration."""
    cern_consumer_key = 'sso-client-id'
    cern_consumer_secret = ''
    if interactive:
        msg = 'Please enter the CERN consumer key for SSO, if ' \
              'left empty default will be used ({}): '.format(
                  cern_consumer_key)
        cern_consumer_key = input(msg) or cern_consumer_key
        msg = 'Please enter CERN SSO consumer secret, if ' \
              'left empty it will be autogenerated: '
        cern_consumer_secret = getpass(prompt=msg)

    secrets_mapping = {
        'CERN_CONSUMER_KEY': cern_consumer_key,
        'CERN_CONSUMER_SECRET': cern_consumer_secret or generate_password()
    }
    create_secret(secret_name, secrets_mapping)


def create_reana_cern_gitlab_secret(secret_name, interactive):
    """Create secrets for the CERN SSO integration."""
    gitlab_oauth_app_id = 'gitlab-oauth-app-id'
    gitlab_oauth_app_secret = ''
    gitlab_host = 'gitlab.cern.ch'
    if interactive:
        msg = 'Please enter the GitLab OAuth application ID, if ' \
              'left empty default will be used ({}): '.format(
                  gitlab_oauth_app_id)
        gitlab_oauth_app_id = input(msg) or gitlab_oauth_app_id
        msg = 'Please enter GitLab OAuth application secret, if ' \
              'left empty it will be autogenerated: '
        gitlab_oauth_app_secret = getpass(prompt=msg)
        msg = 'Please enter the GitLab host, if ' \
              'left empty default will be used ({}): '.format(
                  gitlab_host)
        gitlab_host = input(msg) or gitlab_host

    secrets_mapping = {
        'REANA_GITLAB_OAUTH_APP_ID': gitlab_oauth_app_id,
        'REANA_GITLAB_OAUTH_APP_SECRET':
        gitlab_oauth_app_secret or generate_password(),
        'REANA_GITLAB_HOST': gitlab_host
    }
    create_secret(secret_name, secrets_mapping)


def delete_reana_secrets():
    """Delete all REANA secrets."""
    try:
        for secret in DEFAULT_REANA_SECRETS_LIST:
            if is_secret_created(secret):
                cmd = 'kubectl delete secret  {}'.format(secret)
                result = subprocess.check_output(cmd, shell=True)
                logging.info(result)
    except subprocess.CalledProcessError as err:
        logging.error('Secret {0} could not be deleted:'
                      ' {1}'.format(secret, err))
        sys.exit(err.returncode)


def generate_password():
    """Generate a password."""
    password_length = 20
    chars = (string.ascii_lowercase + string.ascii_uppercase + string.digits)
    password = ''
    for _ in range(password_length):
        password += random.choice(chars)
    return password


def check_needed_secrets_are_created(interactive=False):
    """Check if the needed secrets are created, it can autogenerate them."""
    create_reana_secret = {
        DEFAULT_REANA_DB_SECRET_NAME: create_reana_db_secret,
        DEFAULT_REANA_CERN_SSO_SECRET_NAME: create_reana_cern_sso_secret,
        DEFAULT_REANA_CERN_GITLAB_SECRET_NAME: create_reana_cern_gitlab_secret
    }

    for secret_name, create_func in create_reana_secret.items():
        secret_exists = is_secret_created(secret_name)
        if not secret_exists:
            create_func(secret_name, interactive)
