"""
Application bootstrap for the LTHHC AI Platform.
"""

from src.core.logger import get_logger


class Application:
    """
    Main application container.
    """

    def __init__(self):

        self.logger = get_logger("LTHHC")

        self.logger.info("--------------------------------------------")
        self.logger.info("LTHHC AI Platform Starting")
        self.logger.info("--------------------------------------------")

    def shutdown(self):

        self.logger.info("LTHHC AI Platform Shutdown")