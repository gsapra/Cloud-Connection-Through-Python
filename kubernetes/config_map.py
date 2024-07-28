from kubernetes import client
import json


class ConfigMapManager:
    def __init__(self, namespace: str, configuration=None):
        self.__namespace = namespace
        self.__api_client = client.ApiClient(configuration=configuration)
        self.__core_api = client.CoreV1Api(self.__api_client)

    def get_properties(self, properties: dict) -> str:
        data = []
        for k, v in properties.items():
            if type(v) == bool:
                val = json.dumps(v)
            else:
                val = v
            data.append('{key}={value}'.format(key=k, value=val))
        return '\n'.join(data)

    def _handle_val(self, data):
        if data == 'True' or data == 'False':
            return eval(data)
        try:
            return int(data)
        except:
            pass
        if data == 'true':
            return True
        if data == 'false':
            return False
        return data

    def render_properties(self, properties: str) -> dict:
        prop = dict()
        for item in properties.split('\n'):
            if item.strip():
                k, *v = item.split('=')
                v = '='.join(v)
                prop.update({
                    k: self._handle_val(v)
                })
        return prop

    def create(self, name, properties, labels=None):
        if labels is None:
            labels = {}
        # default_labels = {'app': 'e6data', 'component': name.split('-')[-1]}
        # labels.update(default_labels)
        secret = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=self.__namespace,
                labels=labels
            ),
            data={'config.properties': self.get_properties(properties)},
        )
        return self.__core_api.create_namespaced_config_map(namespace=self.__namespace, body=secret)

    def list_namespaced_config_map(self):
        return self.__core_api.list_namespaced_config_map(namespace=self.__namespace)

    def read_namespaced_config_map(self, name: str):
        return self.__core_api.read_namespaced_config_map(
            name=name,
            namespace=self.__namespace
        )

    def patch(self, name, properties, labels=None):
        if labels is None:
            labels = {}
        # default_labels = {'app': 'e6data', 'component': name.split('-')[-1]}
        # labels.update(default_labels)
        secret = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=self.__namespace,
                labels=labels
            ),
            data={'config.properties': self.get_properties(properties)},
        )
        return self.__core_api.patch_namespaced_config_map(name=name, namespace=self.__namespace, body=secret)

    def compare_properties(self, name: str, properties: dict, exclude_keys: list = None) -> bool:
        """
        Compare existing properties with new.
        To make sure to patch only if there is any change.
        """
        if not exclude_keys:
            exclude_keys = list()
        response = self.read_namespaced_config_map(
            name=name
        )
        existing_properties = self.render_properties(response.data['config.properties'])
        prop1 = dict()
        prop2 = dict()
        for k, v in properties.items():
            if k not in exclude_keys:
                prop1.update({k: v})
        for k, v in existing_properties.items():
            if k not in exclude_keys:
                prop2.update({k: v})
        return prop1 == prop2

    def patch_properties(self, name, properties):
        secret = client.V1ConfigMap(
            # api_version="v1",
            kind="ConfigMap",
            data={'config.properties': self.get_properties(properties)},
        )
        return self.__core_api.patch_namespaced_config_map(name=name, namespace=self.__namespace, body=secret)

    def delete(self, name: str):
        return self.__core_api.delete_namespaced_config_map(
            name=name,
            namespace=self.__namespace
        )

