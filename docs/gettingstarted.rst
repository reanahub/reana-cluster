.. _gettingstarted:

Getting started
===============

This tutorial explains how to quick-start with REANA-Cluster.

Deploy locally
--------------

Are you looking at installing and deploying REANA cluster locally on your laptop?

1. Install `kubectl <https://kubernetes.io/docs/tasks/tools/install-kubectl/>`_
   (e.g. version 1.9.1) and `minikube
   <https://kubernetes.io/docs/tasks/tools/install-minikube/>`_ (e.g. version
   0.27.0):

   .. code-block:: console

      $ sudo dpkg -i kubectl*.deb minikube*.deb

2. Start Minikube virtual machine:

   .. code-block:: console

      $ minikube start --kubernetes-version="v1.9.4"

3. Install REANA-Cluster sources. You probably want to use a virtual environment:

   .. code-block:: console

      $ mkvirtualenv reana-cluster
      $ pip install reana-cluster

4. Start REANA cluster instance on Minikube:

   .. code-block:: console

      $ reana-cluster init

5. Check the status of the REANA cluster deployment. (Note that it may take
   several minutes to pull the REANA component images for the first time.)

   .. code-block:: console

      $ reana-cluster status
      ...
      REANA cluster is ready.

6. Display the commands to set up the environment for the user clients:

   .. code-block:: console

      $ reana-cluster env
      export REANA_SERVER_URL=http://192.168.99.100:32732

   Please see the `reana-client <https://reana-client.readthedocs.io/>`_
   documentation on how to run reusable analysis examples on your
   locally-deployed cluster.

7. Note that after you finish testing REANA, you can delete the locally-deployed
   cluster and the Minikube virtual machine as follows:

   .. code-block:: console

      $ reana-cluster down
      $ minikube stop

Deploy on CERN infrastructure
-----------------------------

1. Log into `lxplus-cloud`
   (CC7 subset of lxplus with recent OpenStack clients) and create a working
   directory for reana:

   .. code-block:: console

      $ ssh lxplus-cloud.cern.ch
      $ mkdir reana && cd reana

2. `Setup your OpenStack account <https://clouddocs.web.cern.ch/clouddocs/tutorial/create_your_openstack_profile.html>`_
   and create a Kubernetes cluster following the
   `official documentation <https://clouddocs.web.cern.ch/clouddocs/containers/quickstart.html#kubernetes>`_.

.. note::

   For now, you will have to create the cluster with Kubernetes version
   1.9.3 since 1.10.1 introduces a
   `bug with backoff limit <https://github.com/kubernetes/kubernetes/issues/54870>`_.

   .. code-block:: console

      $ openstack coe cluster create reana-cloud --keypair mykey
          --node-count 1
          --cluster-template kubernetes
          --master-flavor m2.medium
          --flavor m2.medium
          --labels influx_grafana_dashboard_enabled=true
          --labels kube_tag="v1.9.3"
          --labels cvmfs_tag=qa
          --labels flannel_backend=vxlan
          --labels container_infra_prefix=gitlab-registry.cern.ch/cloud/atomic-system-containers/
          --labels ingress_controller=traefik

.. note::

   For now, the traefik ingress needs to be amended so permissions are set
   correctly (once fixed in OpenStack this will come automatically.

   .. code-bloack:: console

      $ kubectl -n kube-system edit ds/ingress-traefik
      # add: `serviceAccountName: ingress-traefik` under
      # `spec.template.spec`.
      # Restart the Ingress controller so it uses the correct permissions.
      $ get pods -n kube-system  | grep ingress
      ingress-traefik-666ee                   1/1       Running   0          2m
      $ kubectl delete ingress-traefik-666ee -n kube-system


3. Load the configuration to connect to the Kubernetes cluster and wait for
   the pods to be created:

   .. code-block:: console

      $ $(openstack coe cluster config reana-cloud)
      $ kubectl get pods -w

4. Set one of the nodes (``kubectl get nodes``) to be an ingress controller
   and create a landb alias:

   .. code-block:: console

      $ kubectl label node <node-name> role=ingress
      $ openstack server set --property landb-alias=reana <ingress-node>

5. Create or add ssl secrets:

   .. code-block:: console

      $ openssl req -x509 -nodes -days 365 -newkey rsa:2048
            -keyout /tmp/tls.key -out /tmp/tls.crt
            -subj "/CN=reana.cern.ch"
      $ kubectl create secret tls reana-ssl-secrets
            --key /tmp/tls.key --cert /tmp/tls.crt

6. Since Python3 does not come by default we have to use the `slc` command to
   activate it and we create a virtual environment for REANA:

   .. code-block:: console

      $ scl enable rh-python36 bash
      $ virtualenv reana
      $ source reana/bin/activate

7. Install `reana-cluster` (since `reana-commons` is not yet released we have to
   install it manually):

   .. code-block:: console

      (reana) $ pip install git+git://github.com/reanahub/reana-commons.git@master#egg=reana-commons
      (reana) $ pip install git+git://github.com/reanahub/reana-cluster.git@master#egg=reana-cluster

8.  Set the database URI and instantiate REANA cluster:

   .. code-block:: console

      (reana) $ export REANA_SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://reana:reana@<db-server>:5432/reana
      (reana) $ reana-cluster init

9. Make REANA accessible from outside:

   .. code-block:: console

      (reana) $ curl http://test-reana.cern.ch/api/ping
      {"message": "OK", "status": "200"}


Next steps
----------

For more information, please see:

- Looking for a more comprehensive user manual? See :ref:`userguide`
- Looking for tips how to develop REANA-Cluster component? See :ref:`developerguide`
- Looking for command-line API reference? See :ref:`cliapi`
