from django.contrib.staticfiles import finders
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from formations.models import Formation
from news.models import News


def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'home/index.html', {
        'formations': Formation.objects.all()[:3],
        'news': News.objects.all()[:5],
    })


def service_worker(request):
    worker_path = finders.find('js/service-worker.js')
    if not worker_path:
        raise Http404
    response = FileResponse(open(worker_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response
