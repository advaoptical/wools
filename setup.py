from setuptools import setup, find_packages


setup(
    name='wools',
    version='0.1.dev',
    description=(
        "Certified Alpakka Wools for knitting code from Jinja templates"),

    install_requires=['alpakka', 'jinja2'],

    packages=find_packages(include=['wools', 'wools.*']),

    entry_points={'alpakka_wools': [
        'Java=wools.java',
        'Akka=wools.java.akka',
        'Jersey=wools.java.jersey',
    ]},

    keywords=[
        'alpakka', 'pyang', 'yang', 'wrappers', 'wrapper', 'wools', 'wool',
        'templates', 'template', 'jinja2', 'jinja', 'python3',
    ],
)
