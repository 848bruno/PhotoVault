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
from .models import Photo, Profile, Cart, Purchase,PrintOrder, PrintOrderItem, OrderStatusUpdate,PrintPrice
from decimal import Decimal
from django.db import transaction, models
from django.http import JsonResponse
from django.db.models import Count, Sum,Avg
from django.utils import timezone
from datetime import timedelta

import json

import requests

from django.views.decorators.csrf import csrf_exempt

from django.conf import settings


def chatbot_page(request):
    return render(request, "chat.html")

# Handles the API POST requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from .models import Photo, Purchase, PrintOrder, PrintOrderItem, Profile, Cart
from datetime import datetime, timedelta
from django.utils import timezone
import json
import requests
from django.conf import settings
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

@csrf_exempt
@login_required
def chatbot_api(request):
    """Comprehensive AI chatbot with full project and user context"""
    
    if request.method == "POST":
        try:
            # Parse request data
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            
            if not user_message:
                return JsonResponse({"reply": "Please provide a message."})
            
            # Get or create conversation history
            conversation_key = f"chat_history_{request.user.id}"
            conversation_history = cache.get(conversation_key, [])
            
            # Add user message to history
            conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": timezone.now().isoformat()
            })
            
            # Build comprehensive context
            system_prompt = build_system_prompt(request.user)
            
            # Prepare messages for API
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add recent conversation history (last 5 exchanges)
            for msg in conversation_history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Call OpenRouter API
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": request.build_absolute_uri('/'),
                        "X-Title": "PhotoVault AI Assistant"
                    },
                    json={
                        "model": "gpt-4.1-mini",  # Can use "mistralai/mistral-7b-instruct:free" for free
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 600,
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_reply = result["choices"][0]["message"]["content"]
                    
                    # Add AI response to history
                    conversation_history.append({
                        "role": "assistant",
                        "content": ai_reply,
                        "timestamp": timezone.now().isoformat()
                    })
                    
                    # Keep only last 20 messages to avoid cache bloat
                    if len(conversation_history) > 20:
                        conversation_history = conversation_history[-20:]
                    
                    # Save updated conversation
                    cache.set(conversation_key, conversation_history, 86400)  # 24 hours
                    
                    return JsonResponse({"reply": ai_reply})
                else:
                    logger.error(f"OpenRouter error {response.status_code}: {response.text}")
                    # Fallback to context-aware response
                    fallback_reply = generate_context_aware_response(request.user, user_message)
                    return JsonResponse({"reply": fallback_reply})
                    
            except requests.exceptions.Timeout:
                return JsonResponse({"reply": "The AI service is taking too long to respond. Here's what I can tell you based on your account..." + generate_context_aware_response(request.user, user_message)})
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error: {str(e)}")
                return JsonResponse({"reply": "I'm having trouble connecting to the AI service. " + generate_context_aware_response(request.user, user_message)})
                
        except json.JSONDecodeError:
            return JsonResponse({"reply": "Invalid request format. Please send valid JSON."}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in chatbot: {str(e)}")
            return JsonResponse({"reply": "Sorry, I encountered an unexpected error. Please try again."})
    
    return JsonResponse({"reply": "Send a POST request with a 'message' field."})

def build_system_prompt(user):
    """Build comprehensive system prompt with user and project context"""
    
    # Get user-specific data
    user_data = get_user_data(user)
    
    # Get project-wide information
    project_info = """PHOTOVAULT PLATFORM INFORMATION:

SERVICES OFFERED:
1. Digital Photo Management
   - Upload photos (JPG, PNG, HEIC, max 10MB)
   - Set custom prices for digital downloads
   - Categorize: Portrait, Landscape, Event, Product, Nature
   - Mark as purchased when bought

2. Physical Print Orders
   - Print sizes: 4x6", 5x7", 8x10", 11x14", 16x20", 20x30"
   - Paper types: Matte, Glossy, Lustre, Metallic
   - Framing: Optional (+KSH 500)
   - Shipping: Standard (5-7d, KSH 200), Express (2-3d, KSH 500), Overnight (1d, KSH 1000)

3. Pricing (Kenya Shillings):
   - Digital photos: Set by photographer
   - Print prices: 
     • 4x6: KSH 200
     • 5x7: KSH 300
     • 8x10: KSH 500
     • 11x14: KSH 800
     • 16x20: KSH 1200
     • 20x30: KSH 2000
   - Tax: 8% on all orders
   - Framing: +KSH 500 per print

4. Order Status Flow:
   Pending → Processing → Printed → Shipped → Delivered → Cancelled

5. User Types:
   - Customer: Browse, purchase photos, order prints
   - Photographer: Upload photos, manage clients, view sales

6. Key Pages & URLs:
   - Dashboard: /client/ (customers) or /admin/ (photographers)
   - Shopping Cart: /cart/
   - Order Tracking: /track-order/
   - Order History: /order-history/
   - Client Management: /client-manage/ (photographers only)
   - Upload Photos: /admin/upload-photos/ (photographers only)

7. Account Management:
   - Profile settings accessible from dashboard
   - Password reset via email
   - Contact: support@photovault.com (9 AM - 6 PM EAT)

8. Common Actions:
   - Upload photos: Use upload modal on admin dashboard
   - Purchase photos: Click "Buy Now" or add to cart
   - Create print order: Select photos → "Order Prints" button
   - Track order: Visit /track-order/ or click order number
   - Clear cart: "Clear Cart" button in cart page
"""
    
    # Build final prompt
    prompt = f"""You are PhotoVault AI Assistant, an intelligent helper for the PhotoVault photo management platform.

CRITICAL CONTEXT - YOU MUST USE THIS INFORMATION:
{user_data}

PLATFORM KNOWLEDGE - REFERENCE THESE DETAILS:
{project_info}

YOUR PERSONALITY & RULES:
1. You are helpful, professional, and concise
2. ALWAYS reference actual user data when relevant (use exact numbers, names, dates)
3. When discussing orders, mention specific order numbers if available
4. For pricing questions, use exact KSH amounts from platform info
5. Suggest specific page URLs or features when appropriate
6. Use markdown formatting: **bold** for emphasis, bullet points for lists
7. If unsure about user-specific data, say "Based on your account..."
8. If asked about something not in context, suggest contacting support@photovault.com
9. Never make up data that isn't provided in the context

RESPONSE FORMATTING:
- Start with a brief acknowledgment if needed
- Provide clear, actionable information
- Use bullet points for steps or lists
- End with a helpful suggestion if appropriate

Now respond to the user's query. Remember to be helpful and reference their actual data when possible."""
    
    return prompt

def get_user_data(user):
    """Extract all relevant user data for context"""
    
    try:
        profile = Profile.objects.get(user=user)
        
        # Basic user info
        user_info = f"""
USER PROFILE:
• Username: {user.username}
• Full Name: {user.get_full_name() or 'Not set'}
• Email: {user.email}
• Phone: {profile.phone or 'Not provided'}
• Account Type: {profile.get_user_type_display()}
• Member Since: {user.date_joined.strftime('%B %d, %Y')} ({ (timezone.now() - user.date_joined).days } days ago)
"""
        
        # Photos data
        uploaded_photos = Photo.objects.filter(photographer=user)
        purchased_photos = Purchase.objects.filter(user=user, status='completed')
        
        photos_info = f"""
PHOTOS:
• Uploaded: {uploaded_photos.count()} photos
• Purchased: {purchased_photos.count()} photos
• In Cart: {Cart.objects.filter(user=user, is_active=True).count()} items
"""
        
        # Add photo categories if any
        if uploaded_photos.exists():
            categories = uploaded_photos.values('category').annotate(count=Count('category'))
            categories_str = ", ".join([f"{cat['category']} ({cat['count']})" for cat in categories])
            photos_info += f"• Categories: {categories_str}\n"
        
        # Orders data
        print_orders = PrintOrder.objects.filter(user=user).order_by('-created_at')
        recent_orders = print_orders[:3]  # Last 3 orders
        
        orders_info = f"""
ORDERS:
• Total Print Orders: {print_orders.count()}
• Active Orders: {print_orders.exclude(status__in=['delivered', 'cancelled']).count()}
• Delivered Orders: {print_orders.filter(status='delivered').count()}
"""
        
        # Add recent orders details
        if recent_orders.exists():
            orders_info += "\nRECENT ORDERS:\n"
            for order in recent_orders:
                items_count = PrintOrderItem.objects.filter(order=order).count()
                orders_info += f"• #{order.order_number}: {order.get_status_display()} - KSH {order.total_amount:.2f} ({order.created_at.strftime('%b %d')}) - {items_count} items\n"
        
        # Financial data
        digital_spent = purchased_photos.aggregate(total=Sum('amount_paid'))['total'] or 0
        print_spent = print_orders.exclude(status='cancelled').aggregate(total=Sum('total_amount'))['total'] or 0
        total_spent = float(digital_spent) + float(print_spent)
        
        financial_info = f"""
FINANCIAL:
• Digital Purchases: KSH {float(digital_spent):.2f}
• Print Orders: KSH {float(print_spent):.2f}
• Total Spent: KSH {total_spent:.2f}
"""
        
        # Cart info
        cart_items = Cart.objects.filter(user=user, is_active=True).select_related('photo')
        if cart_items.exists():
            cart_total = sum(item.photo.price * item.quantity for item in cart_items)
            cart_info = f"""
CART:
• Items in Cart: {cart_items.count()}
• Cart Total: ~KSH {cart_total:.2f}
• Contains: {', '.join(set(item.photo.category for item in cart_items))}
"""
        else:
            cart_info = "\nCART: Empty\n"
        
        # Combine all info
        full_context = user_info + photos_info + orders_info + financial_info + cart_info
        
        # Add photographer-specific data
        if profile.user_type == 'photographer':
            clients = User.objects.filter(profile__user_type='customer')
            client_photos = Photo.objects.filter(photographer__in=clients)
            
            photographer_info = f"""
PHOTOGRAPHER DATA:
• Total Clients: {clients.count()}
• Photos Uploaded for Clients: {client_photos.count()}
• Revenue from Client Photos: KSH {client_photos.aggregate(total=Sum('price'))['total'] or 0:.2f}
"""
            full_context += photographer_info
        
        return full_context
        
    except Profile.DoesNotExist:
        return "User profile not found. Please complete your profile setup."
    except Exception as e:
        logger.error(f"Error getting user data: {str(e)}")
        return f"Error loading user data: {str(e)[:100]}..."

def generate_context_aware_response(user, user_message):
    """Generate intelligent response based on user context when API fails"""
    
    user_message_lower = user_message.lower()
    
    # Check for specific intents
    if any(word in user_message_lower for word in ['photo', 'upload', 'image']):
        try:
            profile = Profile.objects.get(user=user)
            if profile.user_type == 'photographer':
                return "As a photographer, you can upload photos using the 'Upload Photos' button on your admin dashboard. Maximum file size is 10MB per photo. You can set prices and categorize them for your clients."
            else:
                return "You can browse photos in the gallery. If you want to upload photos, you need a photographer account. Contact support@photovault.com to upgrade your account."
        except:
            return "Photo uploads are available for photographer accounts. Maximum file size is 10MB. Supported formats: JPG, PNG, HEIC."
    
    elif any(word in user_message_lower for word in ['order', 'track', 'status']):
        try:
            recent_order = PrintOrder.objects.filter(user=user).order_by('-created_at').first()
            if recent_order:
                return f"Your most recent order is #{recent_order.order_number} ({recent_order.get_status_display()}). Visit /track-order/ to see all your orders and their current status."
            else:
                return "You don't have any print orders yet. Select photos and click 'Order Prints' to create your first order."
        except:
            return "You can track your orders in the 'Track Order' section. Each order has a unique number and status updates."
    
    elif any(word in user_message_lower for word in ['price', 'cost', 'how much']):
        return """Print pricing:
• 4x6: KSH 200
• 5x7: KSH 300  
• 8x10: KSH 500
• 11x14: KSH 800
• 16x20: KSH 1200
• 20x30: KSH 2000
Framing: +KSH 500 per print
Shipping: Standard KSH 200, Express KSH 500, Overnight KSH 1000
Tax: 8% on all orders"""
    
    elif any(word in user_message_lower for word in ['cart', 'basket', 'checkout']):
        try:
            cart_count = Cart.objects.filter(user=user, is_active=True).count()
            if cart_count > 0:
                return f"You have {cart_count} items in your cart. Visit /cart/ to review and checkout. Total will be calculated based on your selections."
            else:
                return "Your cart is empty. Browse photos and click 'Add to Cart' to start shopping."
        except:
            return "Visit /cart/ to view your shopping cart. You can add photos from the gallery."
    
    elif any(word in user_message_lower for word in ['help', 'support', 'contact']):
        return "For support, email support@photovault.com (9 AM - 6 PM EAT). Include your username and any relevant order numbers. You can also check the help sections in your dashboard."
    
    elif any(word in user_message_lower for word in ['account', 'profile', 'settings']):
        profile_type = "photographer" if hasattr(user, 'profile') and user.profile.user_type == 'photographer' else "customer"
        return f"You have a {profile_type} account. Update your profile information from your dashboard settings. For account issues, contact support@photovault.com."
    
    # Default response
    return """I'm your PhotoVault assistant! I can help you with:
• Photo uploads and management
• Print orders and pricing
• Order tracking
• Account questions
• Cart and checkout

What specific help do you need today?"""

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



def pic(request):
     # logged-in user
    photos = Photo.objects.all().order_by("-uploaded_at")
    return render(request, 'pic.html', {'photos': photos})


def index(request):
    return render(request, 'index.html')



def admin(request):
    status_filter = request.GET.get('status', '')

    # Base query: all orders
    base_query = PrintOrder.objects.all().order_by('-created_at')

    # Apply status filter if given
    if status_filter:
        orders = base_query.filter(status=status_filter)
    else:
        orders = base_query

    # Count pending orders
    pending_count = base_query.filter(status='pending').count()

    # Recent orders (latest 5)
    recent_orders = orders[:5]  # you can slice here or in template
    users = User.objects.filter(profile__user_type="customer")

    context = {
        'users':users,
        "orders": orders,
        "pending_count": pending_count,
        "recent_orders": recent_orders,
        "status_filter": status_filter,
    }
    
    
    
    return render(request, 'admin.html',context)


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

##=====print order views=====##
@login_required
@require_POST
def create_print_order(request):
    try:
        data = request.POST
        
        # Get selected photo IDs
        photo_ids = [int(id) for id in data.get('selected_photos', '').split(',') if id]
        if not photo_ids:
            return JsonResponse({'success': False, 'error': 'No photos selected'})
        
        # Get photos - REMOVE is_purchased filter for print orders
        # Print orders can be created for already purchased photos
        photos = Photo.objects.filter(id__in=photo_ids)
        
        if not photos.exists():
            return JsonResponse({'success': False, 'error': 'No valid photos found'})
        
        # Calculate prices
        size = data.get('print_size', '8x10')
        quantity = int(data.get('quantity', 1))
        framing = data.get('framing') == 'on'
        
        # Get print price - add default if not exists
        try:
            print_price = PrintPrice.objects.get(size=size)
            print_unit_price = print_price.price
            framing_price = print_price.framing_price if framing else Decimal('0.00')
        except PrintPrice.DoesNotExist:
            # Create default print prices if they don't exist
            print_unit_price = Decimal('500.00')  # Default price
            framing_price = Decimal('500.00') if framing else Decimal('0.00')
        
        # Shipping costs
        shipping_method = data.get('shipping_method', 'express')
        shipping_costs = {
            'standard': Decimal('200.00'),
            'express': Decimal('500.00'),
            'overnight': Decimal('1000.00')
        }
        shipping_cost = shipping_costs.get(shipping_method, Decimal('500.00'))
        
        # Calculate totals
        subtotal = (print_unit_price + framing_price) * len(photos) * quantity
        tax = subtotal * Decimal('0.08')  # 8% tax
        total = subtotal + shipping_cost + tax
        
        with transaction.atomic():
            # Create print order
            order = PrintOrder.objects.create(
                user=request.user,
                print_size=size,
                paper_type=data.get('paper_type', 'matte'),
                quantity=quantity,
                framing=framing,
                frame_color=data.get('frame_color') if framing else None,
                shipping_method=shipping_method,
                shipping_address=data.get('shipping_address'),
                shipping_city=data.get('shipping_city'),
                shipping_state=data.get('shipping_state'),
                shipping_zip=data.get('shipping_zip'),
                shipping_country='Kenya',
                contact_email=data.get('contact_email'),
                contact_phone=data.get('contact_phone'),
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax=tax,
                total_amount=total,
                status='pending'
            )
            
            # Create order items
            for photo in photos:
                PrintOrderItem.objects.create(
                    order=order,
                    photo=photo,
                    quantity=quantity,
                    unit_price=print_unit_price,
                    notes=f"Print: {size}, Paper: {data.get('paper_type')}" + 
                          (f", Framing: {data.get('frame_color')}" if framing else "")
                )
            
            # Create initial status update
            OrderStatusUpdate.objects.create(
                order=order,
                status='pending',
                notes='Order created successfully',
                updated_by=request.user
            )
            
            # Remove from cart if present
            Cart.objects.filter(user=request.user, photo__in=photos).delete()
        
        messages.success(request, f'Print order #{order.order_number} created successfully!')
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'redirect_url': f'/trackOrder/{order.id}/'
        })
        
    except Exception as e:
        import traceback
        print(f"Error creating print order: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})
@login_required
def track_order_view(request, order_id=None):
    if order_id:
        # Single order view
        order = get_object_or_404(PrintOrder, id=order_id, user=request.user)
        status_updates = order.status_updates.all().order_by('-created_at')
        
        context = {
            'order': order,
            'status_updates': status_updates,
            'single_view': True,
        }
        return render(request, 'trackOrder.html', context)
    
    # All active orders view
    active_orders = PrintOrder.objects.filter(
        user=request.user
    ).exclude(
        status__in=['delivered', 'cancelled']
    ).order_by('-created_at')
    
    recent_orders = PrintOrder.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Calculate statistics
    total_orders = PrintOrder.objects.filter(user=request.user).count()
    delivered_orders = PrintOrder.objects.filter(user=request.user, status='delivered').count()
    total_spent = PrintOrder.objects.filter(
        user=request.user, status='delivered'
    ).aggregate(total=models.Sum('total_amount'))['total'] or Decimal('0.00')
    
    context = {
        'active_orders': active_orders,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'total_spent': total_spent,
    }
    return render(request, 'trackOrder.html', context)




def orderHistory(request):

    orders = PrintOrder.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'orderHistory.html',context)

# Admin Views for Photographers
@login_required
def admin_orders(request):
    status_filter = request.GET.get('status', '')

    # Base query: all orders
    base_query = PrintOrder.objects.all().order_by('-created_at')

    # Apply status filter if given
    if status_filter:
        orders = base_query.filter(status=status_filter)
    else:
        orders = base_query

    # Count pending orders
    pending_count = base_query.filter(status='pending').count()

    context = {
        "orders": orders,
        "pending_count": pending_count,
        "status_filter": status_filter,
    }
    return render(request, "admin_orders.html", context)
@login_required
@require_POST
def update_order_status(request, order_id):
    if not request.user.profile.is_photographer:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    try:
        data = json.loads(request.body)
        order = get_object_or_404(PrintOrder, id=order_id)
        
        # Check if user is the photographer for any photo in the order
        if not order.photos.filter(photographer=request.user).exists():
            return JsonResponse({'success': False, 'error': 'Not authorized'})
        
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if new_status not in dict(PrintOrder.STATUS_CHOICES):
            return JsonResponse({'success': False, 'error': 'Invalid status'})
        
        with transaction.atomic():
            order.status = new_status
            order.save()
            
            OrderStatusUpdate.objects.create(
                order=order,
                status=new_status,
                notes=notes,
                updated_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'new_status': order.get_status_display(),
            'status_class': get_status_class(new_status)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_status_class(status):
    status_classes = {
        'pending': 'warning',
        'processing': 'info',
        'printed': 'primary',
        'shipped': 'success',
        'delivered': 'success',
        'cancelled': 'danger',
    }
    return status_classes.get(status, 'secondary')


@login_required
def trackOrder(request, order_id=None):
    if order_id:
        # Single order view
        order = get_object_or_404(PrintOrder, id=order_id, user=request.user)
        status_updates = order.status_updates.all().order_by('-created_at')
        
        context = {
            'order': order,
            'status_updates': status_updates,
            'single_view': True,
        }
        return render(request, 'trackOrder.html', context)
    
    # All active orders
    active_orders = PrintOrder.objects.filter(
        user=request.user
    ).exclude(
        status__in=['delivered', 'cancelled']
    ).order_by('-created_at')
    
    recent_orders = PrintOrder.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Statistics
    total_orders = PrintOrder.objects.filter(user=request.user).count()
    delivered_orders = PrintOrder.objects.filter(user=request.user, status='delivered').count()
    total_spent = PrintOrder.objects.filter(
        user=request.user, status='delivered'
    ).aggregate(total=models.Sum('total_amount'))['total'] or Decimal('0.00')
    
    context = {
        'active_orders': active_orders,
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'total_spent': total_spent,
    }
    return render(request, 'trackOrder.html', context)



@login_required
def clientManage(request):
    # Only photographers should access this
    if not request.user.profile.is_photographer:
        messages.error(request, 'Access denied. Photographer account required.')
        return redirect('home')
    
    # Get all customers
    customers = User.objects.filter(
        profile__user_type='customer'
    ).select_related('profile').prefetch_related(
        'uploaded_photos', 'purchases', 'print_orders'
    )
    
    # Add statistics to each customer
    customer_list = []
    total_revenue = Decimal('0.00')
    
    for customer in customers:
        # Get photo counts
        total_photos = customer.uploaded_photos.count()
        purchased_photos = customer.purchases.filter(status='completed').count()
        
        # Get order statistics
        print_orders = customer.print_orders.all()
        total_orders = print_orders.count()
        total_spent = print_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_revenue += total_spent
        
        # Calculate average order value
        avg_order_value = Decimal('0.00')
        if total_orders > 0:
            avg_order_value = total_spent / Decimal(str(total_orders))
        
        # Determine activity status
        last_login = customer.last_login
        last_order = print_orders.order_by('-created_at').first()
        last_activity = max(
            last_login or customer.date_joined,
            last_order.created_at if last_order else customer.date_joined
        )
        
        # Determine if new (registered within last 30 days)
        is_new = (timezone.now() - customer.date_joined) < timedelta(days=30)
        
        # Determine if active (activity within last 30 days)
        is_active = False
        if last_activity:
            is_active = (timezone.now() - last_activity) < timedelta(days=30)
        
        # Determine tier based on total spent
        if total_spent > Decimal('5000.00'):
            tier = 'premium'
            tier_class = 'pv-light'
        elif total_spent > Decimal('1000.00'):
            tier = 'standard'
            tier_class = 'info'
        else:
            tier = 'basic'
            tier_class = 'secondary'
        
        # Determine status badge
        if is_new:
            status_text = 'New'
            status_class = 'info'
        elif is_active:
            status_text = 'Active'
            status_class = 'success'
        else:
            status_text = 'Inactive'
            status_class = 'warning'
        
        # Create customer data dict
        customer_data = {
            'user': customer,
            'profile': customer.profile,
            'total_photos': total_photos,
            'purchased_photos': purchased_photos,
            'total_orders': total_orders,
            'total_spent': total_spent,
            'avg_order_value': avg_order_value,
            'last_order_date': last_order.created_at if last_order else None,
            'last_activity': last_activity,
            'is_active': is_active,
            'is_new': is_new,
            'tier': tier,
            'tier_class': tier_class,
            'status_text': status_text,
            'status_class': status_class,
            'client_id': f"CL-{customer.id:04d}",
        }
        
        customer_list.append(customer_data)
    
    # Sort by total spent (descending)
    customer_list.sort(key=lambda x: x['total_spent'], reverse=True)
    
    # Calculate statistics for the stats cards
    total_clients = len(customer_list)
    active_clients = len([c for c in customer_list if c['is_active']])
    premium_clients = len([c for c in customer_list if c['tier'] == 'premium'])
    repeat_rate = 0
    
    if total_clients > 0:
        clients_with_multiple_orders = len([c for c in customer_list if c['total_orders'] > 1])
        repeat_rate = round((clients_with_multiple_orders / total_clients) * 100)
    
    standard_clients = total_clients - premium_clients
    
    context = {
        'customers': customer_list,
        'customer_count': total_clients,
        'total_revenue': total_revenue,
        'total_clients': total_clients,
        'active_clients': active_clients,
        'premium_clients': premium_clients,
        'standard_clients': standard_clients,  # Add this line
        'repeat_rate': repeat_rate,
    }
    return render(request, 'clientManage.html', context)