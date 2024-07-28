import logging

import yaml
from kubernetes import client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

class DeploymentManager:
    def __init__(self, namespace, configuration=None):
        self.__namespace = namespace
        self.__api_client = client.ApiClient(configuration=configuration)
        self.__apps_client = client.AppsV1Api(self.__api_client)

    def create(self, deployment_yaml: str):
        return self.__apps_client.create_namespaced_deployment(
            body=yaml.safe_load(deployment_yaml),
            namespace=self.__namespace
        )

    def list_replicaset(self):
        return self.__apps_client.list_namespaced_replica_set(self.__namespace)

    def delete_zero_ready_replicaset(self, cluster_uuid):
        replicas = self.list_replicaset()
        for rs in replicas.items:
            if cluster_uuid == rs.metadata.labels.get('cluster_uuid'):
                if not rs.status.ready_replicas or rs.spec.replicas == 0:
                    self.__apps_client.delete_namespaced_replica_set(name=rs.metadata.name, namespace=self.__namespace)

    def list_namespaced_deployment(self):
        return self.__apps_client.list_namespaced_deployment(namespace=self.__namespace)

    def patch(self, name: str, deployment_yaml: str):
        return self.__apps_client.patch_namespaced_deployment(
            name=name,
            body=yaml.safe_load(deployment_yaml),
            namespace=self.__namespace
        )

    def patch_scale(self, name: str, replicas: int):
        return self.__apps_client.patch_namespaced_deployment_scale(
            name=name,
            body={'spec': {'replicas': replicas}},
            namespace=self.__namespace
        )

    def read_namespaced_deployment_status(self, name: str):
        return self.__apps_client.read_namespaced_deployment_status(
            name=name,
            namespace=self.__namespace
        )

    def delete_deployment(self, name: str):
        return self.__apps_client.delete_namespaced_deployment(
            name=name,
            namespace=self.__namespace
        )

    def is_deployment_present(self, list_of_deployment_name):
        """
        Sends True even if either of deployments is present
        """
        for deployment_name in list_of_deployment_name:
            try:
                self.read_namespaced_deployment_status(
                    name=deployment_name
                )
                return True
            except:
                pass
        return False

    def patch_a_label(self, label_name: str, label_value: str, name: str):
        return self.__apps_client.patch_namespaced_deployment(
            name=name,
            body={
                'spec': {'template': {'metadata': {'labels': {label_name: label_value}}}},
                'metadata': {'labels': {label_name: label_value}}
            },
            namespace=self.__namespace
        )

    def patch_image_tag(self, tag_value: str, name: str, image_name_in_container=None):
        response = self.__apps_client.read_namespaced_deployment(
            name=name,
            namespace=self.__namespace
        )
        component=None
        if image_name_in_container:
            for j in response.spec.template.spec.containers:
                if image_name_in_container in j.image:
                    image = j.image
                    component=j.name
                    break
            else:
                logger.error("Error in patching image {}".format([name,tag_value,image_name_in_container]))
                return
        else:
            image = response.spec.template.spec.containers[0].image
        image_tag_version = image.split(':')
        image_tag_version[1] = tag_value
        tag = ':'.join(image_tag_version)
        if not component:
            component = name.split('-')[-1]
        return self.__apps_client.patch_namespaced_deployment(
            name=name,
            namespace=self.__namespace,
            body={
                "spec": {"template": {"spec": {"containers": [{"name": component, "image": tag}]}}}
            }
        )