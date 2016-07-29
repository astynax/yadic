==========================================
Yet Another Dependency Injection Container
==========================================


.. image:: https://travis-ci.org/barsgroup/yadic.svg?branch=master
    :alt: Tests
    :target: https://travis-ci.org/barsgroup/yadic

.. image:: https://img.shields.io/coveralls/barsgroup/yadic.svg?style=flat
    :alt: Coverage
    :target: https://coveralls.io/r/barsgroup/yadic

Usage example:

.. code-block:: python
    :number-lines: 0

    cont = Container({
        # Available engines
        'engine': {
            'Diesel': {'__realization__': 'domain.engine.Diesel'}
        },
        # Available vehicles
        'vehicle': {
            'Truck': {
                '__realization__': 'domain.vehicles.Truck',
                # this will be a constructor argument
                # and value will contain an instance of Diesel class
                'engine': 'Diesel',
            }
        },
        # Cities
        'city': {
            '__default__': {
                '__type__': 'static'  # City won't be instantiated on injection
            },
            'Paris': {
                '__realization__': 'domain.address.Paris'
            },
            'Fleeblebrox': {
                '__realization__': 'domain.address.Fleeblebrox'
            }
        },
        # Cargo
        'stuff': {
            '__default__': {
                '__realization__': '__builtin__.dict'  # target is just a dict
            },
            'food': {
                # at this time $name is just plain kwarg (not an injection)
                '$name': 'Erkburgles'
            },
            'fuel': {
                '$name': 'Unobtaineum'
            },
            'drink': {
                '$name': 'Nuke-Cola'
            }
        },
        # transfers
        'transfer': {
            'from_Paris_with_love': {
                '__realization__': 'domain.transfer.Transfer',
                '__type__': 'singleton',  # every trasfer is unique
                'vehicle': 'Truck',
                # at this time names of kwargs differ from the name of group ("city")
                'from_city:city': 'Paris',
                'to_city:city': 'Fleeblebrox',
                'cargo:stuff': ['food', 'drink']
            }
        }
    })

    tr = cont.get('transfer', 'from_Paris_with_love')

    # this will be equal to

    Transfer(
        vehicle=Truck(engine=Diesel()),
        from_city=Paris,
        to_city=Fleeblebrox,
        cargo=[{'name': 'Erkburgles'}, {'name': 'Nuke-Cola'}]
    )

For more info go to `https://github.com/astynax/yadic <https://github.com/astynax/yadic>`_
