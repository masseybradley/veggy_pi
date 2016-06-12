from celery import Celery

from exceptions import ImportError, Exception
from www import settings


app = Celery('tasks', broker=settings.BROKER, backend=settings.CELERY_RESULT_BACKEND)

class VeggyMonitor():
    def __init__(self, *args, **kwargs):
        """ 
        the veggy monitor class implements celery event handlers for 
        worker-heartbeat
        """
        self.state = app.events.State()
        self.data = {}

        def get_worker_heartbeat(event):
            print self.state.event(event), event
        
        with app.connection() as connection:
            recv = app.events.Receiver(connection, handlers={
                'worker-heartbeat': get_worker_heartbeat,
            })
            recv.capture(limit=None, timeout=None, wakeup=True)


class VeggyTaskHandler():
    def __init__(self, *args, **kwargs):
        pass

    @app.task
    def add(x, y):
        print x, y
        total = x + y
        print 'total: ', total
        return total
