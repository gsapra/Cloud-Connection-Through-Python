from kubernetes import client


class IngressManager:
    def __init__(self, namespace):
        self.__namespace = namespace

    def create(self, name: str, host: str, port: int):
        """
        To create ingress.
        https://github.com/kubernetes-client/python/blob/master/examples/ingress_create.py
        :param name: str
        :param host: str
        :param port: int
        :return:
        """
        networking_v1_api = client.NetworkingV1Api()
        body = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(name="ingress-%s" % name, annotations={
                "nginx.ingress.kubernetes.io/rewrite-target": "/"
            }),
            spec=client.V1IngressSpec(
                rules=[client.V1IngressRule(
                    host=host,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path="/",
                            path_type="Exact",
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    port=client.V1ServiceBackendPort(
                                        number=port,
                                    ),
                                    name="service-%s" % name
                                )
                            )
                        )]
                    )
                )]
            )
        )
        # Creation of the Deployment in specified namespace
        return networking_v1_api.create_namespaced_ingress(
            namespace=self.__namespace,
            body=body
        )

    def delete(self, name: str):
        networking_v1_api = client.NetworkingV1Api()
        networking_v1_api.delete_namespaced_ingress(
            namespace=self.__namespace,
            name='ingress-%s' % name
        )
