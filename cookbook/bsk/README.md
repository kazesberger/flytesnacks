# how to reproduce stuck workflow

run the workflow `flye_large_fan_out_fail` with `number_of_inputs >= 10000`


current test-env config:

```
❯ k get cm flyte-propeller-config -oyaml                                                                                                                                          [arn:aws:eks:eu-central-1:494237398978:cluster/infrateam-dev-eks-wca2|flyte]
apiVersion: v1
data:
  admin.yaml: |
    admin:
      clientId: flytepropeller
      clientSecretLocation: /etc/secrets/client_secret
      endpoint: flyteadmin:81
      insecure: true
    event:
      capacity: 1000
      rate: 500
      type: admin
  cache.yaml: |
    cache:
      max_size_mbs: 4096
      target_gc_percent: 70
  catalog.yaml: |
    catalog-cache:
      endpoint: datacatalog:89
      insecure: true
      type: datacatalog
  copilot.yaml: |
    plugins:
      k8s:
        co-pilot:
          image: cr.flyte.org/lyft/flyteplugins/flytecopilot:dc4bdbd61cac88a39a5ff43e40f026bdbc2c78a2
          memory: 1024Mi
          name: flyte-copilot-
          start-timeout: 30s
  core.yaml: |
    propeller:
      downstream-eval-duration: 5s
      enable-admin-launcher: true
      gc-interval: 4h
      kube-client-config:
        burst: 100
        qps: 1000
        timeout: 30s
      leader-election:
        enabled: true
        lease-duration: 15s
        lock-config-map:
          name: propeller-leader
          namespace: flyte
        renew-deadline: 10s
        retry-period: 2s
      limit-namespace: all
      max-workflow-retries: 5
      metadata-prefix: metadata/propeller
      metrics-prefix: flyte
      prof-port: 10254
      queue:
        batch-size: -1
        batching-interval: 2s
        queue:
          base-delay: 5s
          capacity: 1000
          max-delay: 120s
          rate: 100
          type: maxof
        sub-queue:
          capacity: 1000
          rate: 100
          type: bucket
        type: batch
      rawoutput-prefix: s3://************-data/
      workers: 100
      workflow-reeval-duration: 10s
    webhook:
      certDir: /etc/webhook/certs
      serviceName: flyte-pod-webhook
  enabled_plugins.yaml: |
    tasks:
      task-plugins:
        default-for-task-types:
          container: container
          container_array: k8s-array
          hive: athena
          pytorch: pytorch
          sidecar: sidecar
          spark: spark
        enabled-plugins:
        - container
        - sidecar
        - spark
        - k8s-array
        - pytorch
        - athena
  k8s.yaml: |
    plugins:
      k8s:
        default-cpus: 100m
        default-env-vars:
        - FLYTE_AWS_ACCESS_KEY_ID: AKIAXGEWYG7BK2WBYRFX
        - FLYTE_AWS_SECRET_ACCESS_KEY: ****************** # key rotated -.-
        default-memory: 100Mi
        resource-tolerations:
          nvidia.com/gpu:
            effect: NoSchedule
            key: volatile
            operator: Exists
  logger.yaml: |
    logger:
      level: 5
      show-source: true
  resource_manager.yaml: |
    propeller:
      resourcemanager:
        redis:
          hostKey: mypassword
          hostPath: redis-resource-manager:6379
        resourceMaxQuota: 10000
        type: redis
  storage.yaml: |
    storage:
      type: s3
      container: "*************"
      connection:
        auth-type: iam
        region: eu-central-1
      limits:
        maxDownloadMBs: 500000

```

Propeller deployment snippet:

```
      containers:
      - command:
        - flytepropeller
        - --config
        - /etc/flyte/config/*.yaml
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              apiVersion: v1
              fieldPath: metadata.name
        image: cr.flyte.org/flyteorg/flytepropeller:v0.13.4
        imagePullPolicy: IfNotPresent
        name: flytepropeller
        ports:
        - containerPort: 10254
          protocol: TCP
        resources:
          limits:
            cpu: "8"
            ephemeral-storage: 1Gi
            memory: 18Gi
          requests:
            cpu: "7"
            ephemeral-storage: 1Gi
            memory: 18Gi

```
