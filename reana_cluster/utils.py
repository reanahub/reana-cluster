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
            cluster_spec = yaml.load(f.read())

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
