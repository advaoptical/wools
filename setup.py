from setuptools import setup


setup(
    name='wools',
    version='0.1.dev',
    description=(
        "Certified Alpakka Wools for knitting code from Jinja templates"),

    install_requires=['alpakka'],

    packages=[
        'wools',
        'wools.java',
        'wools.java.akka',
    ],
    entry_points={'alpakka_wools': [
        'Java=wools.java',
        'Akka=wools.java.akka',
    ]},

    keywords=[
        'alpakka', 'pyang', 'yang', 'wrappers', 'wrapper', 'wools', 'wool',
        'templates', 'template', 'jinja2', 'jinja', 'python3',
    ],
)
