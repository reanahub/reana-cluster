# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018, 2019 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA cluster client configuration."""

import pkg_resources

from reana_cluster.backends.kubernetes import KubernetesBackend

cluster_spec_default_file_path = pkg_resources.resource_filename(
    'reana_cluster', 'configurations/reana-cluster-minikube.yaml')
"""REANA cluster specification file default location."""

generated_cluster_conf_default_path = './cluster_config/'
"""Default location to output configuration files for REANA cluster backend."""

cluster_spec_schema_file_path = pkg_resources.resource_filename(
    'reana_cluster', 'schemas/reana-cluster.json')
"""REANA cluster specification schema location."""

traefik_configuration_file_path = pkg_resources.resource_filename(
    'reana_cluster', 'configurations/helm/traefik/minikube.yaml')
"""Traefik configuration schema location."""

supported_backends = {
    'kubernetes': KubernetesBackend,
}
"""Dictionary to extend REANA cluster with new cluster backend."""

reana_env_exportable_info_components = ['reana-server']
"""Components which information will be produced by ``reana-client env``."""

reana_cluster_ready_necessary_components = ['workflow-controller',
                                            'message-broker',
                                            'server']
"""Components which must be running for the cluster status to be ready."""

traefik_release_name = 'reana-traefik'
"""Name used for traefik deployment."""

DEFAULT_REANA_DB_SECRET_NAME = 'reana-db-secrets'
"""Default name for REANA DB Kubernetes secrets object."""

DEFAULT_REANA_DB_USER = 'reana'
"""Default name for REANA DB user name."""

DEFAULT_REANA_CERN_SSO_SECRET_NAME = 'reana-cern-sso-secrets'
"""Default name for CERN SSO Kubernetes secrets object."""

DEFAULT_REANA_CERN_GITLAB_SECRET_NAME = 'reana-cern-gitlab-secrets'
"""Default name for CERN GitLab Kubernetes secrets object."""

DEFAULT_REANA_SECRETS_LIST = [
    DEFAULT_REANA_DB_SECRET_NAME,
    DEFAULT_REANA_CERN_SSO_SECRET_NAME,
    DEFAULT_REANA_CERN_GITLAB_SECRET_NAME
]
"""Default secrets required by default."""
