.. _gettingstarted:

Getting started
===============

This tutorial explains how to quick-start with REANA-Cluster.

Deploy REANA cluster locally
----------------------------

Are you looking at installing and deploying REANA cluster locally on your laptop?

1. Install Minikube following `minikube installation guide <https://kubernetes.io/docs/getting-started-guides/minikube/#installation>`_.

2. Start Minikube virtual machine:

.. code-block:: console

   $ minikube start --kubernetes-version="v1.6.4"

3. Install REANA-Cluster sources. You probably want to use a virtual environment:

.. code-block:: console

   $ mkvirtualenv reana-cluster
   $ pip install reana-cluster

4. Start REANA cluster instance on Minikube:

.. code-block:: console

   $ reana-cluster init

5. Check the status of deployed REANA cluster components:

.. code-block:: console

   $ reana-cluster verify components

6. Check whether all the pods are running:

.. code-block:: console

   $ kubectl get pods

The REANA cluster is now ready to serve users. Please see the `reana-client
<https://reana-client.readthedocs.io/>`_ documentation on how to run reusable
analysis examples on our locally-deployed cluster.

Note that after you finish testing REANA, you can delete the locally-deployed
cluster and the Minikube virtual machine as follows:

.. code-block:: console

  $ reana-cluster down
  $ minikube stop

Next steps
----------

For more information, please see:

- Looking for a more comprehensive user manual? See :ref:`userguide`
- Looking for tips how to develop REANA-Cluster component? See :ref:`developerguide`
- Looking for command-line API reference? See :ref:`cliapi`
