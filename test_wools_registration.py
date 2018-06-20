from setuptools import find_packages
from pkg_resources import iter_entry_points

import alpakka

WOOL_PACKAGES = {
    'Java': 'wools.java',
    'Akka': 'wools.java.akka',
}


def test_wools_registration():
    # Check that all Wools are automagically loaded and registered by alpakka
    # via the 'alpakka_wools' entry_points from setup
    assert set(WOOL_PACKAGES.items()) == {
        (ep.name, ep.module_name)
        for ep in iter_entry_points('alpakka_wools')}
    for name, package in WOOL_PACKAGES.items():
        assert name in alpakka.WOOLS
        assert package in alpakka.WOOLS
    # And verify that there are not more wools.* packages registered than
    # expected
    assert set(WOOL_PACKAGES.values()) == {
        item[1].package for item in alpakka.WOOLS.items()}
    # Finally import every available wools.* subpackage...
    for package in find_packages(include=['wools', 'wools.*']):
        __import__(package)
    # ... to check if the number of registerd Wools grows, what would mean
    # that some available Wools are not listed in setup entry_points
    assert set(WOOL_PACKAGES.values()) == {
        item[1].package for item in alpakka.WOOLS.items()}
