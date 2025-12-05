from django.shortcuts import render
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from datetime import datetime, date
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import Profile
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .models import Photo, Profile, Cart, Purchase
from decimal import Decimal
from django.http import JsonResponse
import json

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
                photographer=client,
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
 

    return render(request, "client.html", {
    })
    
@login_required
def purchase_photo(request, photo_id):
    photo = Photo.objects.get(id=photo_id, client=request.user)
    photo.is_purchased = True
    photo.save()

    messages.success(request, "Photo purchased successfully!")
    return redirect("client")



def client(request):
   
     # Get all photos that are not purchased yet
    available_photos = Photo.objects.filter(is_purchased=False)
    
    # Get purchased photos for this user
    purchased_photos = Photo.objects.filter(
        is_purchased=True,
        purchases__user=request.user,
        purchases__status='completed'
    ).distinct()
    
    context = {
        'photos': available_photos,
        'purchased_photos': purchased_photos,
        'purchased_count': purchased_photos.count(),
    }

    return render(request, 'client.html', context)

@login_required
def client_page(request):
    return render(request, "client.html")


def pic(request):
     # logged-in user
    photos = Photo.objects.all().order_by("-uploaded_at")
    return render(request, 'pic.html', {'photos': photos})


def index(request):
    return render(request, 'index.html')



def admin(request):
    users = User.objects.filter(profile__user_type="customer")
    return render(request, 'admin.html',{'users':users})


#=====cart views=====#


def cart(request):

      # Get active cart items for the user
    cart_items = Cart.objects.filter(user=request.user, is_active=True).select_related('photo')
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    
    # Shipping cost (you can customize this)
    shipping = Decimal('200.00')  # Standard shipping
    if subtotal >= Decimal('5000.00'):
        shipping = Decimal('0.00')  # Free shipping for orders over 5000
    
    tax_rate = Decimal('8.00')  # 8% tax
    tax = subtotal * (tax_rate / Decimal('100.00'))
    
    total = subtotal + shipping + tax
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'tax_rate': tax_rate,
        'total': total,
        'item_count': cart_items.count(),
    }
    return render(request, 'cart.html',context)

@login_required
@require_POST
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        photo_id = data.get('photo_id')
        quantity = int(data.get('quantity', 1))
        
        photo = get_object_or_404(Photo, id=photo_id, is_purchased=False)
        
        # Check if photo is already in cart
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            photo=photo,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Get updated cart count
        cart_count = Cart.objects.filter(user=request.user, is_active=True).count()
        
        return JsonResponse({
            'success': True,
            'message': f'Added {photo.category} to cart',
            'cart_count': cart_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def remove_from_cart(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        
        cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
        cart_item.delete()
        
        cart_count = Cart.objects.filter(user=request.user, is_active=True).count()
        
        return JsonResponse({
            'success': True,
            'cart_count': cart_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def update_cart_quantity(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
        
        if quantity < 1:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        # Calculate updated totals
        cart_items = Cart.objects.filter(user=request.user, is_active=True).select_related('photo')
        subtotal = sum(item.total_price for item in cart_items)
        
        return JsonResponse({
            'success': True,
            'subtotal': float(subtotal),
            'item_total': float(cart_item.total_price) if quantity > 0 else 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def quick_buy(request, photo_id):
    try:
        photo = get_object_or_404(Photo, id=photo_id, is_purchased=False)
        
        # Create purchase directly
        purchase = Purchase.objects.create(
            user=request.user,
            photo=photo,
            amount_paid=photo.price,
            status='completed'
        )
        
        # Mark photo as purchased
        photo.is_purchased = True
        photo.save()
        
        # Remove from cart if exists
        Cart.objects.filter(user=request.user, photo=photo).delete()
        
        messages.success(request, f'Successfully purchased {photo.category}!')
        return redirect('client')
        
    except Exception as e:
        messages.error(request, f'Error processing purchase: {str(e)}')
        return redirect('client')


@login_required
def checkout(request):
    if request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user, is_active=True)
        
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
        
        # Process each item in cart
        total_amount = Decimal('0.00')
        purchases = []
        
        for cart_item in cart_items:
            if not cart_item.photo.is_purchased:
                purchase = Purchase(
                    user=request.user,
                    photo=cart_item.photo,
                    amount_paid=cart_item.photo.price * cart_item.quantity,
                    status='completed'
                )
                purchases.append(purchase)
                total_amount += purchase.amount_paid
                
                # Mark photo as purchased
                cart_item.photo.is_purchased = True
                cart_item.photo.save()
        
        # Bulk create purchases
        Purchase.objects.bulk_create(purchases)
        
        # Clear the cart
        cart_items.delete()
        
        messages.success(request, f'Successfully purchased {len(purchases)} items! Total: KSH {total_amount}')
        return redirect('client')
    
    return redirect('cart')


@login_required
def clear_cart(request):
    Cart.objects.filter(user=request.user, is_active=True).delete()
    messages.success(request, 'Cart cleared successfully')
    return redirect('cart')




def orderHistory(request):
    return render(request, 'orderHistory.html')

def trackOrder(request):
    return render(request, 'trackOrder.html')

def clientManage(request):
    return render(request, 'clientManage.html')