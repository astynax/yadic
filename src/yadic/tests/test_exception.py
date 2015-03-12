# coding: utf-8

from yadic.container import Container, EntityConfiguringError


class FakeConainer(Container):
    def _get_entity(self, name):
        if name == 'LAMBDA':
            return lambda: None
        else:
            return dict


def test_exception():
    cont = FakeConainer({
        'group_a': {
            'a': {
                '__realization__': 'LAMBDA',
                '$arg': 42
            }
        },
        'group_b': {
            'b': {
                '__realization__': 'DICT',
                'dep:group_a': 'a'
            }
        },
        'group_c': {
            'c': {
                '__realization__': 'DICT',
                'dep:group_b': 'b'
            }
        }
    })

    try:
        assert not cont.get('group_c', 'c')
    except EntityConfiguringError as e:
        assert e.path == ('group_c:c', 'group_b:b', 'group_a:a')
        assert isinstance(e.exc, TypeError)
