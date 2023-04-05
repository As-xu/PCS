from flask import Blueprint
import logging

logger = logging.getLogger(__name__)


class BaseBlueprint(Blueprint):
    pass


base_bp = BaseBlueprint('pcs_bp', __name__)


class BlueprintFactory:
    @classmethod
    def create_bp(cls, name, import_name, *args, **kwargs):
        bp = BaseBlueprint(name, import_name, *args, **kwargs)
        base_bp.register_blueprint(bp)
        return bp