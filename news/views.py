from django.shortcuts import render

# Create your views here.

### Создали первое представление
# ```python
from django.http import HttpResponse

def info(request):
    return HttpResponse("This is the info page.")

def main(request):
    return HttpResponse("Hello, world!")  # вернет страничку с надписью "Hello, world!"

# ```