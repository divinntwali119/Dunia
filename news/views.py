from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from .models import News


def news(request: HttpRequest) -> HttpResponse:
    return render(request, 'news/news.html', {'news': News.objects.all()})
