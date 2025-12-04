from django.shortcuts import render
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from datetime import datetime, date
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import Profile
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Photo
# Create your views here.
def base(request):
    return render(request, 'base.html')



def register(request):
    if request.method == 'POST':

        # SAFELY get all fields
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        user_type = request.POST.get('user_type')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        terms = request.POST.get('terms')

        # Validate required fields
        if not all([first_name, last_name, username, email, user_type, password, confirm_password]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'register.html', request.POST)

        # Validate terms
        if not terms:
            messages.error(request, "You must agree to the Terms and Privacy Policy.")
            return render(request, 'register.html', request.POST)

        # Password match check
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html', request.POST)

        # Ensure username is unique
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'register.html', request.POST)

        # Ensure email is unique
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'register.html', request.POST)

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        # ---------------------------------------------------------
        #  CREATE PROFILE associated with the user
        # ---------------------------------------------------------
        Profile.objects.create(
            user=user,
            phone=phone,
            user_type=user_type
        )
        # ---------------------------------------------------------

        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')
    context = {
        'profile_choices': Profile.USER_TYPES,
    }

    return render(request, 'register.html', context)

def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")

        # Allow login using username OR email
        try:
            user = User.objects.get(email=identifier)
            username = user.username
        except User.DoesNotExist:
            username = identifier  # treat as username

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Get user type from profile
            profile = Profile.objects.get(user=user)

            if profile.user_type == "customer":
                return redirect("client")  # URL name
            elif profile.user_type == "photographer":
                return redirect("admin")  # URL name

            # fallback redirect
            return redirect("home")

        else:
            messages.error(request, "Invalid login credentials")

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")

def upload_photos(request):

    if request.method == "POST":
        client_id = request.POST.get("client")
        price = request.POST.get("price")
        category = request.POST.get("category")
        description = request.POST.get("description")
        photos = request.FILES.getlist("photos")
        user_type = request.POST.get('user_type')

        client = User.objects.get(id=client_id)

        for photo in photos:
            Photo.objects.create(
                client=client,
                image=photo,
                price=price,
                category=category,
                description=description,
            )

        messages.success(request, "Photos uploaded successfully!")
        return redirect("admin")

   

    return render(request, "admin.html")


@login_required
def client_gallery(request):
    al = Photo.objects.all()



   
    return render(request, "client.html", {"al": al})





def index(request):
    return render(request, 'index.html')

def client(request):
    return render(request, 'client.html')

def admin(request):
    users = User.objects.filter(profile__user_type="customer")
    return render(request, 'admin.html',{'users':users})





def cart(request):
    return render(request, 'cart.html')

def orderHistory(request):
    return render(request, 'orderHistory.html')

def trackOrder(request):
    return render(request, 'trackOrder.html')

def clientManage(request):
    return render(request, 'clientManage.html')