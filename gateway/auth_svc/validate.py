import os

import requests

auth_svc_address = os.environ.get("AUTH_SVC_ADDRESS", "localhost:5000")


def token(request):
    if not "Authorization" in request.headers:
        return None, ("missing authorization header", 401)

    # TODO: we can just forward the request?
    # probably do it for both `token` and `validate
    response = requests.post(
        f"http://{auth_svc_address}/validate",
        headers={"Authorization": request.headers["Authorization"]},
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
