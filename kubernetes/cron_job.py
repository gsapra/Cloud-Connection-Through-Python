import yaml
from kubernetes import client


class CronJobManager:
    def __init__(self, namespace, configuration=None):
        self.__namespace = namespace
        self.__api_client = client.ApiClient(configuration=configuration)
        self.__apps_client = client.AppsV1Api(self.__api_client)
        self.__core_client = client.BatchV1Api(self.__api_client)

    def create(self, cron_job_yaml: str):
        return self.__core_client.create_namespaced_cron_job(
            namespace=self.__namespace,
            body=yaml.safe_load(cron_job_yaml)
        )

    def list_namespaced_cron_job(self):
        return self.__core_client.list_namespaced_cron_job(namespace=self.__namespace)

    def patch(self, name: str, cron_job_yaml: str):
        return self.__core_client.patch_namespaced_cron_job(
            name=name,
            namespace=self.__namespace,
            body=yaml.safe_load(cron_job_yaml)
        )

    def delete(self, name: str):
        return self.__core_client.delete_namespaced_cron_job(
            name=name,
            namespace=self.__namespace,
        )
