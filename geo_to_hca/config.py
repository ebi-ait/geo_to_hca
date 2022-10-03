import os
from typing import get_type_hints, Union


class AppConfigError(Exception):
    pass


def _parse_bool(val: Union[str, bool]) -> bool:  # pylint: disable=E1136
    return val if type(val) == bool else val.lower() in ['true', 'yes', '1']


class Config:
    IS_INTERACTIVE: bool = 'true'
    DEBUG: bool = 'false' \
                  ''
    EUTILS_HOST: str = 'https://eutils.ncbi.nlm.nih.gov'
    EUTILS_BASE_URL: str = f'{EUTILS_HOST}/entrez/eutils'
    NCBI_WEB_HOST: str = 'https://www.ncbi.nlm.nih.gov'

    def __init__(self, env):
        self.load(env)

    def load(self, env):
        for field in self.__annotations__:
            if not field.isupper():
                continue
            # Raise AppConfigError if required field not supplied
            default_value = getattr(self, field, None)
            if default_value is None and env.get(field) is None:
                raise AppConfigError('The {} field is required'.format(field))
            # Cast env var value to expected type and raise AppConfigError on failure
            try:
                var_type = get_type_hints(Config)[field]
                if var_type == bool:
                    value = _parse_bool(env.get(field, default_value))
                else:
                    value = var_type(env.get(field, default_value))

                self.__setattr__(field, value)
            except ValueError:
                raise AppConfigError('Unable to cast value of "{}" to type "{}" for "{}" field'.format(
                    env[field],
                    var_type,
                    field
                )
                )

    def reload(self):
        self.load(os.environ)