from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from formations.models import Formation
from news.models import News


def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'home/index.html', {
        'formations': Formation.objects.all()[:3],
        'news': News.objects.all()[:5],
    })
