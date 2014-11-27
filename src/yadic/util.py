# coding:utf-8
"""Utilties"""


def merge(d1, d2, fn, path=tuple()):
    """
    Updates the dict "d1" with elems of the dict "d2",
    and returns the dict "d1".
    Collisions will be resolved using the function "fn",
    which takes:
    - both of values
    - link to itself
    - path to values (for ex. ("level1", "level2"))
    end returns new value.
    """
    if not isinstance(d1, dict) or not isinstance(d2, dict):
        raise TypeError("Only dicts can be merged!")
    for k, v in d2.items():
        try:
            old_v = d1[k]
        except KeyError:
            d1[k] = v
        else:
            d1[k] = fn(old_v, v, fn, path + (k,))
    return d1


def deep_merge(d1, d2, fn):
    """
    Сливает словари вглубь, функция fn используется
    для не-словарей.
    """
    def merger(x, y, m, p):
        if isinstance(x, dict) and isinstance(y, dict):
            g = merge
        else:
            g = fn
        return g(x, y, m, p)

    return merge(d1, d2, merger)


if __name__ == '__main__':

    def add(x, y, m, p):
        return x + y

    # test: "flat" merge
    assert merge(
        {'a': {'val': 1}, 'b': {'val': 1}},
        {'b': {'val': 2}, 'c': {'val': 5}},
        lambda x, y, m, p: merge(x, y, add)
    ) == {
        'a': {'val': 1},
        'b': {'val': 3},
        'c': {'val': 5}
    }

    # test: deep merge
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
