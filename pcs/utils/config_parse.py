from configparser import ConfigParser, RawConfigParser
from .path import make_dirs
import logging
import optparse
import os
import secrets

logger = logging.getLogger(__name__)

SECRET_KEY = secrets.token_hex()


LogNameDict = {
    'CRITICAL': logging.CRITICAL,
    'FATAL': logging.FATAL,
    'ERROR': logging.ERROR,
    'WARN': logging.WARNING,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET,
}


class PCSOption(optparse.Option, object):
    def __init__(self, *opts, **attrs):
        super(PCSOption, self).__init__(*opts, **attrs)


class ConfigManager(object):
    def __init__(self):

        self.options = {
            "SECRET_KEY": SECRET_KEY,
            "JWT_SECRET_KEY": SECRET_KEY,
        }
        self.config_file = None
        self.parser = optparse.OptionParser(option_class=PCSOption)

        group = optparse.OptionGroup(self.parser, "Common")
        group.add_option("-c", "--config", dest="CONFIG", help="配置文件")
        self.parser.add_option_group(group)
        self.parse_config()

    def parse_config(self, args=None):
        self._parse_config(args)

    def _parse_config(self, args=None):
        if args is None:
            args = []
        opt, args = self.parser.parse_args(args)

        self.config_file = os.path.abspath(opt.CONFIG or '')
        self.load()

        self.options["DATA_DIR"] = self.options.get("DATA_DIR") or os.path.join(self.options["BASE_DIR"], 'data')
        self.options["LOG_DIR"] = self.options.get("LOG_DIR") or os.path.join(self.options["BASE_DIR"], 'log')
        self.options["DB_CONF_PATH"] = os.path.join(os.path.abspath(''), "db_config.json")
        make_dirs([self.options["DATA_DIR"], self.options["LOG_DIR"]])

        log_level = self.options["LOG_LEVEL"]
        if self.options["LOG_LEVEL"] in LogNameDict.keys():
            self.options["LOG_LEVEL"] = LogNameDict.get(log_level)
        else:
            self.options["LOG_LEVEL"] = logging.INFO

    def load(self):
        defaults = {
            "BASE_DIR": os.path.abspath(''),
            "LOG_FILE_NAME": "pcs_server.log",
            "LOG_LEVEL": logging.INFO,
        }
        p = RawConfigParser(defaults=defaults)
        try:
            p.read([self.config_file])
            if not p.sections():
                self.options.update(defaults)
                return None

            for key in p.sections():
                for (name, value) in p.items(key):
                    name = name.upper()
                    if value == 'True' or value == 'true':
                        value = True
                    if value == 'False' or value == 'false':
                        value = False
                    if value == 'None':
                        value = None
                    if isinstance(value, str) and value.isdigit():
                        value = int(value)
                    self.options[name] = value
        except IOError:
            pass
        except ConfigParser.NoSectionError:
            pass
        return None

    def get(self, key, default=None):
        return self.options.get(key, default)

    def pop(self, key, default=None):
        return self.options.pop(key, default)

    def keys(self):
        return self.options.keys()

    def __setitem__(self, key, value):
        self.options[key] = value

    def __getitem__(self, key):
        return self.options.get(key) or None


def parse_config(args=None):
    config = ConfigManager()
    config.parse_config(args)
    return config


