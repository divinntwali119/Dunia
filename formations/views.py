from django.shortcuts import render

from .models import Formation


def formations(request):
    return render(request, 'formations/formations.html', {
        'formations': Formation.objects.all(),
    })
