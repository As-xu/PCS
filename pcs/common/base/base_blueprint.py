import logging
from flask import Blueprint, current_app
from flask_jwt_extended import verify_jwt_in_request
from functools import wraps


logger = logging.getLogger(__name__)


def verify_func(fn, no_verify=False, fresh=False, refresh=False, locations=None, verify_type=True, skip_revocation_check=False):
    @wraps(fn)
    def decorator(*args, **kwargs):
        verify_jwt_in_request(
            no_verify, fresh, refresh, locations, verify_type, skip_revocation_check
        )
        return current_app.ensure_sync(fn)(*args, **kwargs)

    return decorator


class BaseBlueprint(Blueprint):
    def route(self, rule, no_verify=False, fresh=False, refresh=False, locations=None, verify_type=True,
              skip_revocation_check=False, **options):
        def decorator(f):
            f = verify_func(f, no_verify, fresh, refresh, locations, verify_type, skip_revocation_check)
            endpoint = options.pop("endpoint", None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f

        return decorator


base_bp = BaseBlueprint('pcs_bp', __name__)


class BlueprintFactory:
    @classmethod
    def create_bp(cls, name, import_name, *args, **kwargs):
        bp = BaseBlueprint(name, import_name, *args, **kwargs)
        base_bp.register_blueprint(bp)
        return bp