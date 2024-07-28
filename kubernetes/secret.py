from kubernetes import client


class SecretManager:
    def __init__(self, namespace, configuration=None, request_timeout=5):
        self.__namespace = namespace
        self.__api_client = client.ApiClient(configuration=configuration)
        self.__core_client = client.CoreV1Api(self.__api_client)
        self._request_timeout = request_timeout  # seconds

    def create(
            self,
            name: str,
            docker_config: str,
    ):
        return self.__core_client.create_namespaced_secret(
            namespace=self.__namespace,
            body=client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=name,
                ),
                type="kubernetes.io/dockerconfigjson",
                data={".dockerconfigjson": docker_config},
            ),
            _request_timeout=self._request_timeout
        )

    def patch(
            self,
            name: str,
            docker_config: str,
    ):
        return self.__core_client.patch_namespaced_secret(
            name=name,
            namespace=self.__namespace,
            body=client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=name,
                ),
                type="kubernetes.io/dockerconfigjson",
                data={".dockerconfigjson": docker_config},
            ),
            _request_timeout=self._request_timeout
        )

    def create_opaque(
            self,
            name: str,
            data: dict,
    ):
        return self.__core_client.create_namespaced_secret(
            namespace=self.__namespace,
            body=client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=name,
                ),
                type="Opaque",
                data=data
            ),
            _request_timeout=self._request_timeout
        )

    def patch_opaque(
            self,
            name: str,
            data: dict,
    ):
        return self.__core_client.patch_namespaced_secret(
            name=name,
            namespace=self.__namespace,
            body=client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=name,
                ),
                type="Opaque",
                data=data
            ),
            _request_timeout=self._request_timeout
        )

    def delete(self, name: str):
        return self.__core_client.delete_namespaced_secret(
            name=name,
            namespace=self.__namespace,
            _request_timeout=self._request_timeout
        )
