from app import app
from app.car.helper import response

@app.errorhandler(404)
def route_not_found(e):
    return response('failed', 'Endpoint not found', 404)


@app.errorhandler(405)
def method_not_found(e):
    return response('failed', 'This method is not allowed for the requested URL', 405)

@app.errorhandler(500)
def internal_server_error(e):
    return response('failed', 'Internal server error', 500)