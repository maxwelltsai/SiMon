DEFAULT_CONFIG = {
    'logger': None, 
    'max_concurrent_jobs': 2,
}

current_config = None 

def get_config():
    if current_config is None:
        current_config = DEFAULT_CONFIG.copy()
    print('current config', current_config)
    return current_config
