from flask import request
import colors

def log_request(response,logger):
    if request.path == '/favicon.ico':
        return response
    elif request.path.startswith('/static'):
        return response

    args = dict(request.args)

    log_params = [
        ('method', request.method, 'magenta'),
        ('path', request.path, 'red'),
        ('status', response.status_code, 'yellow'),
        ('params', args, 'yellow')
    ]

    request_id = request.headers.get('X-Request-ID')
    if request_id:
        log_params.append(('request_id', request_id, 'yellow'))

    parts = []
    for name, value, color in log_params:
        part = colors.color("{}={}".format(name, value), fg=color)
        parts.append(part)
    line = " ".join(parts)

    logger.info(line)

    return response