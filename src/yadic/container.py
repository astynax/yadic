# -*- coding: utf-8 -*-

from __future__ import print_function
from importlib import import_module
import re

from yadic.util import merge


def _merge_upto_lvl2_then_take_other(d1, d2, resolver, path):
    """"merge tool", suitable for normalization
    of the container configuration"""
    if isinstance(d1, dict) and isinstance(d2, dict) and not path:
        # not so deep, merging...
        return merge(d1, d2, resolver, path)
    return d2  # "take other"


class EntityConfiguringError(TypeError):
    """Entity getting error"""

    def __init__(self, path, exc):
        self.path = path
        self.exc = exc

    def __str__(self):
        return ('"{1}" configuring error: "{0!s}"').format(
            self.exc,
            '->'.join(self.path)
        )


class Injectable(type):
    "Provides the __init__ with the suitable args, based on dependencies"

    def __new__(cls, name, bases, dic):
        deps = dic.setdefault('depends_on', tuple())
        if deps and '__init__' not in dic:
            # формирование конструктора
            init = eval("lambda self, {}: {}".format(
                ','.join(deps),
                ' or '.join(
                    'setattr(self, "{0}", {0})'.format(d)
                    for d in deps)
            ))
            dic['__init__'] = init
        return super(Injectable, cls).__new__(cls, name, bases, dic)


class Container(object):
    "DI Container"

    _TYPES = ('static', 'singleton', None)

    def __init__(self, config):
        """:param config: configuration
        :type config: dict"""
        errors = self.collect_errors(config)
        if errors:
            raise ValueError('\n'.join(['Config errors:'] + errors))
        self._config = self._normalize(config)
        self._entity_cache = {}
        self._singletones = {}

    @staticmethod
    def _normalize(config):
        """Rebuilds the configuration for the speedup purpose
        :param config: initial configuration
        :type config: dict"""

        def norm_deps(blueprint):
            """Converts each of the dependencies to one of the forms:
            ```
            "name": (None, (('group', 'entity'),...))
            "name": ('group', 'entity')
            "$name": value
            "__name__": value
            ```"""
            result = {}
            for k, v in blueprint.items():
                if k.startswith('$') or k.startswith('__'):
                    result[k] = v
                else:
                    kk, group = (k.split(':') + [k])[:2]
                    if isinstance(v, list):
                        vv = (None, tuple((group, i) for i in v))
                    else:
                        vv = (group, v)
                    result[kk] = vv
            return result

        result = {}
        for sect, elems in config.items():
            plan = norm_deps(elems.pop('__default__', {}))
            section = result[sect] = {}
            for el_name, customization in elems.items():
                if el_name != '__default__':
                    section[el_name] = merge(
                        plan.copy(),  # no deepcopy cause of single-level dict
                        norm_deps(customization),
                        _merge_upto_lvl2_then_take_other
                    )
        return result

    @staticmethod
    def _get_entity(name):
        """Returns the entity for the full name
        :param name: entity name
        :type name: str"""
        if '.' not in name:
            raise ValueError('Entity name must be the fully qualified!')
        attr_name = name.split('.')[-1]
        module = import_module(name[:-(len(attr_name) + 1)])
        return getattr(module, attr_name)

    def _get_blueprint(self, group, name):
        """Returns the entity configuration and realization
        :param group: group of entities
        :type group: str
        :param name: name of entity
        :type name: str"""
        blueprint = self._config[group][name]
        key = (group, name)
        return (
            blueprint,
            self._entity_cache.get(key) or self._entity_cache.setdefault(
                key, self._get_entity(blueprint['__realization__']))
        )

    def itergroup(self, group):
        """Returns the iterator of tuples
        (entity_name, entity_configuration, realization)
        :param group: entity group
        :type group: str
        """
        if group not in self._config:
            raise KeyError("Unknown group: {}!".format(group))
        return (
            (i,) + self._get_blueprint(group, i)
            for i in self._config[group]
        )

    def get(self, group, name):
        """Returns the fully configured entity instance
        :param group: entity group
        :type group: str
        :param name: entity name
        :type name: str
        """
        fullname = '{}:{}'.format(group, name)
        try:
            blueprint, realization = self._get_blueprint(group, name)
        except KeyError:
            raise ValueError("{} is not configured!".format(fullname))

        typ = blueprint.get('__type__')

        if typ == 'static':
            result = realization
        else:
            is_singleton = typ == 'singleton'
            if is_singleton:
                result = self._singletones.get((group, name))
            if not is_singleton or not result:
                deps = {}
                for dep_name, dep_val in blueprint.items():
                    # handle "__interdal__" deps
                    if dep_name.startswith('_'):
                        continue
                    # handle "$static" deps
                    elif dep_name.startswith('$'):
                        deps[dep_name[1:]] = dep_val
                    else:
                        # handle manageable deps
                        first, rest = dep_val
                        try:
                            if first is None:
                                deps[dep_name] = tuple(
                                    self.get(g, e) for (g, e) in rest
                                )
                            else:
                                deps[dep_name] = self.get(first, rest)
                        except EntityConfiguringError as e:
                            e.path = (fullname,) + e.path
                            raise
                try:
                    result = realization(**deps)
                except Exception as e:
                    raise EntityConfiguringError(path=(fullname,), exc=e)
                if is_singleton:
                    self._singletones[(group, name)] = result
        return result

    @classmethod
    def collect_errors(cls, cfg):
        """Returns the list of errors of the configuration
        :param cfg: configuration
        :type cfg: dict
        """
        errors = []

        def wrong(what, names):
            errors.append(
                '{0!r} is a wrong {1} name!'.format(':'.join(names), what))

        is_ident = re.compile(r'(?i)^[a-z]\w*$').match
        is_valid_name = re.compile(
            r'(?i)^(?:\$?[a-z]\w*)|(?:[a-z]\w*:[a-z]\w*)$').match

        for group, elems in cfg.items():
            if not is_ident(group):
                wrong('group', (group,))
            for el, cfg in elems.items():
                if not is_ident(el) and el != '__default__':
                    wrong('element', (group, el))
                for k, v in cfg.items():
                    if not (
                        is_valid_name(k) or
                        k in ('__realization__', '__type__')
                    ):
                        wrong('attr', (group, el, k))
                    if k == '__type__' and v not in cls._TYPES:
                        wrong('type', (group, el, k))
        return errors


__all__ = (Container, Injectable)
