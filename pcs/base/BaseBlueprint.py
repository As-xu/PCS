from flask import Blueprint
import logging

logger = logging.getLogger(__name__)


class BaseBlueprint(Blueprint):
    pass


pcs_bp = BaseBlueprint('pcs_bp', __name__)


class BlueprintFactory:
    @classmethod
    def create_bp(cls, name, import_name, *args, **kwargs):
        bp = BaseBlueprint(name, import_name, *args, **kwargs)
        pcs_bp.register_blueprint(bp)
        return bp