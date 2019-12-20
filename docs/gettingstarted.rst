.. _gettingstarted:

Getting started
===============

This tutorial explains how to quick-start with REANA-Cluster.

Deploy locally
--------------

Are you looking at installing and deploying REANA cluster locally on your laptop?

1. Install `kubectl <https://kubernetes.io/docs/tasks/tools/install-kubectl/>`_
   (e.g. version 1.16.3), `minikube
   <https://kubernetes.io/docs/tasks/tools/install-minikube/>`_ (e.g. version
   1.5.2) and `Helm <https://docs.helm.sh/using_helm/#installing-helm>`_ (e.g.
   version 3.0.0):

   .. code-block:: console

      $ sudo dpkg -i kubectl*.deb minikube*.deb kubernetes-helm*.deb

2. Start Minikube virtual machine:

   .. code-block:: console

      $ minikube start --feature-gates="TTLAfterFinished=true"

3. Install REANA-Cluster sources. You probably want to use a virtual environment:

   .. code-block:: console

      $ # create new virtual environment
      $ virtualenv ~/.virtualenvs/myreana
      $ source ~/.virtualenvs/myreana/bin/activate
      $ # install reana-cluster utility
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
      $ eval $(reana-cluster env --include-admin-token)

   If you need to create more users you can:

   .. code-block:: console

      $ kubectl exec \
            -ti $(kubectl get pods -l=app=server -o jsonpath='{.items[0].metadata.name}') \
            -- flask users create \
                  -e jane.doe@example.org \
                  --admin-access-token $REANA_ACCESS_TOKEN
      User was successfully created.
      ID                                     EMAIL                  ACCESS_TOKEN
      09259d12-b06c-4a13-a696-ae8e57f1f0c9   jane.doe@example.org   dHYXgh5AXmukZrdWccZaSg



7. You can now run REANA examples on the locally-deployed cluster using
   `reana-client <https://reana-client.readthedocs.io/>`_.

   Note that after you finish testing REANA, you can delete the locally-deployed
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

3. Load the configuration to connect to the Kubernetes cluster and wait for
   the pods to be created:

   .. code-block:: console

      $ $(openstack coe cluster config <cluster-name>)
      $ kubectl get pods -w

4. Set one of the nodes to be an ingress controller
   and create a landb alias:

   .. code-block:: console

      # Get all cluster nodes
      $ kubectl get nodes
      $ kubectl label node <node-name> role=ingress
      $ openstack server set --property landb-alias=<your-subdomain> <ingress-node>

5. As we are using the alpha feature gate `TTLAfterFinished
   <https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/>`_
   we need to manually activate it:

   .. code-block:: console

      $ # Get the Kube master name and connect to it
      $ openstack server list | grep -E reana-.*-master
      $ ssh -i <ssh-key> fedora@<master-node>
      ssh> # Add `TTLAfterFinished=true` to the `--feature-gates` in
      ssh> # `/etc/kubernetes/apiserver `and `/etc/kubernetes/controller-manager`
      ssh> sudo vi /etc/kubernetes/apiserver
      ssh> sudo vi /etc/kubernetes/controller-manager
      ssh> # Finally restart both services
      ssh> sudo systemctl restart kube-apiserver
      ssh> sudo systemctl restart kube-controller-manager
      ssh> # Logout from the master node
      ssh> exit

6. Since Python3 does not come by default we have to use the `slc` command to
   activate it and we create a virtual environment for REANA:

   .. code-block:: console

      $ scl enable rh-python36 bash
      $ virtualenv reana
      $ source reana/bin/activate

7. Install `reana-cluster`:

   .. code-block:: console

      (reana) $ pip install reana-cluster


8. Create your own ``reana-cluster.yaml``. For instance, to deploy REANA
   ``0.6.0`` at CERN with 200 GB Ceph volume and having as URL
   ``reana-dev.cern.ch`` the file, ``reana-cluster-CERN.yaml``, would look
   like follows:

   .. code-block:: yaml

      cluster:
        type: "kubernetes"
        version: "v1.16.3"
        db_config: &db_base_config
          - REANA_DB_NAME: "reana"
          - REANA_DB_HOST: "db-host-name"
          - REANA_DB_PORT: "5432"
        root_path: "/var/reana"
        shared_volume_path: "/var/reana"
        reana_url: "reana-dev.cern.ch"
        ui: True
        eos: True
        cephfs: True
        cephfs_volume_size: 200
        cephfs_os_share_id: <cephfs-share-id>
        cephfs_os_share_access_id: <cephfs-share-access-id>
        db_persistence_path: "/var/reana/db"

      components:
        reana-workflow-controller:
          type: "docker"
          image: "reanahub/reana-workflow-controller:0.6.0"
          environment:
           - <<: *db_base_config
           - REANA_JOB_CONTROLLER_IMAGE: "reanahub/reana-job-controller:0.6.0"
           - REANA_WORKFLOW_ENGINE_IMAGE_CWL: "reanahub/reana-workflow-engine-cwl:0.6.0"
           - REANA_WORKFLOW_ENGINE_IMAGE_YADAGE: "reanahub/reana-workflow-engine-yadage:0.6.0"
           - REANA_WORKFLOW_ENGINE_IMAGE_SERIAL: "reanahub/reana-workflow-engine-serial:0.6.0"

        reana-server:
          type: "docker"
          image: "reanahub/reana-server:0.6.0"
          environment:
           - <<: *db_base_config

        reana-message-broker:
          type: "docker"
          image: "reanahub/reana-message-broker:0.6.0"


9. Instantiate REANA cluster:

   .. code-block:: console

      (reana) $ reana-cluster -f reana-cluster-CERN.yaml init

10. Test that REANA can be accessed by the specified domain name:

   .. code-block:: console

      (reana) $ curl http://reana-dev.cern.ch/api/ping
      {"message": "OK", "status": "200"}


Next steps
----------

For more information, please see:

- Looking for a more comprehensive user manual? See :ref:`userguide`
- Looking for tips how to develop REANA-Cluster component? See :ref:`developerguide`
- Looking for command-line API reference? See :ref:`cliapi`
