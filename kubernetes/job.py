import yaml
from kubernetes import client


class JobManager:
    def __init__(self, namespace: str):
        self.__namespace = namespace
        self.__batch_api = client.BatchV1Api()

    def create(
            self,
            yaml_content: str
    ):
        """
        To create a job.
        https://github.com/kubernetes-client/python/blob/master/examples/job_crud.py
        :param yaml_content:
        :return:
        """
        dep = yaml.safe_load(yaml_content)
        return self.__batch_api.create_namespaced_job(self.__namespace, dep)

    def delete(
            self,
            name: str,
    ):
        return self.__batch_api.delete_namespaced_job(
            name=name,
            namespace=self.__namespace
        )

    def list_namespaced_job(self):
        return self.__batch_api.list_namespaced_job(namespace=self.__namespace)

