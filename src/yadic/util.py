# coding:utf-8
"""Utilties"""


def merge(d1, d2, fn, path=tuple()):
    """
    Updates the dict "d1" with elems of the dict "d2",
    and returns the dict "d1".
    Keys like 'a' and '$a' will be considered equal!
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
            if k.startswith('$'):
                variants = (k, k[1:])
            else:
                variants = ('$' + k, k)
        except AttributeError:
            variants = (k,)
        for key in variants:
            try:
                old_v = d1.pop(key)
            except KeyError:
                continue
            else:
                d1[k] = fn(old_v, v, fn, path + (k,))
                break
        else:
            d1[k] = v
    return d1


def deep_merge(d1, d2, fn):
    """
    Merges d2 into d1 on any level of the depth
    """
    def merger(x, y, m, p):
        if isinstance(x, dict) and isinstance(y, dict):
            g = merge
        else:
            g = fn
        return g(x, y, m, p)

    return merge(d1, d2, merger)
