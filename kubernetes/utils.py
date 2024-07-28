from typing import List
from dataclasses import dataclass


@dataclass(frozen=True)
class KeyValueModel:
    name: str
    value: str


class BaseModel:
    def get_key_value_params_envs(self, data: List[KeyValueModel], indent_line: int) -> str:
        envs = list()
        space = ''
        for env in data:
            param = ('{spacer:%s}- name: {name}\n' % indent_line).format(
                spacer=space,
                name=env.name,
            )
            param += ('{spacer:%s}value: "{value}"' % (indent_line + 2)).format(
                spacer=space,
                value=env.value
            )
            envs.append(param)
        return '\n'.join(envs)

    def get_key_value_params_labels(self, data: List[KeyValueModel], indent_line: int) -> str:
        envs = list()
        space = ''
        for env in data:
            param = ('{spacer:%s}{name}: {value}\n' % indent_line).format(
                spacer=space,
                name=env.name,
                value=env.value,
            )
            envs.append(param)
        return '\n'.join(envs)
