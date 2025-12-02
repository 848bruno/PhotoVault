from django.shortcuts import render

# Create your views here.
def base(request):
    return render(request, 'base.html')

def index(request):
    return render(request, 'index.html')

def client(request):
    return render(request, 'client.html')

def admin(request):
    return render(request, 'admin.html')


def logout(request):
    return render(request, 'logout.html')

def login(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

def cart(request):
    return render(request, 'cart.html')

def orderHistory(request):
    return render(request, 'orderHistory.html')

def trackOrder(request):
    return render(request, 'trackOrder.html')

def clientManage(request):
    return render(request, 'clientManage.html')