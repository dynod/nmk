"""
Config item resolvers
"""

from abc import ABC, abstractmethod
from typing import Union

from nmk.model.model import NmkModel


class NmkConfigResolver(ABC):
    """
    Config item resolver base class

    :param model: model instance
    """

    def __init__(self, model: NmkModel):
        self.model = model
        """model instance"""

    @abstractmethod
    def get_value(self, name: str) -> Union[str, int, bool, list, dict]:  # pragma: no cover
        """
        Get item current value

        :param name: config item name
        :return: item value
        """
        pass

    @abstractmethod
    def get_type(self, name: str) -> object:  # pragma: no cover
        """
        Get item value type

        :param name: config item name
        :return: item value type
        """
        pass

    def is_volatile(self, name: str) -> bool:
        """
        State if this item is volatile (i.e. shall not be cached)

        :param name: config item name
        :return: item volatile property
        """
        return False


class NmkStrConfigResolver(NmkConfigResolver):
    """
    String config item resolver base class
    """

    def get_type(self, name: str) -> object:
        """
        Get item value type

        :param name: config item name
        :return: item value type (str)
        """
        return str

    @abstractmethod
    def get_value(self, name: str) -> str:  # pragma: no cover
        """
        Get item current string value

        :param name: config item name
        :return: item value
        """
        pass


class NmkBoolConfigResolver(NmkConfigResolver):
    """
    Bool config item resolver base class
    """

    def get_type(self, name: str) -> object:
        """
        Get item value type

        :param name: config item name
        :return: item value type (bool)
        """
        return bool

    @abstractmethod
    def get_value(self, name: str) -> bool:  # pragma: no cover
        """
        Get item current bool value

        :param name: config item name
        :return: item value
        """
        pass


class NmkIntConfigResolver(NmkConfigResolver):
    """
    Int config item resolver base class
    """

    def get_type(self, name: str) -> object:
        """
        Get item value type

        :param name: config item name
        :return: item value type (int)
        """
        return int

    @abstractmethod
    def get_value(self, name: str) -> int:  # pragma: no cover
        """
        Get item current int value

        :param name: config item name
        :return: item value
        """
        pass


class NmkDictConfigResolver(NmkConfigResolver):
    """
    Dict config item resolver base class
    """

    def get_type(self, name: str) -> object:
        """
        Get item value type

        :param name: config item name
        :return: item value type (dict)
        """
        return dict

    @abstractmethod
    def get_value(self, name: str) -> dict:  # pragma: no cover
        """
        Get item current dict value

        :param name: config item name
        :return: item value
        """
        pass


class NmkListConfigResolver(NmkConfigResolver):
    """
    List config item resolver base class
    """

    def get_type(self, name: str) -> object:
        """
        Get item value type

        :param name: config item name
        :return: item value type (list)
        """
        return list

    @abstractmethod
    def get_value(self, name: str) -> list:  # pragma: no cover
        """
        Get item current list value

        :param name: config item name
        :return: item value
        """
        pass
