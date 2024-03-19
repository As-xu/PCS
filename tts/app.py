import logging
import sys
logger = logging.getLogger('tts')

from tts.initialization import Initializer
from tts.utils.config_parse import parse_config
from tts.common.base import BaseFlaskApp
from flask.cli import load_dotenv


def create_app():
    args = sys.argv[1:]
    config = parse_config(args)

    try:
        load_dotenv()
        app = BaseFlaskApp(__name__, template_folder='templates')

        if config:
            app.config.from_mapping(config)

        app_initializer = Initializer(app)
        app_initializer.init_app()

        logger.info("""
            TTTTTTTTTTTTTTTTTTTTTTT                             TTTTTTTTTTTTTTTTTTTTTTT  iiii                                              
            T:::::::::::::::::::::T                             T:::::::::::::::::::::T i::::i                                             
            T:::::::::::::::::::::T                             T:::::::::::::::::::::T  iiii                                              
            T:::::TT:::::::TT:::::T                             T:::::TT:::::::TT:::::T                                                    
            TTTTTT  T:::::T  TTTTTTeeeeeeeeeeee    aaaaaaaaaaaaaTTTTTT  T:::::T  TTTTTTiiiiiii    mmmmmmm    mmmmmmm       eeeeeeeeeeee    
                    T:::::T      ee::::::::::::ee  a::::::::::::a       T:::::T        i:::::i  mm:::::::m  m:::::::mm   ee::::::::::::ee  
                    T:::::T     e::::::eeeee:::::eeaaaaaaaaa:::::a      T:::::T         i::::i m::::::::::mm::::::::::m e::::::eeeee:::::ee
                    T:::::T    e::::::e     e:::::e         a::::a      T:::::T         i::::i m::::::::::::::::::::::me::::::e     e:::::e
                    T:::::T    e:::::::eeeee::::::e  aaaaaaa:::::a      T:::::T         i::::i m:::::mmm::::::mmm:::::me:::::::eeeee::::::e
                    T:::::T    e:::::::::::::::::e aa::::::::::::a      T:::::T         i::::i m::::m   m::::m   m::::me:::::::::::::::::e 
                    T:::::T    e::::::eeeeeeeeeee a::::aaaa::::::a      T:::::T         i::::i m::::m   m::::m   m::::me::::::eeeeeeeeeee  
                    T:::::T    e:::::::e         a::::a    a:::::a      T:::::T         i::::i m::::m   m::::m   m::::me:::::::e           
                  TT:::::::TT  e::::::::e        a::::a    a:::::a    TT:::::::TT      i::::::im::::m   m::::m   m::::me::::::::e          
                  T:::::::::T   e::::::::eeeeeeeea:::::aaaa::::::a    T:::::::::T      i::::::im::::m   m::::m   m::::m e::::::::eeeeeeee  
                  T:::::::::T    ee:::::::::::::e a::::::::::aa:::a   T:::::::::T      i::::::im::::m   m::::m   m::::m  ee:::::::::::::e  
                  TTTTTTTTTTT      eeeeeeeeeeeeee  aaaaaaaaaa  aaaa   TTTTTTTTTTT      iiiiiiiimmmmmm   mmmmmm   mmmmmm    eeeeeeeeeeeeee     
        """)

        return app

    except Exception as e:
        logger.exception("初始化TTS失败 %s" % str(e))
        raise e



