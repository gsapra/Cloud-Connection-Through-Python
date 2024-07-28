import time

import yaml
from kubernetes import client


class DaemonSetManager:
    def __init__(self, namespace, configuration=None):
        self.__namespace = namespace
        self.__api_client = client.ApiClient(configuration=configuration)
        self.__apps_client = client.AppsV1Api(self.__api_client)

    def create(
            self,
            body: str
    ):
        return self.__apps_client.create_namespaced_daemon_set(
            namespace=self.__namespace, body=yaml.safe_load(body)
        )

    def patch(self, name: str, body: str):
        return self.__apps_client.patch_namespaced_daemon_set(
            name=name,
            namespace=self.__namespace,
            body=yaml.safe_load(body)
        )

    def delete(self, name: str):
        return self.__apps_client.delete_namespaced_daemon_set(
            name=name,
            namespace=self.__namespace
        )

    def watcher(self, name: str):
        current_retry_max_count = 0
        MAX_RETRY_COUNT = 36
        WAITING_TIME_FOR_RETRY = 10  # Seconds
        while True:
            ret = self.__apps_client.read_namespaced_daemon_set_status(
                name=name,
                namespace=self.__namespace
            )
            desired_number_scheduled = ret._status.desired_number_scheduled
            current_number_scheduled = ret._status.current_number_scheduled
            number_ready = ret._status.number_ready
            status = dict(
                current_number_scheduled=current_number_scheduled,
                desired_number_scheduled=desired_number_scheduled,
                number_ready=number_ready
            )
            print(status)
            if desired_number_scheduled == current_number_scheduled == number_ready and number_ready > 0:
                return True
            current_retry_max_count += 1
            time.sleep(WAITING_TIME_FOR_RETRY)
            if current_retry_max_count >= MAX_RETRY_COUNT:
                raise Exception('Max retry exceeded.')
