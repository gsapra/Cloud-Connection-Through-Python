import yaml
from kubernetes import client


class StatefulManager:
    def __init__(self, namespace):
        self.__namespace = namespace
        self.__api_client = client.ApiClient()
        self.__apps_client = client.AppsV1Api(self.__api_client)

    def create(self, stateful_set_yaml: str):
        return self.__apps_client.create_namespaced_stateful_set(
            body=yaml.safe_load(stateful_set_yaml),
            namespace=self.__namespace
        )

    def patch(self, name: str, stateful_set_yaml: str):
        return self.__apps_client.patch_namespaced_stateful_set(
            body=yaml.safe_load(stateful_set_yaml),
            namespace=self.__namespace,
            name=name
        )

    def delete(self, name: str):
        return self.__apps_client.delete_namespaced_stateful_set(
            namespace=self.__namespace,
            name=name
        )
