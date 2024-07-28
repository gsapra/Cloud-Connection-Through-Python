from kubernetes import client


class NamespaceManager:
    def __init__(self, namespace):
        self.__namespace = namespace
        self.__api_client = client.ApiClient()
        self.__core_client = client.CoreV1Api(self.__api_client)

    def create(self, namespace: str):
        return self.__core_client.create_namespace(
            client.V1Namespace(
                metadata=client.V1ObjectMeta(name=namespace)
            )
        )

    def delete(self, namespace: str):
        return self.__core_client.delete_namespace(
            name=namespace
        )
