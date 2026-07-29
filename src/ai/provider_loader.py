import importlib
import pkgutil


class ProviderLoader:
    """
    Discovers and imports all provider modules in a package.
    """

    @staticmethod
    def load(package):

        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):

            if is_pkg:
                continue

            importlib.import_module(f"{package.__name__}.{module_name}")