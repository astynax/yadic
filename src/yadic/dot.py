# coding:utf-8

from __future__ import print_function

import json
from collections import deque
from optparse import OptionParser

from yadic.container import Container


def dot(container, include, exclude):
    """
    Builds the .dot-file for container's hierarchy

    :param container: container object
    :type container: yadic.container.Container
    :param include: include list [(group, entity),...]
    :type include: dict
    :param exclude: exclude list [(group, entity),...]
    :type exclude: dict
    """
    assert isinstance(include, dict) and isinstance(exclude, dict)
    data = container._config

    def make_filter(data, consider_from=False):
        groupset = set(g for (g, es) in data.items() if not es)
        nodeset = set(_key_pairs(data))

        def inner(pair):
            from_node, node = pair
            return (from_node and consider_from) or (
                node[0] in groupset or node in nodeset
            )
        return inner

    def branch(node):
        grp, ent = node
        result = []
        for dep_name, val in data[grp][ent].items():
            if not dep_name.startswith('$') and not dep_name.startswith('__'):
                first, rest = val
                if first is None:
                    deps = rest
                else:
                    deps = [val]
                result.extend(deps)
        return result

    initial = _key_pairs(data)

    return _render_digraph(_arc_list(
        initial=initial,
        branch_it=branch,
        include=make_filter(include, True) if include else (lambda _: True),
        exclude=make_filter(exclude)
    ))


def _key_pairs(data):
    """Returns list of paris which contains
    toplevel and second level keys of source dict.

    >>> list(sorted(_key_pairs({'a', {'x': 1, 'y': 2}, 'b', {}})))
    [('a', 'x'), ('a', 'y')]
    """
    return ((k1, k2) for k1, lvl2 in data.items() for k2 in lvl2)


def _arc_list(initial, branch_it, include, exclude):
    result = []
    populated = set()
    nodes = deque((None, n) for n in initial)
    while nodes:
        _, node = pair = nodes.popleft()
        if include(pair) and not exclude(pair):
            result.append(pair)
            if node not in populated:
                populated.add(node)
                nodes.extend((node, child) for child in branch_it(node))
    return result


def _render_digraph(pairs):
    """Renders paris of nodes to .dot-file with directional graph.
    """
    out = ['digraph container {']
    for frm, to in pairs:
        out.append(
            '\t' +
            ('"{}:{}" -> '.format(*frm) if frm else '') +
            '"{}:{}";'.format(*to))
    out.append("}")
    return '\n'.join(out)


def _parse_filter(filter_string):
    """Parses the filter-string (include/exclude).

    Returns the dictionary in form "group -> set of entities"

    >>> _parse_string('names:Tom,Moe;pets:Spot;cars')
    {'names': set(['Tom', 'Moe']), 'pets': set(['Spot']), 'cars': set()}
    """
    result = {}
    for f in filter_string.split(';'):
        if f:
            group, ents = (f.split(':') + [''])[:2]
            result[group] = set(e for e in ents.split(',') if e)
    return result


def _main():
    parser = OptionParser(usage='usage: %prog [options] <CONFIG.JSON>')
    parser.add_option(
        '-i', '--include', dest='include', metavar='FILTER', default=None)
    parser.add_option(
        '-x', '--exclude', dest='exclude', metavar='FILTER', default=None)
    options, args = parser.parse_args()

    if not args:
        parser.error('config file must be provided')
    else:
        conf_file, = args
        with open(conf_file) as f:
            print(dot(
                container=Container(json.load(f)),
                include=_parse_filter(options.include or ''),
                exclude=_parse_filter(options.exclude or '')
            ))


if __name__ == '__main__':
    _main()
