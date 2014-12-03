# -*- coding: utf-8 -*-

from __future__ import print_function
from importlib import import_module
import re

from yadic.util import merge


def _merge_upto_lvl2_then_take_other(d1, d2, resolver, path):
    """"merge tool", suitable for normalization
    of the container configuration"""
    if isinstance(d1, dict) and isinstance(d2, dict) and len(path) < 2:
        # not so deep, merging...
        return merge(d1, d2, resolver, path)
    return d2  # "take other"


class Injectable(type):
    "Provides the __init__ with the suitable args, based on dependencies"

    def __new__(cls, name, bases, dic):
        deps = dic.setdefault('depends_on', tuple())
        if deps and '__init__' not in dic:
            # формирование конструктора
            init = eval("lambda self, %s: %s" % (
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
        result = {}
        for sect, elems in config.items():
            plan = elems.pop('__default__', {})
            section = result[sect] = {}
            for el_name, customization in elems.items():
                if el_name != '__default__':
                    section[el_name] = merge(
                        plan.copy(), customization,
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
        :param group: entity group
        :type group: str
        :param name: entity name
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
            raise KeyError("Unknown group: %r!" % group)
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
        try:
            blueprint, realization = self._get_blueprint(group, name)
        except KeyError:
            raise ValueError("%s:%s is not configured!" % (group, name))

        typ = blueprint.get('__type__')

        if typ == 'static':
            result = realization
        else:
            is_singleton = typ == 'singleton'
            if is_singleton:
                result = self._singletones.get((group, name))
            if not is_singleton or not result:
                deps = {}
                for dep_group, dep_name in blueprint.items():
                    # handle "__interdal__" deps
                    if dep_group.startswith('_'):
                        continue
                    # handle "$static" deps
                    elif dep_group.startswith('$'):
                        deps[dep_group[1:]] = dep_name
                    else:
                        # handle "name:group"-like keys
                        if ':' in dep_group:
                            dep_attr, custom_dep_group = dep_group.split(':')
                        else:
                            dep_attr = custom_dep_group = dep_group
                        if isinstance(dep_name, str):
                            dep_value = self.get(custom_dep_group, dep_name)
                        else:
                            dep_value = [self.get(custom_dep_group, d)
                                         for d in dep_name]
                        deps[dep_attr] = dep_value
                result = realization(**deps)
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
            errors.append('%r is a wrong %s name!' % (':'.join(names), what))

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


__all__ = (Container,)


if __name__ == '__main__':

    # ======================
    # Config validation test
    assert Container.collect_errors({'$grp': {}})
    assert Container.collect_errors({'grp': {'$$name': {}}})
    assert Container.collect_errors({'grp': {'$name': {}}})
    assert Container.collect_errors({'grp': {'name': {'$$attr': ''}}})
    assert Container.collect_errors({'grp': {'name': {'$': ''}}})
    assert Container.collect_errors({'grp': {'$name:grp': {}}})
    assert Container.collect_errors({'grp': {'name:grp:grp': {}}})
    assert Container.collect_errors({'grp': {'name::grp': {}}})
    assert Container.collect_errors({'grp': {'name:': {}}})
    assert Container.collect_errors({'grp': {'name': {'__type__': 'asdf'}}})
    assert Container.collect_errors(
        {'grp': {'name': {'__realizationN__': 'asdf'}}})

    # ============================================
    # complex example
    class Named(object):
        def __str__(self):
            return self.name

    class Engine(object):
        def __init__(self, fuel):
            self.fuel = fuel

        def __str__(self):
            return "%s on %s" % (self.name, self.fuel)

    # 2/3 compatible class
    Vehicle = Injectable(
        'Vehicle',
        (object,),
        {
            'depends_on': ('actuator', 'engine'),
            '__str__': lambda self: (
                "The vehicle, driven by %s, which powered by %s" % (
                    self.actuator, self.engine))
        }
    )

    entities = {
        'demo.veh.Vehicle': Vehicle,
        'demo.act.Wheel': type('Wheel', (Named,), {'name': 'wheel'}),
        'demo.act.Rotor': type('Rotor', (Named,), {'name': 'rotor'}),
        'demo.fue.Gasoline': 'Gasoline',
        'demo.fue.Coal': 'Coal',
        'demo.eng.Diesel': type('Diesel', (Engine,), {'name': 'diesel'}),
        'demo.eng.SteamEngine': type(
            'SteamEngine', (Engine,), {'name': 'steam engine'}),
    }

    config = {
        'vehicle': {
            '__default__': {
                '__realization__': 'demo.veh.Vehicle',
                'engine': 'Diesel'
            },
            'Truck': {'actuator': 'Wheel'},
            'Boat': {'actuator': 'Rotor', 'engine': 'SteamEngine'}
        },
        'actuator': {
            'Wheel': {'__realization__': 'demo.act.Wheel'},
            'Rotor': {'__realization__': 'demo.act.Rotor'},
        },
        'engine': {
            '__default__': {
                'fuel': 'Gasoline'
            },
            'Diesel': {'__realization__': 'demo.eng.Diesel'},
            'SteamEngine': {
                '__realization__': 'demo.eng.SteamEngine',
                'fuel': 'Coal'
            }
        },
        'fuel': {
            # элементы с as-is не инстанцируются, а предоставляются "как есть"
            '__default__': {'__type__': 'static'},
            'Gasoline': {'__realization__': 'demo.fue.Gasoline'},
            'Coal': {'__realization__': 'demo.fue.Coal'},
        }
    }

    cont = type('LocalContainer', (Container,), {
        '_get_entity': staticmethod(entities.get)}
    )(config)

    for name, _, realization in cont.itergroup('vehicle'):
        print('%s :: %s' % (name, realization.__name__))
        print('  ', cont.get('vehicle', name))

    # ===========================================
    # static elements
    def fake_imports(modules):
        def getter(key):
            m, a = key.split('.')
            return modules[m][a]
        return getter

    cont = type('C', (Container,), {'_get_entity': staticmethod(
        fake_imports({
            'module': {
                'square': lambda arg: arg * arg,
                'CONST': 5
            }
        }))}
    )({
        'function': {
            'f': {
                '__realization__': 'module.square',
                'arg': 'x',
            }
        },
        'arg': {
            'x': {'__realization__': 'module.CONST', '__type__': 'static'}
        }
    })
    assert cont.get('function', 'f') == 25

    # ========================
    # singleton-elements

    cont = type('LocalContainer', (Container,), {
        '_get_entity': staticmethod({'List': list}.get)}
    )({
        'container': {
            'list': {
                '__type__': 'singleton',
                '__realization__': 'List'
            }
        }
    })
    cont.get('container', 'list').append(1)
    cont.get('container', 'list').append(2)
    assert cont.get('container', 'list') == [1, 2]

    # =====================================
    # static args

    cont = type('LocalContainer', (Container,), {
        '_get_entity': staticmethod({'Func': lambda x, y: x + y}.get)}
    )({
        'results': {
            'sum_x_y': {
                '__realization__': 'Func',
                '$x': 20,
                '$y': 22,
            }
        }
    })
    assert cont.get('results', 'sum_x_y') == 42

    # =====================================
    # multiple deps from one group

    cont = type('MGContainer', (Container,), {
        '_get_entity': staticmethod({
            'Sum': lambda x, y: x + y,
            'X': 15,
            'Y': 27,
        }.get)
    })({
        'result': {
            'sum': {
                '__realization__': 'Sum',
                'x:arg': 'x',
                'y:arg': 'y'
            }
        },
        'arg': {
            '__default__': {'__type__': 'static'},
            'x': {'__realization__': 'X'},
            'y': {'__realization__': 'Y'}
        }
    })
    assert cont.get('result', 'sum') == 42

    # =================================================
    # multiple deps from one group as a single argument

    cont = type('MGContainer', (Container,), {
        '_get_entity': staticmethod({
            'Sum': lambda nums: nums[0] + nums[1],
            'X': 15,
            'Y': 27,
        }.get)
    })({
        'result': {
            'sum': {
                '__realization__': 'Sum',
                'nums:arg': ['x', 'y']
            }
        },
        'arg': {
            '__default__': {'__type__': 'static'},
            'x': {'__realization__': 'X'},
            'y': {'__realization__': 'Y'}
        }
    })
    assert cont.get('result', 'sum') == 42

    # =================================================
    # "merge tool" test

    fridge = {
        'food': {
            'bread': 1,
            'eggs': {
                'croc': 2,
                'turkey': 7,
            }
        },
        'drinks': {
            'bottles': [0.5, 0.33]
        }
    }

    basket = {
        'food': {
            'bread': 10,
            'carrot': 2,
            'eggs': {
                'rukh': 1
            }
        },
        'drinks': {
            'bottles': [1.0],
            'cans': [0.25, 0.25]
        }
    }

    our_food = merge(fridge, basket, _merge_upto_lvl2_then_take_other)

    assert our_food == {
        'food': {
            'bread': 10,
            'carrot': 2,
            'eggs': {
                'rukh': 1,
            }
        },
        'drinks': {
            'bottles': [1.0],
            'cans': [0.25, 0.25]
        }
    }
