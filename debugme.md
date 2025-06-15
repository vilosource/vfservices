During testing we tried to visit: https://website.vfservices.viloforge.com/accounts/login/

But we got the following error:

Forbidden (403)
CSRF verification failed. Request aborted.

Help
Reason given for failure:

    Origin checking failed - https://website.vfservices.viloforge.com does not match any trusted origins.
    
In general, this can occur when there is a genuine Cross Site Request Forgery, or when Django’s CSRF mechanism has not been used correctly. For POST forms, you need to ensure:

Your browser is accepting cookies.
The view function passes a request to the template’s render method.
In the template, there is a {% csrf_token %} template tag inside each POST form that targets an internal URL.
If you are not using CsrfViewMiddleware, then you must use csrf_protect on any views that use the csrf_token template tag, as well as those that accept the POST data.
The form has a valid CSRF token. After logging in in another browser tab or hitting the back button after a login, you may need to reload the page with the form, because the token is rotated after a login.
You’re seeing the help section of this page because you have DEBUG = True in your Django settings file. Change that to False, and only the initial error message will be displayed.

You can customize this page using the CSRF_FAILURE_VIEW setting.


- 
debug the issue.

you should debug this by using the docker-compose.yml 
docker compose build 
docker compose start
visit the web page, 
login as admin/admin123 
you should understand how the code is working via traefik 





