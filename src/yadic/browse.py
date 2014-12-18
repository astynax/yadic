# coging: utf-8

import sys
import json
import os
import re
import tempfile
import webbrowser

from yadic import Container


def build_and_browse(context):
    with open(os.path.join(
        os.path.split(__file__)[0],
        'browseable.html'
    )) as raw:
        template = raw.read()
        for key, val in context.items():
            template = re.sub(r'\{\{%s\}\}' % key, val, template)
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            try:
                f.write(bytes(template, 'UTF-8'))  # for py3
            except TypeError:
                f.write(template)
            webbrowser.open('file://%s' % f.name)


def main():
    fname, prefix = (sys.argv[1:] + [None, None])[:2]
    if not fname:
        print("Usage: cmd config.json [prefix]")
    else:
        try:
            with open(fname) as f:
                config = json.load(f)
        except Exception as e:
            print(e)
            sys.exit(1)
        if prefix:
            for key in prefix.split("."):
                config = config[key]
        cont = Container(config)
        data = {}
        for grp, ents in cont._config.items():
            grp_data = data[grp] = {}
            for name, blueprint in ents.items():
                deps = grp_data[name] = []
                for dep_name, dep_value in blueprint.items():
                    if (
                        dep_name.startswith('$') or
                        dep_name.startswith('_')
                    ):
                        continue
                    if dep_value[0] is None:
                        deps.extend(dep_value[1])
                    else:
                        deps.append(dep_value)
        build_and_browse({
            'title': fname,
            'data': json.dumps(data)
        })


if __name__ == '__main__':
    main()
