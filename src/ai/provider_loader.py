import importlib
import pkgutil


class ProviderLoader:
    """
    Dynamically imports every module in a package.

    Importing a module causes any registration decorators
    within that module to execute.
    """

    @staticmethod
    def load(package) -> None:
        """
        Import every module in the supplied package.

        Args:
            package: The package containing provider modules.
        """

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            importlib.import_module(
                f"{package.__name__}.{module_name}"
            )