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
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder


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
    photos = OrderStatusUpdate.objects.all()
    return render(request, 'pic.html', {'photos': photos})


def index(request):
    return render(request, 'index.html')





@login_required
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
    recent_orders = orders[:5]
    users = User.objects.filter(profile__user_type="customer")
    
    # ===== DASHBOARD METRICS =====
    # Date ranges
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_60_days = today - timedelta(days=60)
    previous_30_days = today - timedelta(days=60)
    
    # 1. Total Revenue (Last 30 days)
    recent_orders_30 = PrintOrder.objects.filter(
        created_at__gte=last_30_days
    ).exclude(status='cancelled')
    total_revenue = recent_orders_30.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Previous period for comparison
    prev_orders_30 = PrintOrder.objects.filter(
        created_at__range=[previous_30_days, last_30_days]
    ).exclude(status='cancelled')
    prev_revenue = prev_orders_30.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    # Calculate percentage change
    revenue_change = 0
    if prev_revenue > 0:
        revenue_change = ((total_revenue - prev_revenue) / prev_revenue) * 100
    
    # 2. Total Orders (Last 30 days)
    total_orders_count = recent_orders_30.count()
    prev_orders_count = prev_orders_30.count()
    
    orders_change = 0
    if prev_orders_count > 0:
        orders_change = ((total_orders_count - prev_orders_count) / prev_orders_count) * 100
    
    # 3. Active Clients (Customers who made orders in last 30 days)
    active_clients = User.objects.filter(
        profile__user_type='customer',
        print_orders__created_at__gte=last_30_days
    ).distinct().count()
    
    prev_active_clients = User.objects.filter(
        profile__user_type='customer',
        print_orders__created_at__range=[previous_30_days, last_30_days]
    ).distinct().count()
    
    clients_change = 0
    if prev_active_clients > 0:
        clients_change = ((active_clients - prev_active_clients) / prev_active_clients) * 100
    
    # 4. Average Order Value
    avg_order_value = Decimal('0.00')
    if total_orders_count > 0:
        avg_order_value = total_revenue / Decimal(str(total_orders_count))
    
    prev_avg_order = Decimal('0.00')
    if prev_orders_count > 0:
        prev_avg_order = prev_revenue / Decimal(str(prev_orders_count))
    
    aov_change = 0
    if prev_avg_order > 0:
        aov_change = ((avg_order_value - prev_avg_order) / prev_avg_order) * 100
    
    # ===== ORDER TYPE DISTRIBUTION =====
    order_types_data = recent_orders_30.values('print_size').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('-revenue')
    
    # Prepare for chart
    order_types = {}
    for item in order_types_data:
        size = item['print_size']
        count = item['count']
        revenue = float(item['revenue'] or 0)
        
        if size not in order_types:
            order_types[size] = {'count': 0, 'revenue': 0}
        order_types[size]['count'] += count
        order_types[size]['revenue'] += revenue
    
    # ===== TOP SELLING PHOTOS =====
    top_photos = Photo.objects.filter(
        purchases__status='completed'
    ).annotate(
        total_sales=Count('purchases'),
        total_revenue=Sum('purchases__amount_paid')
    ).order_by('-total_revenue')[:5]
    
    # Format for template
    top_photos_list = []
    for photo in top_photos:
        top_photos_list.append({
            'id': photo.id,
            'image': photo.image,
            'category': photo.get_category_display(),
            'description': photo.description or f"{photo.category} Photo",
            'price': photo.price,
            'sales_count': photo.total_sales or 0,
            'revenue': photo.total_revenue or Decimal('0.00')
        })
    
    # ===== DAILY REVENUE DATA (Last 7 days) =====
    daily_revenue = []
    daily_labels = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        day_revenue = PrintOrder.objects.filter(
            created_at__range=[day_start, day_end]
        ).exclude(status='cancelled').aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        daily_revenue.append(float(day_revenue))
        daily_labels.append(date.strftime('%b %d'))
    
    # ===== CLIENT ACQUISITION =====
    # New clients in last 30 days
    new_clients = User.objects.filter(
        profile__user_type='customer',
        date_joined__gte=last_30_days
    ).count()
    
    # Average first order value - FIXED FOR SQLITE
    # Get all customers with orders
    customers_with_orders = User.objects.filter(
        profile__user_type='customer',
        print_orders__isnull=False
    ).distinct()
    
    avg_first_order = Decimal('0.00')
    if customers_with_orders.exists():
        # Get first order for each customer
        first_order_amounts = []
        for customer in customers_with_orders:
            first_order = customer.print_orders.order_by('created_at').first()
            if first_order:
                first_order_amounts.append(first_order.total_amount)
        
        if first_order_amounts:
            avg_first_order = sum(first_order_amounts) / len(first_order_amounts)
    
    # Repeat rate (clients with >1 order) - FIXED QUERY
    # DON'T re-import Count here, use the one already imported at the top
    
    # Method 1: Get all customers and count their orders
    all_customers = User.objects.filter(profile__user_type='customer')
    repeat_clients = 0
    
    # You can use a simpler approach: count customers with more than 1 order
    for customer in all_customers:
        order_count = customer.print_orders.count()
        if order_count > 1:
            repeat_clients += 1
    
    total_clients = all_customers.count()
    repeat_rate = 0
    if total_clients > 0:
        repeat_rate = (repeat_clients / total_clients) * 100
    
    # ===== PERFORMANCE METRICS =====
    # Average processing time (pending to processing)
    processing_times = []
    completed_orders = PrintOrder.objects.filter(
        status='delivered',
        created_at__gte=last_30_days
    )
    
    for order in completed_orders:
        status_updates = order.status_updates.all().order_by('created_at')
        if len(status_updates) >= 2:
            pending_time = status_updates.filter(status='pending').first()
            processing_time = status_updates.filter(status='processing').first()
            
            if pending_time and processing_time:
                time_diff = (processing_time.created_at - pending_time.created_at).total_seconds() / 86400  # days
                processing_times.append(time_diff)
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 1.2
    
    # On-time delivery rate
    total_delivered = completed_orders.count()
    on_time_delivered = 0  # You would need estimated_delivery field to calculate this
    delivery_rate = 95.4  # Placeholder
    
    # ===== CHART COLORS =====
    chart_colors = [
        'rgba(76, 175, 80, 0.8)',   # PV Light Green
        'rgba(33, 150, 243, 0.8)',  # Info Blue
        'rgba(255, 193, 7, 0.8)',   # Warning Yellow
        'rgba(156, 39, 176, 0.8)',  # Purple
        'rgba(244, 67, 54, 0.8)',   # Red
    ]
    
    # Import json for serialization
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    # ===== CONTEXT =====
    context = {
        'users': users,
        'orders': orders,
        'pending_count': pending_count,
        'recent_orders': recent_orders,
        'status_filter': status_filter,
        
        # Dashboard metrics
        'total_revenue': float(total_revenue),
        'total_orders': total_orders_count,
        'active_clients': active_clients,
        'avg_order_value': float(avg_order_value),
        
        # Percentage changes
        'revenue_change': round(revenue_change, 1),
        'orders_change': round(orders_change, 1),
        'clients_change': round(clients_change, 1),
        'aov_change': round(aov_change, 1),
        
        # Charts data
        'order_types': order_types,
        'top_photos': top_photos_list,
        'daily_revenue': json.dumps(daily_revenue, cls=DjangoJSONEncoder),
        'daily_labels': json.dumps(daily_labels, cls=DjangoJSONEncoder),
        'chart_colors': json.dumps(chart_colors, cls=DjangoJSONEncoder),
        
        # Client acquisition
        'new_clients': new_clients,
        'avg_first_order': float(avg_first_order),
        'repeat_rate': round(repeat_rate, 1),
        
        # Performance metrics
        'avg_processing_time': round(avg_processing_time, 1),
        'delivery_rate': delivery_rate,
        
        # Chart colors array for template (not JSON)
        'chart_colors_list': chart_colors,
    }
    
    return render(request, 'admin.html', context)


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
    return render(request, 'cart.html', context)

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
def admin_orders(request, order_id):
    # Only photographers allowed
    order = get_object_or_404(PrintOrder, id=order_id)

    # Check if user has permission (photographer or order owner)
    if not request.user.profile.is_photographer and order.user != request.user:
        return JsonResponse({'success': False, 'error': 'Access denied'})

    # Get order items
    order_items = order.printorderitem_set.all().select_related('photo')

    # Get status updates
    status_updates = order.status_updates.all().order_by('-created_at')

    # Build order timeline
    timeline = []
    if order.created_at:
        timeline.append({
            'date': order.created_at,
            'status': 'Created',
            'description': 'Order was placed'
        })

    for update in status_updates:
        timeline.append({
            'date': update.created_at,
            'status': update.get_status_display(),
            'description': update.notes or 'Status updated',
            'updated_by': update.updated_by.get_full_name() or update.updated_by.username
        })

    context = {
        'order': order,
        'order_items': order_items,
        'status_updates': status_updates,
        'timeline': timeline,
    }

    # AJAX request → return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'id': order.user.id,
                'username': order.user.username,
                'email': order.user.email,
                'full_name': order.user.get_full_name(),
            },
            'print_size': order.print_size,
            'paper_type': order.paper_type,
            'quantity': order.quantity,
            'framing': order.framing,
            'frame_color': order.frame_color,
            'shipping_method': order.shipping_method,
            'shipping_address': order.shipping_address,
            'shipping_city': order.shipping_city,
            'shipping_state': order.shipping_state,
            'shipping_zip': order.shipping_zip,
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'subtotal': float(order.subtotal),
            'shipping_cost': float(order.shipping_cost),
            'tax': float(order.tax),
            'total_amount': float(order.total_amount),
            'status': order.status,
            'status_display': order.get_status_display(),

            'items': [
                {
                    'id': item.id,
                    'photo_id': item.photo.id if item.photo else None,
                    'photo_url': item.photo.image.url if item.photo and item.photo.image else None,
                    'photo_description': item.photo.description if item.photo else 'Photo',
                    'photo_category': item.photo.get_category_display() if item.photo else 'Unknown',
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.unit_price * item.quantity),
                    'notes': item.notes,
                }
                for item in order_items
            ],

            'status_updates': [
                {
                    'id': update.id,
                    'status': update.status,
                    'status_display': update.get_status_display(),
                    'notes': update.notes,
                    'created_at': update.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_by': update.updated_by.get_full_name() or update.updated_by.username,
                }
                for update in status_updates
            ]
        }

        return JsonResponse({'success': True, 'order': order_data})
    return render(request, 'admin_orders.html', context)



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

    # Count orders by status for stats
    pending_count = base_query.filter(status='pending').count()
    processing_count = base_query.filter(status='processing').count()
    shipped_count = base_query.filter(status='shipped').count()
    
    # Calculate total revenue (excluding cancelled orders)
    total_revenue = base_query.exclude(status='cancelled').aggregate(
        total=models.Sum('total_amount')
    )['total'] or Decimal('0.00')

    context = {
        "orders": orders,
        "pending_count": pending_count,
        "processing_count": processing_count,
        "shipped_count": shipped_count,
        "total_orders_count": base_query.count(),
        "total_revenue": float(total_revenue),
        "status_filter": status_filter,
    }
    return render(request, "admin_orders.html", context)
# Add this import at the top if not already there
from django.http import HttpResponseForbidden

# Remove or comment out the duplicate update_order_status function (the first one)
# Keep only the second one (around line 950)

@login_required
@require_POST
def update_order_status(request, order_id):
    """Update order status with AJAX - SIMPLIFIED VERSION"""
    try:
        data = json.loads(request.body)
        order = get_object_or_404(PrintOrder, id=order_id)
        
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        # Validate status
        valid_statuses = [choice[0] for choice in PrintOrder.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
        
        with transaction.atomic():
            # Update order status
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Create status update record
            OrderStatusUpdate.objects.create(
                order=order,
                status=new_status,
                notes=notes,
                updated_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'new_status': order.get_status_display(),
            'new_status_key': new_status,
            'old_status': old_status,
            'order_number': order.order_number,
            'message': f'Order #{order.order_number} status updated to {order.get_status_display()}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
@login_required
def get_order_details_ajax(request, order_id):
    """Get order details for AJAX requests - SIMPLIFIED"""
    try:
        order = get_object_or_404(PrintOrder, id=order_id)
        
        # Get status updates
        status_updates = order.status_updates.all().order_by('-created_at')
        
        # ========== FIXED: Get status choices from PrintOrder model ==========
        # Import the PrintOrder model's STATUS_CHOICES directly
        status_choices = []
        
        # Loop through all status choices defined in the model
        for choice_value, choice_label in PrintOrder.STATUS_CHOICES:
            status_choices.append({
                'value': choice_value,        # e.g., 'pending', 'processing'
                'label': choice_label,        # e.g., 'Pending', 'Processing'
                'selected': choice_value == order.status  # Mark current status
            })
        # ====================================================================
        
        # Get order items if needed
        try:
            order_items = order.printorderitem_set.all().select_related('photo')
            items_data = [
                {
                    'id': item.id,
                    'photo_id': item.photo.id if item.photo else None,
                    'photo_url': item.photo.image.url if item.photo and item.photo.image else '',
                    'photo_description': item.photo.description if item.photo else 'Photo',
                    'photo_category': item.photo.get_category_display() if item.photo else 'Unknown',
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.unit_price * item.quantity),
                }
                for item in order_items
            ]
        except:
            items_data = []
        
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'id': order.user.id,
                'username': order.user.username,
                'email': order.user.email,
                'full_name': order.user.get_full_name(),
            },
            'print_size': order.print_size,
            'paper_type': order.paper_type,
            'quantity': order.quantity,
            'framing': order.framing,
            'frame_color': order.frame_color,
            'shipping_method': order.shipping_method,
            'shipping_address': order.shipping_address,
            'shipping_city': order.shipping_city,
            'shipping_state': order.shipping_state,
            'shipping_zip': order.shipping_zip,
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'subtotal': float(order.subtotal),
            'shipping_cost': float(order.shipping_cost),
            'tax': float(order.tax),
            'total_amount': float(order.total_amount),
            'status': order.status,
            'status_display': order.get_status_display(),
            
            # ========== ADD THIS: Status choices array ==========
            'status_choices': status_choices,
            # ====================================================
            
            'items': items_data,
            'status_updates': [
                {
                    'id': update.id,
                    'status': update.status,
                    'status_display': update.get_status_display(),
                    'notes': update.notes,
                    'created_at': update.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_by': update.updated_by.get_full_name() or update.updated_by.username,
                }
                for update in status_updates
            ]
        }
        
        return JsonResponse({'success': True, 'order': order_data})
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full traceback to console
        return JsonResponse({'success': False, 'error': str(e)})

def get_status_class(status):
    """Helper function to get CSS class for status"""
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
def order_details(request, order_id):
    """View detailed order information"""
    order = get_object_or_404(PrintOrder, id=order_id)
    
    # Check if user has permission (admin or order owner)
    if not request.user.profile.is_photographer and order.user != request.user:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    # Get order items
    order_items = order.printorderitem_set.all().select_related('photo')
    
    # Get status updates
    status_updates = order.status_updates.all().order_by('-created_at')
    
    # Calculate order timeline
    timeline = []
    if order.created_at:
        timeline.append({
            'date': order.created_at,
            'status': 'Created',
            'description': 'Order was placed'
        })
    
    for update in status_updates:
        timeline.append({
            'date': update.created_at,
            'status': update.get_status_display(),
            'description': update.notes or 'Status updated',
            'updated_by': update.updated_by.get_full_name() or update.updated_by.username
        })
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_updates': status_updates,
        'timeline': timeline,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'id': order.user.id,
                'username': order.user.username,
                'email': order.user.email,
                'full_name': order.user.get_full_name(),
            },
            'print_size': order.print_size,
            'paper_type': order.paper_type,
            'quantity': order.quantity,
            'framing': order.framing,
            'frame_color': order.frame_color,
            'shipping_method': order.shipping_method,
            'shipping_address': order.shipping_address,
            'shipping_city': order.shipping_city,
            'shipping_state': order.shipping_state,
            'shipping_zip': order.shipping_zip,
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'subtotal': float(order.subtotal),
            'shipping_cost': float(order.shipping_cost),
            'tax': float(order.tax),
            'total_amount': float(order.total_amount),
            'status': order.status,
            'status_display': order.get_status_display(),
            'items': [
                {
                    'id': item.id,
                    'photo_id': item.photo.id if item.photo else None,
                    'photo_url': item.photo.image.url if item.photo and item.photo.image else None,
                    'photo_description': item.photo.description if item.photo else 'Photo',
                    'photo_category': item.photo.get_category_display() if item.photo else 'Unknown',
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.unit_price * item.quantity),
                    'notes': item.notes,
                }
                for item in order_items
            ],
            'status_updates': [
                {
                    'id': update.id,
                    'status': update.status,
                    'status_display': update.get_status_display(),
                    'notes': update.notes,
                    'created_at': update.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_by': update.updated_by.get_full_name() or update.updated_by.username,
                }
                for update in status_updates
            ]
        }
        return JsonResponse({'success': True, 'order': order_data})
    
    # Return HTML template for regular requests
    return render(request, 'order_details.html', context)


@login_required
def client_details(request, client_id):
    """View detailed client information"""
    # Check if user is photographer
    if not request.user.profile.is_photographer:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    client = get_object_or_404(User, id=client_id, profile__user_type='customer')
    profile = get_object_or_404(Profile, user=client)
    
    # Get client statistics
    uploaded_photos = Photo.objects.filter(photographer=client).count()
    purchased_photos = Purchase.objects.filter(user=client, status='completed').count()
    
    # Get print orders
    print_orders = PrintOrder.objects.filter(user=client).order_by('-created_at')
    total_orders = print_orders.count()
    
    # Calculate total spent
    total_spent = print_orders.exclude(status='cancelled').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    # Get recent orders
    recent_orders = print_orders[:5]
    
    # Calculate average order value
    avg_order_value = Decimal('0.00')
    if total_orders > 0:
        avg_order_value = total_spent / Decimal(str(total_orders))
    
    # Determine activity status
    last_login = client.last_login
    last_order = print_orders.first()
    last_activity = max(
        last_login or client.date_joined,
        last_order.created_at if last_order else client.date_joined
    )
    is_active = (timezone.now() - last_activity) < timedelta(days=30)
    
    # Determine tier
    if total_spent > Decimal('5000.00'):
        tier = 'premium'
        tier_class = 'pv-light'
    elif total_spent > Decimal('1000.00'):
        tier = 'standard'
        tier_class = 'info'
    else:
        tier = 'basic'
        tier_class = 'secondary'
    
    context = {
        'client': client,
        'profile': profile,
        'uploaded_photos': uploaded_photos,
        'purchased_photos': purchased_photos,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'avg_order_value': avg_order_value,
        'recent_orders': recent_orders,
        'last_activity': last_activity,
        'is_active': is_active,
        'tier': tier,
        'tier_class': tier_class,
        'client_id': f"CL-{client.id:04d}",
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        client_data = {
            'id': client.id,
            'username': client.username,
            'email': client.email,
            'first_name': client.first_name,
            'last_name': client.last_name,
            'full_name': client.get_full_name(),
            'date_joined': client.date_joined.strftime('%Y-%m-%d'),
            'last_login': client.last_login.strftime('%Y-%m-%d %H:%M:%S') if client.last_login else None,
            'phone': profile.phone,
            'uploaded_photos': uploaded_photos,
            'purchased_photos': purchased_photos,
            'total_orders': total_orders,
            'total_spent': float(total_spent),
            'avg_order_value': float(avg_order_value),
            'is_active': is_active,
            'tier': tier,
        }
        return JsonResponse({'success': True, 'client': client_data})
    
    return render(request, 'client_details.html', context)


@login_required
def bulk_assign_photos(request):
    """Bulk assign photos to multiple clients"""
    if not request.user.profile.is_photographer:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            client_ids = data.get('client_ids', [])
            photo_ids = data.get('photo_ids', [])
            
            if not client_ids or not photo_ids:
                return JsonResponse({'success': False, 'error': 'No clients or photos selected'})
            
            clients = User.objects.filter(id__in=client_ids, profile__user_type='customer')
            photos = Photo.objects.filter(id__in=photo_ids)
            
            assigned_count = 0
            for client in clients:
                for photo in photos:
                    # Check if photo is already assigned to this client
                    if not Photo.objects.filter(id=photo.id, photographer=client).exists():
                        # Create a copy of the photo for this client
                        Photo.objects.create(
                            photographer=client,
                            image=photo.image,
                            price=photo.price,
                            category=photo.category,
                            description=photo.description,
                            is_purchased=False,
                        )
                        assigned_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Assigned {assigned_count} photos to {clients.count()} clients',
                'assigned_count': assigned_count
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def delete_clients(request):
    """Delete selected clients"""
    if not request.user.profile.is_photographer:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            client_ids = data.get('client_ids', [])
            
            if not client_ids:
                return JsonResponse({'success': False, 'error': 'No clients selected'})
            
            # Delete clients and their related data
            deleted_count = 0
            for client_id in client_ids:
                try:
                    client = User.objects.get(id=client_id, profile__user_type='customer')
                    # Delete related photos, orders, purchases, cart items
                    Photo.objects.filter(photographer=client).delete()
                    Purchase.objects.filter(user=client).delete()
                    Cart.objects.filter(user=client).delete()
                    PrintOrder.objects.filter(user=client).delete()
                    
                    # Delete profile
                    Profile.objects.filter(user=client).delete()
                    
                    # Delete user
                    client.delete()
                    deleted_count += 1
                    
                except User.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Deleted {deleted_count} client(s)',
                'deleted_count': deleted_count
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})