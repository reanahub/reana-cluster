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

import yaml
from jsonschema import ValidationError, validate

from .config import cluster_spec_schema_file_path


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

    https_port = _discover_https_port(ports)
    if https_port and not insecure:
        scheme = 'https'
        port = https_port
    else:
        scheme = 'http'
        port = ports[0]

    return '{scheme}://{host}:{port}'.format(
        scheme=scheme, host=host, port=port)
