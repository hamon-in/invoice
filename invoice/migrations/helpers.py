from alembic.config import Config

def get_config(db):
    cfg = Config()
    for option,value in [("script_location", "alembic"),
                         ("sqlalchemy.url", db)]:
        alembic_cfg.set_main_option(option, value)
    return cfg

    # alembic_cfg.set_section_option("mysection", "foo", "bar")
  
    
