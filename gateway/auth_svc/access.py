import os

# make http request to auth service, not flask.incoming request
import requests

auth_svc_address = os.environ.get("AUTH_SVC_ADDRESS", "localhost:5000")


# client code for auth service
# NOTE: request here is flask.request, but based on this
# function definition, request could be anything that has `authorization`
def login(request):
    auth = request.authorization
    if not auth:
        return None, ("missing credentials", 401)

    basicAuth = (auth.username, auth.password)
    # HTTP
    # AUTH_SVC_ADDRESS constains both the host and port
    response = requests.post(f"http://{auth_svc_address}/login", auth=basicAuth)

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
