a = "2025-09-26 10:48:40,485 | DEBUG | Application | Backend server exec response: {'status': 'ok', 'result': True}"


def _on_log_updated( data):
    if 'DEBUG' in data:
        return
    print(-1, data)

_on_log_updated(a)