"""Controllers package.

Business logic layer that sits between views (routes) and models.
Controllers handle data manipulation and business rules.
"""
from .hello import HelloController
from .comic import ComicController

__all__ = ['HelloController', 'ComicController']
