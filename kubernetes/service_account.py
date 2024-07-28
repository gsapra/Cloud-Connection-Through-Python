from kubernetes import client


class ServiceAccountManager:
    def __init__(self, namespace):
        self.__namespace = namespace
        self.__api_client = client.ApiClient()
        self.__core_client = client.CoreV1Api(self.__api_client)

    def create(self, namespace: str, service_account_name: str):
        return self.__core_client.create_namespaced_service_account(
            namespace=namespace,
            body=dict(metadata=dict(name=service_account_name))
        )

    def delete(self, namespace: str, service_account_name: str):
        response = self.__core_client.delete_namespaced_service_account(
            namespace=namespace,
            name=service_account_name
        )
        return response
