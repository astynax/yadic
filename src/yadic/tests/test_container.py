# coding:utf-8

from yadic.util import merge
from yadic.container import (
    Injectable, Container,
    _merge_upto_lvl2_then_take_other
)


def test_config_normalization():
    """Tests the normalization of config"""
    assert Container._normalize({
        'grp': {
            '__default__': {
                'dep1': 'x',
                'dep2': 'z',
                '$arg': 100,
                'other': ['a', 'b'],
                '$dic': {'a': 1}
            },
            'ent': {
                'dep1:dep1': 'y',
                'other:other': ['c'],
                '$dic': {'b': 2}
            },
            'ent2': {
                '$dic': {'c': 3}
            }
        }
    }) == {
        'grp': {
            'ent': {
                'dep1': ('dep1', 'y'),
                'dep2': ('dep2', 'z'),
                '$arg': 100,
                'other': (None, (('other', 'c'),)),
                '$dic': {'b': 2},
            },
            'ent2': {
                'dep1': ('dep1', 'x'),
                'dep2': ('dep2', 'z'),
                '$arg': 100,
                'other': (None, (('other', 'a'), ('other', 'b'))),
                '$dic': {'c': 3}
            }
        }
    }


def test_config_validation():
    """Tests the validation of the config"""

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


def test_static_elements():
    """Tests the realization of the static elements"""

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


def test_singletones():
    """Tests the realization of the singletone elements"""

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


def test_plain_args():
    """Tests the $plain arguments/deps usage"""

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


def test_multiple_deps_from_one_group():
    """Tests the possibility for using of
    the multiple deps from one group"""

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


def test_multivalue_deps():
    """Tests the multi-value deps"""

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


def test_config_merging_tool():
    """Tests the tool for the config merging"""

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


def test_complex_example():
    """Tests the complex contained example"""

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

    boat, truck = sorted(v[0] for v in cont.itergroup('vehicle'))

    assert str(cont.get('vehicle', boat)) == (
        "The vehicle, driven by rotor, which powered by steam engine on Coal")

    assert str(cont.get('vehicle', truck)) == (
        "The vehicle, driven by wheel, which powered by diesel on Gasoline")
