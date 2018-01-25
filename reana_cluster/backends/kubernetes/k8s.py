# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017 CERN.
#
# REANA is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# REANA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# REANA; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.
"""Abstract Base Class representing REANA cluster backend."""

import json
import logging

import pkg_resources
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from kubernetes import client as k8s_client
from kubernetes import config as k8s_config
from kubernetes.client import configuration
from kubernetes.client.rest import ApiException
from pkg_resources import parse_version

from reana_cluster import ReanaBackendABC


class KubernetesBackend(ReanaBackendABC):
    """A class for interacting with Kubernetes.

    Attributes:
        __cluster_type  Type of the backend this class implements support for.
        _conf   Configuration.

    """

    __cluster_type = 'Kubernetes'

    _conf = {
        'templates_folder': pkg_resources.resource_filename(
            __name__, '/templates'),
        'min_version': 'v1.6.4',
        'max_version': 'v1.6.4',
    }

    def __init__(self,
                 cluster_spec,
                 cluster_conf=None,
                 kubeconfig=None,
                 context=None):
        """Initialise Kubernetes specific ReanaBackend-object.

        :param cluster_spec: Dictionary representing complete REANA
            cluster spec file.

        :param cluster_conf: A generator/iterable of Kubernetes YAML manifests
            of REANA components as Python objects. If set to `None`
            cluster_conf will be generated from manifest templates in
            `templates` folder specified in `_conf.templates_folder`

        :param kubeconfig: Name of the kube-config file to use for configuring
            reana-cluster. If set to `None` then `$HOME/.kube/config` will be
            used.
            Note: Might pickup a config-file defined in $KUBECONFIG as well.

        :param context: set the active context. If is set to `None`,
            current_context from config file will be used.

        """
        logging.debug('Creating a ReanaBackend object '
                      'for Kubernetes interaction.')

        # Load Kubernetes cluster configuration. If reana-cluster.yaml
        # doesn't specify this K8S Python API defaults to '$HOME/.kube/config'
        if kubeconfig is None:
            kubeconfig = cluster_spec['cluster'].get('config', None)

        if context is None:
            context = cluster_spec['cluster'].get('config_context', None)

        k8s_config.load_kube_config(kubeconfig, context)

        # Instantiate clients for various Kubernetes REST APIs
        self._corev1api = k8s_client.CoreV1Api()
        self._versionapi = k8s_client.VersionApi()
        self._extbetav1api = k8s_client.ExtensionsV1beta1Api()

        self.cluster_spec = cluster_spec
        self.cluster_conf = cluster_conf or \
                            self.generate_configuration(cluster_spec)  # noqa

    @property
    def cluster_type(self):
        """."""
        return self.__cluster_type

    @property
    def cluster_url(self):
        """Return URL of Kubernetes instance `reana-cluster` connects to."""
        return configuration.host

    @property
    def current_config(self):
        """Return Kubernetes configuration (e.g. `~/.kube/config`)."""
        return configuration

    @classmethod
    def generate_configuration(cls, cluster_spec):
        """Generate Kubernetes manifest files used to init REANA cluster.

        :param cluster_spec: Dictionary representing complete REANA
            cluster spec file.

        :return: A generator/iterable of generated Kubernetes YAML manifests
            as Python objects.
        """
        # Setup an Environment for Jinja
        env = Environment(
            loader=FileSystemLoader(
                cls._conf['templates_folder']),
            keep_trailing_newline=False
        )

        # Define where are backend conf params needed when rendering templates.
        be_conf_params_fp = cls._conf['templates_folder'] + '/config.yaml'

        try:
            with open(be_conf_params_fp) as f:

                # Load backend conf params
                backend_conf_parameters = yaml.load(f.read())

                # Would it be better to combine templates or populated
                # templates in Python code for improved extensibility?
                # Just drop a .yaml template and add necessary to config.yaml
                # without changing anything?

                # Load template combining all other templates from
                # templates folder
                template = env.get_template('backend_conf.yaml')

                components = cluster_spec['components']
                rs_img = components['reana-server']['image']
                rjc_img = components['reana-job-controller']['image']
                rwfc_img = components['reana-workflow-controller']['image']
                rwm_img = components['reana-workflow-monitor']['image']
                rmb_img = components['reana-message-broker']['image']
                rwe_img = components['reana-workflow-engine-yadage']['image']

                rs_environment = components['reana-server']\
                    .get('environment', [])
                rjc_environment = components['reana-job-controller'] \
                    .get('environment', [])
                rwfc_environment = components['reana-workflow-controller'] \
                    .get('environment', [])
                rwm_environment = components['reana-workflow-monitor'] \
                    .get('environment', [])
                rmb_environment = components['reana-message-broker'] \
                    .get('environment', [])
                rwe_environment = components['reana-workflow-engine-yadage'] \
                    .get('environment', [])

                rs_mountpoints = components['reana-server']\
                    .get('mountpoints', [])
                rjc_mountpoints = components['reana-job-controller']\
                    .get('mountpoints', [])
                rwfc_mountpoints = components['reana-workflow-controller']\
                    .get('mountpoints', [])
                rwm_mountpoints = components['reana-workflow-monitor'] \
                    .get('mountpoints', [])
                rmb_mountpoints = components['reana-message-broker'] \
                    .get('mountpoints', [])
                rwe_mountpoints = components['reana-workflow-engine-yadage'] \
                    .get('mountpoints', [])

                # Render the template using given backend config parameters
                cluster_conf = template.\
                    render(backend_conf_parameters,
                           SERVER_IMAGE=rs_img,
                           JOB_CONTROLLER_IMAGE=rjc_img,
                           WORKFLOW_CONTROLLER_IMAGE=rwfc_img,
                           WORKFLOW_MONITOR_IMAGE=rwm_img,
                           MESSAGE_BROKER_IMAGE=rmb_img,
                           WORKFLOW_ENGINE_IMAGE=rwe_img,
                           RS_MOUNTPOINTS=rs_mountpoints,
                           RJC_MOUNTPOINTS=rjc_mountpoints,
                           RWFC_MOUNTPOINTS=rwfc_mountpoints,
                           RWM_MOUNTPOINTS=rwm_mountpoints,
                           RMB_MOUNTPOINTS=rmb_mountpoints,
                           RWE_MOUNTPOINTS=rwe_mountpoints,
                           RS_ENVIRONMENT=rs_environment,
                           RJC_ENVIRONMENT=rjc_environment,
                           RWFC_ENVIRONMENT=rwfc_environment,
                           RWM_ENVIRONMENT=rwm_environment,
                           RMB_ENVIRONMENT=rmb_environment,
                           RWE_ENVIRONMENT=rwe_environment,
                           )

                # Strip empty lines for improved readability
                cluster_conf = '\n'.join(
                    [line for line in cluster_conf.splitlines() if
                     line.strip()])

                # Should print the whole configuration in a loop
                # Now prints just memory address of generator object
                logging.debug('Loaded K8S config successfully: \n {}'
                              .format(yaml.load_all(cluster_conf)))

        except TemplateNotFound as e:
            logging.info(
                'Something wrong when fetching K8S config file templates from '
                '{filepath} : \n'
                '{error}'.format(
                    filepath=cls._conf['templates_folder'],
                    error=e.strerror))
            raise e

        except IOError as e:
            logging.info(
                'Something wrong when reading K8S config parameters-file from '
                '{filepath} : \n'
                '{error}'.format(filepath=be_conf_params_fp,
                                 error=e.strerror))
            raise e

        # As Jinja rendered string is basically multiple YAML documents in one
        # string parse it with YAML-library and return a generator containing
        # independent YAML documents (split from `---`) as Python objects.
        return yaml.load_all(cluster_conf)

    def init(self):
        """Initialize REANA cluster, i.e. deploy REANA components to backend.

        :return: `True` if init was completed successfully.
        :rtype: bool

        :raises ApiException: Failed to successfully interact with
            Kubernetes REST API. Reason for failure is indicated as HTTP error
            codes in addition to a textual description of the error.

        """
        if not self._cluster_running():
            pass

        # Should check that cluster is not already initialized.
        # Maybe use `verify_components()` or `get()` each component?

        for manifest in self.cluster_conf:
            try:

                logging.debug(json.dumps(manifest))

                if manifest['kind'] == 'Deployment':

                    # REANA Job Controller needs access to K8S-cluster's
                    # service-account-token in order to create new Pods.
                    if manifest['metadata']['name'] == 'job-controller':
                        manifest = self._add_service_acc_key_to_jc(manifest)

                    self._extbetav1api.create_namespaced_deployment(
                        body=manifest,
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'Namespace':
                    self._corev1api.create_namespace(body=manifest)

                elif manifest['kind'] == 'ResourceQuota':
                    self._corev1api.create_namespaced_resource_quota(
                        body=manifest,
                        namespace=manifest['metadata']['namespace'])

                elif manifest['kind'] == 'Service':
                    self._corev1api.create_namespaced_service(
                        body=manifest,
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

            except ApiException as e:  # Handle K8S API errors

                if e.status == 409:
                    pass

                if e.status == 400:
                    pass

                raise e

        return True

    def _add_service_acc_key_to_jc(self, rjc_manifest):
        """Add K8S service account credentials to REANA Job Controller.

        In order to interact (e.g. create Pods to run workflows) with
        Kubernetes cluster REANA Job Controller needs to have access to
        API credentials of Kubernetes service account.

        :param rjc_manifest: Python object representing Kubernetes Deployment-
            manifest file of REANA Job Controller generated with
            `generate_configuration()`.

        :return: Python object representing Kubernetes Deployment-
            manifest file of REANA Job Controller with service account
            credentials of the Kubernetes instance `reana-cluster`
            if configured to interact with.
        """
        # Get all secrets for default namespace
        # Cannot use `k8s_corev1.read_namespaced_secret()` since
        # exact name of the token (e.g. 'default-token-8p260') is not know.
        secrets = self._corev1api.list_namespaced_secret(
            'default', include_uninitialized='false')

        # Maybe debug print all secrets should not be enabled?
        # logging.debug(k8s_corev1.list_secret_for_all_namespaces())

        # K8S might return many secrets. Find `service-account-token`.
        for item in secrets.items:
            if item.type == 'kubernetes.io/service-account-token':
                srv_acc_token = item.metadata.name

                # Search for appropriate place to place the token
                # in job-controller deployment manifest
                for i in rjc_manifest['spec']['template']['spec']['volumes']:
                    if i['name'] == 'svaccount':
                        i['secret']['secretName'] = srv_acc_token

        return rjc_manifest

    def _cluster_running(self):
        """Verify that interaction with cluster backend is possible.

        THIS IS CURRENTLY JUST A MOCKUP. NO REAL CHECKS ARE DONE.

        Verifies that Kubernetes deployment is reachable through it's REST API.
        Only very basic checking is done and it is not guaranteed that REANA
        cluster can be initialized, just that interaction with the specified
        Kubernetes deployment is possible.

        :return: `True` if Kubernetes deployment is reachable through
            it's REST API.
        """
        # Maybe just do a request to `/healthz/ping` -endpoint at cluster_url?
        # i.e no kubernetes-python client interaction?
        return True

    def restart(self):
        """Restarts all deployed components. NOT CURRENTLY IMPLEMENTED.

        :raises NotImplementedError:

        """
        raise NotImplementedError()

    def down(self):
        """Bring REANA cluster down, i.e. deletes all deployed components.

        Deletes all Kubernetes Deployments, Namespaces, Resourcequotas and
        Services that were created during initialization of REANA cluster.

        :return: `True` if all components were destroyed successfully.
        :rtype: bool

        :raises ApiException: Failed to successfully interact with
            Kubernetes REST API. Reason for failure is indicated as HTTP error
            codes in addition to a textual description of the error.

        """
        # What is a good propagationPolicy of `V1DeleteOptions`?
        # Default is `Orphan`
        # https://kubernetes.io/docs/concepts/workloads/controllers/garbage-collection/
        # https://github.com/kubernetes-incubator/client-python/blob/master/examples/notebooks/create_deployment.ipynb

        if not self._cluster_running():
            pass

        # All K8S objects seem to use default -namespace.
        # Is this true always, or do we create something for non-default
        # namespace (in the future)?
        for manifest in self.cluster_conf:
            try:
                logging.debug(json.dumps(manifest))

                if manifest['kind'] == 'Deployment':
                    self._extbetav1api.delete_namespaced_deployment(
                        name=manifest['metadata']['name'],
                        body=k8s_client.V1DeleteOptions(
                            propagation_policy="Foreground",
                            grace_period_seconds=5),
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'Namespace':
                    self._corev1api.delete_namespace(
                        name=manifest['metadata']['name'],
                        body=k8s_client.V1DeleteOptions())

                elif manifest['kind'] == 'ResourceQuota':
                    self._corev1api.delete_namespaced_resource_quota(
                        name=manifest['metadata']['name'],
                        body=k8s_client.V1DeleteOptions(),
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

                elif manifest['kind'] == 'Service':
                    self._corev1api.delete_namespaced_service(
                        name=manifest['metadata']['name'],
                        namespace=manifest['metadata'].get('namespace',
                                                           'default'))

            except ApiException as e:  # Handle K8S API errors

                if e.status == 409:  # Conflict, object probably already exists
                    pass

                if e.status == 404:
                    pass

                if e.status == 400:
                    pass

        return True

    def get_component(self, component_name, component_namespace='default'):
        """Fetch info (e.g.URL) about deployed REANA component.

        Fetches information such as URL(s) of a REANA component deployed to
        REANA cluster.

        :param component_name: Name of the REANA component whose information
            is to be fetched.
        :type component_name: string

        :param component_namespace: Namespace where REANA component specified
            with `component_name` is deployed. Kubernetes specific information.
        :type component_namespace: string

        :return: Information (e.g. URL(s)) about a deployed REANA component.
        :rtype: dict

        :raises ApiException: Failed to successfully interact with
            Kubernetes REST API. Reason for failure is indicated as HTTP error
            codes in addition to a textual description of the error.

        """
        comp_info = {
            'internal_ip': '',
            'ports': [],
            'external_ip_s': [],
            'external_name': '',
        }

        try:

            # Strip reana-prefix from component name if it is there.
            component_name_without_prefix = None
            if not component_name.startswith('reana-'):
                component_name_without_prefix = component_name
            else:
                component_name_without_prefix = component_name[len('reana-'):]

            minikube_ip = None

            # If running on Minikube, ip-address is Minikube VM-address
            nodeconf = self._corev1api.list_node()

            # There can be many Nodes. Is this a problem?
            # (i.e. How to know which is the one should be connected to?)
            for item in nodeconf.items:
                if item.metadata.name == 'minikube':
                    # Running on minikube --> get ip-addr from status.addresses
                    for address in item.status.addresses:
                        if address.type == 'InternalIP':
                            minikube_ip = address.address

            # Get ip-addresses and ports of the component (K8S service)
            comp = self._corev1api.read_namespaced_service(
                component_name_without_prefix,
                component_namespace)

            logging.debug(comp)

            comp_info['external_name'] = comp.spec.external_name
            comp_info['external_ip_s'] = minikube_ip or comp.spec.external_i_ps
            comp_info['internal_ip'] = comp.spec.external_i_ps

            for port in comp.spec.ports:
                if minikube_ip:
                    comp_info['ports'].append(str(port.node_port))
                else:
                    comp_info['ports'].append(str(port.port))

            logging.debug(comp_info)

        except ApiException as e:  # Handle K8S API errors

            if e.status == 409:  # Conflict
                pass

            if e.status == 404:
                pass

            if e.status == 400:
                pass

            raise e

        return comp_info

    def verify_components(self):
        """Verify that REANA components are setup according to specifications.

        Verifies that REANA components are set up as specified in REANA
        cluster specifications file.
        Components must be deployed first, before verification can be done.

        Currently verifies only that docker image (<NAME>:<TAG> -string) of a
        deployed component matches to docker image specified in REANA cluster
        specification file.

        :return: `True` if verification of components was successful.
        :rtype: bool

        :raises ApiException: Failed to successfully interact with
            Kubernetes REST API. Reason for failure is indicated as HTTP error
            codes in addition to a textual description of the error.

        """
        if not self._cluster_running():
            pass

        try:
            for manifest in self.cluster_conf:

                # We are only interested in Deployment manifests since
                # these define docker images that Kubernetes Pods based on
                # these Deployments should be using.
                if manifest['kind'] == 'Deployment':
                    component_name = manifest['metadata']['name']

                    # Kubernetes Deployment manifest could have multiple
                    # containers per manifest file. Current implementation
                    # expects only one container per manifest file.
                    spec_img = manifest['spec'][
                        'template']['spec']['containers'][0]['image']

                    deployed_comp = self._extbetav1api. \
                        read_namespaced_deployment(component_name, 'default')

                    logging.debug(deployed_comp)

                    # Kubernetes Deployment could have multiple containers per
                    # Deployment. Current implementation expects only one
                    # container per deployment.
                    # THIS WILL CAUSE PROBLEM if there are two Pods and one
                    # of them is (even temporarily, e.g. update situation)
                    # based on "old" image defined in older REANA cluster
                    # specification file.
                    deployed_img = deployed_comp.spec.template.spec.containers[
                        0].image

                    logging.info('Component name: {}\n'
                                 'Specified image: {}\n'
                                 'Currently deployed image: {}\n'
                                 .format(component_name,
                                         spec_img,
                                         deployed_img))

                    if not spec_img == deployed_img:
                        logging.error('Mismatch between specified and '
                                      'deployed image of {}. \n'
                                      'Specified image: {}\n'
                                      'Currently deployed image: {}\n'
                                      .format(component_name,
                                              spec_img,
                                              deployed_img))

        except ApiException as e:  # Handle K8S API errors

            if e.status == 409:
                pass

            if e.status == 404:
                pass

            if e.status == 400:
                pass

            raise e

        return True

    def verify_backend(self):
        """Verify that cluster backend is compatible with REANA.

        Verifies that REANA cluster backend is 1) compatible with REANA and
        2) set up as specified in REANA cluster specifications file.

        Currently includes just a version check.

        :return: `True` if verification of backend was successful.
        :rtype: bool

        """
        return self._verify_k8s_version()

    def _verify_k8s_version(self):
        """Verify version of K8S instance is compatible with REANA cluster.

        Verifies that the version of Kubernetes instance `reana-cluster` is
        connecting to is compatible with REANA (min, max versions in config)
        and that version is compatible with target version in REANA cluster
        specifications file.

        Version strings are parsed according to PEP440, which seems to support
        semantic versioning style what Kubernetes uses.
        (PEP440 not fully compliant with semver)

        :return: `True` if version verification was completed successfully.
        :rtype: bool

        """
        if not self._cluster_running():
            pass

        curr_ver = parse_version(self._versionapi.get_code().git_version)
        expected_ver = parse_version(
            self.cluster_spec['cluster']['version'])
        max_ver = parse_version(self._conf['max_version'])
        min_ver = parse_version(self._conf['min_version'])

        logging.info('Current K8S version: {}\n'
                     'Specified K8S version: {}\n'
                     'Max supported K8S version: {}\n'
                     'Min supported K8S version: {}'
                     .format(curr_ver, expected_ver, max_ver, min_ver))

        # Compare current K8S version to max / min
        if curr_ver >= max_ver:
            logging.error('Your Kubernetes version is too new: {cur} \n'
                          'Newest version REANA supports is: {max}'
                          .format(cur=curr_ver, max=max_ver))

        elif curr_ver <= min_ver:
            logging.error('Your Kubernetes version is too old: {cur} \n'
                          'Oldest version REANA supports is: {min}'
                          .format(cur=curr_ver, min=min_ver))

        # Compare specified version to max/min
        elif expected_ver >= max_ver:
            logging.error('Specified Kubernetes version is too new: {cur} \n'
                          'Newest version REANA supports is: {max}'
                          .format(cur=curr_ver, max=max_ver))

        elif expected_ver <= min_ver:
            logging.error('Specified Kubernetes version is too old: {cur} \n'
                          'Oldest version REANA supports is: {min}'
                          .format(cur=curr_ver, min=min_ver))

        # Compare specified version to current K8S version
        elif expected_ver <= curr_ver:
            logging.error('Your Kubernetes version is too new: {cur} \n'
                          'Specification expects: {expected}'
                          .format(cur=curr_ver, expected=expected_ver))

        elif expected_ver >= curr_ver:
            logging.error('Your Kubernetes version is too old: {cur} \n'
                          'Specification expects: {expected}'
                          .format(cur=curr_ver, expected=expected_ver))

        return True
