from typing import List

import yaml
from kubernetes import client
from kubernetes.utils import BaseModel, KeyValueModel


class ServiceManager(BaseModel):
    SERVICE_TYPE_LOAD_BALANCER = 'LoadBalancer'
    SERVICE_TYPE_CLUSTER_IP = 'ClusterIP'

    def __init__(self, namespace, configuration=None):
        super().__init__()
        self.__namespace = namespace
        self.__api_client = client.ApiClient(configuration=configuration)
        self.__core_client = client.CoreV1Api(self.__api_client)
        self.__supported_service_type = [
            self.SERVICE_TYPE_LOAD_BALANCER,
            self.SERVICE_TYPE_CLUSTER_IP
        ]

    def get_yaml(self, name: str, service_type: str, target_port: int, labels: List[KeyValueModel]) -> str:
        if service_type not in self.__supported_service_type:
            raise Exception(
                'Unsupported service type. Supported service type {supported_service_type}. Found {service_type}.'.format(
                    supported_service_type=' or '.join(self.__supported_service_type),
                    service_type=service_type
                )
            )
        return """
apiVersion: v1
kind: Service
metadata:
  name: {name}
  labels:
{labels}
spec:
  type: {service_type}
  ports:
    - port: 80
      targetPort: {target_port}
      protocol: TCP
      name: http
  selector:
{labels}
        """.format(
            name=name,
            service_type=service_type,
            target_port=target_port,
            labels=self.get_key_value_params_labels(data=labels, indent_line=4),
        )

    def create(self, service_yaml: str):
        return self.__core_client.create_namespaced_service(
            body=yaml.safe_load(service_yaml),
            namespace=self.__namespace
        )
    def read_namespaced_service_status(self, name: str):
        return self.__core_client.read_namespaced_service_status(
            name=name,
            namespace=self.__namespace
        )

    def list_namespaced_service(self):
        return self.__core_client.list_namespaced_service(
            namespace=self.__namespace
        )

    def patch(self, name: str, service_yaml: str):
        return self.__core_client.patch_namespaced_service(
            name=name,
            body=yaml.safe_load(service_yaml),
            namespace=self.__namespace
        )

    def delete(self, name: str):
        return self.__core_client.delete_namespaced_service(
            name=name,
            namespace=self.__namespace
        )
    def is_service_present(self, list_of_service_name):
        """
        Sends True even if either of services is present
        """
        for service_name in list_of_service_name:
            try:
                self.read_namespaced_service_status(
                    name=service_name
                )
                return True
            except:
                pass
        return False