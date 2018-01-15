Getting started
===============


Quickstart
----------

0. `Install Minikube <https://kubernetes.io/docs/getting-started-guides/minikube/#installation>`_.

1. Start Minikube
   ::

   $ minikube start --kubernetes-version="v1.6.4"


2. Install reana-cluster (you probably want to use a virtualenv)
   ::

   $ mkvirtualenv reana-cluster
   $ pip install -e 'git+https://github.com/reanahub/reana-cluster.git@master#egg=reana-cluster'


3. Download default reana-cluster.yaml -file
   ::

   $ wget https://raw.githubusercontent.com/reanahub/reana-cluster/master/reana-cluster.yaml


4. Initialize a REANA cluster
   ::

   $ reana-cluster init


5. Check that all components are deployed
   ::

   $ reana-cluster verify components


6. Run some of our `reana-demo -example workflows <https://github.com/search?q=org%3Areanahub+reana-demo&type=Repositories>`_
   on your newly created cluster.

   Check how to `Get information about a deployed REANA component`_ in order to
   configure reana-client properly (e.g. `$REANA_SERVER_URL`)

.. |br| raw:: html

   <br />

7. Delete REANA cluster
   ::

   $ reana-cluster down


8. Stop Minikube
   ::

   $ minikube stop


Prerequisites
-------------

Currently reana-cluster command line tool supports deploying
REANA components only to `Kubernetes <https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/>`_
infrastructure, so in order to deploy REANA components one needs to have a
working Kubernetes deployment.

reana-cluster utilizes configuration files of `kubectl -tool <https://kubernetes.io/docs/user-guide/kubectl-overview/>`_
to set up a connection to Kubernetes infrastructure, so in order
to use reana-cluster one needs to have kubectl installed
and configured properly.


Test reana-cluster using Minikube
---------------------------------

Easiest way to test reana-cluster without dedicating time to
setting up a real Kubernetes infrastructure is to use
`Minikube <https://kubernetes.io/docs/getting-started-guides/minikube/>`_,
which is a spins up a working Kubernetes deployment in a virtual machine.

Once you have installed kubectl and Minikube, start Minikube by running:

.. code-block:: console

   $ minikube start --kubernetes-version="v1.6.4"
   ...
   minikube: Running
   cluster: Running
   kubectl: Correctly Configured: pointing to minikube-vm at 192.168.99.100

.. note::
   Currently REANA supports only Kubernetes v1.6.4

As seen from the output, Minikube startup routines should
configure kubectl to interact with the newly created
virtual machine, but it best to test that kubectl is indeed
configured properly:

.. code-block:: console

   $ kubectl get all
   NAME             CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
   svc/kubernetes   10.0.0.1     <none>        443/TCP   3d


Install reana-cluster cli tool
------------------------------

reana-cluster command line interface tool is not yet released
in PyPI, so install it from our GitHub repotory:

.. code-block:: console

   $ pip install \
     -e 'git+https://github.com/reanahub/reana-cluster.git@master#egg=reana-cluster'


Initialize a REANA cluster
--------------------------

Main function of reana-cluster command line tool is to
initialize a working REANA cluster, ready to run workflows
you submit to it using reana-client.

In order to achieve this reana-cluster needs to know how
REANA cluster should be set up; e.g. what versions of REANA
components should be deployed and how the configuration of each
component should be set up.

reana-client expects to get information via REANA cluster
specification file.

The specifications file is written in YAML syntax, but since
reana-cluster is still work-in-progress the structure of
REANA specifications file might change rapidly.
We therefore suggest that you download our default
configuration file from the root of our GitHub repository:

.. code-block:: console

   $ wget https://raw.githubusercontent.com/reanahub/reana-cluster/master/reana-cluster.yaml


Default REANA cluster specifications file deploys latest
released versions of all REANA components in their
default configuration. Please note that default specifications file
is intended for evaluation, not for production deployments.

After downloading the specifications file it is just a matter of
running `init` with reana-cluster:

.. code-block:: console

   $ reana-cluster init


Verify REANA components
-----------------------

You can verify that components deployed to REANA cluster are set up according
to what is defined in REANA cluster specifications file `verify`:

.. code-block:: console

   $ reana-cluster verify components


Get information about a deployed REANA component
------------------------------------------------

To print component specific information, for example URLs that can
be used to interact with the component run
``reana-cluster get <COMPONENT_NAME>``.
When REANA cluster is deployed on minikube ``get``-command returns
an IP-address+port combination. This information can be used to construct URL
to access component's API or user-interface in case component provides one.

.. code-block:: console

   $ reana-cluster get reana-server
   ...
   external_name: None
   internal_ip: None
   external_ip_s: 192.168.99.100
   ports: ['31904']

.. note::
   You can use ``get``-command if you need to configure reana-client
   (`$REANA_SERVER_URL`) or access reana-workflow-monitor:
   \http://``<external_ip_s>``:``<ports>``


Delete REANA cluster deployment
-------------------------------

To bring the cluster deployment down, i.e. delete all REANA components that
were deployed during `init`, you run:

.. code-block:: console

   $ reana-cluster down
