# coding:utf-8

from __future__ import print_function

import sys
import json
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

    def checker(dic):
        def inner(grp, ent):
            ents = dic.get(grp)
            if ents is None:
                return False
            return not ents or ent in ents
        return inner

    def keep_all(*args):
        return True

    out = []
    already = set()

    def render(grp, ent, dep, dep_render, skip):
        dep_group, dep_ent = dep
        if skip(dep_group, dep_ent):
            out.append('\t"%s:%s";' % (grp, ent))
        else:
            out.append('\t"%s:%s" -> "%s:%s";' % (
                grp, ent, dep_group, dep_ent))
            if dep_render and dep not in already:
                # we need to go deeper!
                dep_render(
                    keep_all, skip,
                    dep_group,
                    [(dep_ent, data[dep_group][dep_ent])],
                    dep_render
                )
            already.add(dep)

    def render_group(keep, skip, group, group_data, dep_render):
        for ent, deps in group_data:
            if keep(group, ent) and not skip(group, ent):
                for dep, val in deps.items():
                    if dep.startswith('$') or dep.startswith('__'):
                        continue
                    first, rest = val
                    targets = rest if first is None else [val]
                    for d in targets:
                        render(group, ent, d, dep_render, skip)

    # if the include list is non-empty,
    # rendering must be the recursive one
    if include:
        dep_render = render_group
    else:
        dep_render = None

    for group, ents in data.items():
        render_group(
            checker(include) if include else keep_all,
            checker(exclude),
            group, ents.items(),
            dep_render=dep_render
        )

    return True, 'digraph container {\n%s\n}' % ('\n'.join(out))


def _parse_filter(filter_string):
    """
    Parses the filter-string (include/exclude)
    into dictionary "group -> set of entities"

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
    parser = OptionParser(usage='usage: %prog [options] config')
    parser.add_option(
        '-p', '--prefix', dest='prefix', metavar='PREFIX', default=None)
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
            data = json.load(f)
            if options.prefix:
                try:
                    for k in options.prefix.split('.'):
                        data = data[k]
                except KeyError:
                    parser.error('Bad PREFIX format')
            ok, res = dot(
                container=Container(data),
                include=_parse_filter(options.include or ''),
                exclude=_parse_filter(options.exclude or '')
            )
            if ok:
                print(res)
            else:
                sys.stderr.write(res + '\n')


if __name__ == '__main__':
    _main()
