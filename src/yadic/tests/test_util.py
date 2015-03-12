# coding:utf-8

from yadic.util import *


def add(x, y, m, p):
    return x + y


def test_flat_merge():
    """Tests the "flat" (one-level) merge"""

    assert merge(
        {'a': {'val': 1}, 'b': {'val': 1}},
        {'b': {'val': 2}, 'c': {'val': 5}},
        lambda x, y, m, p: merge(x, y, add)
    ) == {
        'a': {'val': 1},
        'b': {'val': 3},
        'c': {'val': 5}
    }


def test_deep_merge():
    """Tests the deep_merge"""

    d1 = {
        'animals': {
            'dogs': {
                'count': 1,
                'names': ['Spot']
            },
            'cats': {
                'count': 2,
                'names': ['Tom', 'Felix']
            }
        },
        'food': {
            'milk': 3
        }
    }

    d2 = {
        'animals': {
            'dogs': {
                'count': 2,
                'names': ['Jaws', 'Bob']
            }
        },
        'food': {
            'milk': 2,
            'sausages': 7
        },
        'junk': {
            'vine glass': 15
        }
    }

    deep_merge(d1, d2, add)

    assert d1 == {
        'animals': {
            'dogs': {
                'count': 3,
                'names': ['Spot', 'Jaws', 'Bob']
            },
            'cats': {
                'count': 2,
                'names': ['Tom', 'Felix']
            }
        },
        'food': {
            'milk': 5,
            'sausages': 7
        },
        'junk': {
            'vine glass': 15
        }
    }


def test_merge_of_dicts_with_prefixed_keys():
    d1 = {
        'a': 1,
        '$b': 2,
        'c': 3
    }
    d2 = {
        '$a': 10,
        'b': 20
    }
    assert merge(d1, d2, lambda x, y, m, p: y) == {
        '$a': 10,
        'b': 20,
        'c': 3
    }
