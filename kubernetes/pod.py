import yaml
from kubernetes import client


class PodManager:
    def __init__(self, namespace, configuration=None):
        self.__namespace = namespace
        self.__api_client = client.ApiClient(configuration=configuration)
        self.__core_client = client.CoreV1Api(self.__api_client)

    def create(self, pod_yaml: str):
        return self.__core_client.create_namespaced_pod(
            namespace=self.__namespace,
            body=yaml.safe_load(pod_yaml)
        )

    def list_namespaced_pod(self):
        return self.__core_client.list_namespaced_pod(namespace=self.__namespace)

    def patch(self, name: str, pod_yaml: str):
        return self.__core_client.patch_namespaced_pod(
            name=name,
            namespace=self.__namespace,
            body=yaml.safe_load(pod_yaml)
        )

    def patch_annotation(self, name: str, annotations: dict):
        return self.__core_client.patch_namespaced_pod(
            name=name,
            namespace=self.__namespace,
            body={
                "metadata": {
                    "annotations": annotations
                }
            }
        )

    def delete(self, name: str):
        return self.__core_client.delete_namespaced_pod(
            name=name,
            namespace=self.__namespace,
        )
