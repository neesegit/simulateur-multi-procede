import functools
import logging
import time
from typing import Any

logger: logging.Logger = logging.getLogger(__name__)

def safe_run(func):
    """Décorateur pour gérer proprement les erreurs et interruptions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.warning("Simulation interrompue par l'utilisateur")
            print("\nSimulation interrompue par l'utilisateur")
            return 1
        except Exception as e:
            logger.error(f"Erreur fatale : {e}", exc_info=True)
            print(f"\nErreur : {e}")
            print("Consultez le log pour plus de détails")
            return 1
    return wrapper

def timed(func):
    """Décorateur pour mesurer la durée d'exécution d'une fonction"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start: float = time.time()
        result = func(*args, **kwargs)
        duration: float = time.time() - start
        logger.info(f"Durée de '{func.__name__}' : {duration:.2f}s")
        return result
    return wrapper

def step(title: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            print("\n" + "-"*70)
            print(f"{title}")
            print("-"*70)
            return func(*args, **kwargs)
        return wrapper
    return decorator

