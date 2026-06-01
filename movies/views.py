# views.py is where logic and processing happens. It takes data, does something with it, and decides what to send to the template.

# -----------------------------------------------------------------------------------


# What is views.py? It is the "Logic Hub." It acts as a middleman that talks to the Database (Models) and the User Interface (Templates).

# If the models.py is the Storage Room and urls.py is the Signpost, then the views.py is the Manager who actually does the work.

# The "Manager" Logic
# A view is just a Python function that follows a simple 3-Step Process:

# Receive: It gets a "Request" from the user (via the URL).
# Fetch: It goes to the database (Models) to grab the right data.
# Deliver: It sends that data to a webpage (Template) for the user to see.

from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking, SeatReservation, Payment
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta, datetime
import re
import threading
import logging
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.db.models import Count, Q,Sum
from django.db.models.functions import ExtractHour


def is_admin(user):
    return user.is_authenticated and user.is_staff

    # What this does:
    # is_authenticated → is the user logged in?
    # is_staff        → is the user a staff member?

    # Both must be True → allowed
    # Either is False  → blocked



def get_embed_url(trailer_url):
    if not trailer_url:
        return None
    youtube_pattern = re.compile(
        r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    )
    match = youtube_pattern.search(trailer_url)
    if match:
        video_id = match.group(4)
        return f"https://www.youtube.com/embed/{video_id}"
    return None


def movie_list(request):
    search_query = request.GET.get("search")
    genre_filter = request.GET.get("genre")
    language_filter = request.GET.get("language")

    movies = Movie.objects.all()

    if search_query:
        movies = movies.filter(name__icontains=search_query)
    if genre_filter:
        movies = movies.filter(genre=genre_filter)
    if language_filter:
        movies = movies.filter(language=language_filter)

    all_genres = Movie.objects.values_list("genre", flat=True).distinct()
    all_languages = Movie.objects.values_list("language", flat=True).distinct()

    return render(
        request,
        "movies/movie_list.html",
        {
            "movies": movies,
            "all_genres": all_genres,
            "all_languages": all_languages,
            "selected_genre": genre_filter,
            "selected_language": language_filter,
        },
    )


def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theater = Theater.objects.filter(movie=movie)
    embed_url = get_embed_url(movie.trailer_url)
    return render(
        request,
        "movies/theater_list.html",
        {"movie": movie, "theaters": theater, "embed_url": embed_url},
    )


def send_booking_email(user, booked_seats, theaters):
    # booked_seats is a LIST — one email for ALL seats booked at once
    logger = logging.getLogger(__name__)

    # Join all seat numbers: "A1, A2, B3"
    seat_numbers = ", ".join([seat.seat_number for seat in booked_seats])

    context = {
        "user_name": user.username,
        "movie_name": theaters.movie.name,
        "theater_name": theaters.name,
        "show_time": theaters.time,
        "seat_number": seat_numbers,
        "booked_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
    }

    html_content = render_to_string("movies/booking_confirmation_email.html", context)

    email = EmailMessage(
        subject=f"Booking Confirmed - {context['movie_name']}",
        body=html_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
    )
    email.content_subtype = "html"

    for attempt in range(3):
        try:
            email.send()
            logger.info(f"Email sent to {user.email} on attempt {attempt + 1}")
            break
        except Exception as e:
            logger.error(f"Email attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                logger.error(
                    f"All 3 attempts failed. Email not delivered to {user.email}"
                )


@login_required(login_url="/login/")
def book_seats(request, theater_id):
    theaters = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theaters)

    if request.method == "POST":
        selected_Seats = request.POST.getlist("seats")

        if not selected_Seats:
            return render(
                request,
                "movies/seat_selection.html",
                {"theaters": theaters, "seats": seats, "error": "No seat selected"},
            )

        error_seats = []
        valid_seat_ids = []

        for seat_id in selected_Seats:
            with transaction.atomic():
                seat = Seat.objects.select_for_update().get(
                    id=seat_id, theater=theaters
                )

                # check if seat is already permanently booked
                if seat.is_booked:
                    error_seats.append(seat.seat_number)
                    continue

                # check if seat is temporarily locked by another user
                active_reservation = SeatReservation.objects.filter(
                    seat=seat,
                    status="pending",
                    expires_at__gt=timezone.now()
                ).exclude(user=request.user).exists()
                # exclude current user — so if same user resubmits,
                # their own reservation doesn't block them

                if active_reservation:
                    error_seats.append(seat.seat_number)
                    continue

                # delete any OLD reservation by this user for this seat
                # (in case they came back after timeout and reselected)
                SeatReservation.objects.filter(
                    seat=seat,
                    user=request.user
                ).delete()

                # create fresh 2 minute lock
                SeatReservation.objects.create(
                    user=request.user,
                    seat=seat,
                    expires_at=timezone.now() + timedelta(minutes=2)
                )

                valid_seat_ids.append(str(seat_id))

        if error_seats:
            error_message = (
                f"The following seats are already booked or reserved: {','.join(error_seats)}"
            )
            return render(
                request,
                "movies/seat_selection.html",
                {"theaters": theaters, "seats": seats, "error": error_message},
            )

        # all seats reserved — now go to payment
        # pass seat ids as comma separated string in URL
        seat_ids_str = ','.join(valid_seat_ids)
        return redirect(f"/movies/theater/{theater_id}/payment/?seats={seat_ids_str}")

    # GET request — show seat map
    # get all currently locked seats to show as pending in UI
    reserved_seat_ids = SeatReservation.objects.filter(
        status="pending",
        expires_at__gt=timezone.now()
    ).values_list("seat_id", flat=True)

    return render(
        request,
        "movies/seat_selection.html",
        {
            "theaters": theaters,
            "seats": seats,
            "reserved_seat_ids": reserved_seat_ids
        }
    )
    
@login_required(login_url="/login/")
def initiate_payment(request, theater_id):
    theater = get_object_or_404(Theater, id=theater_id)

    # GET request — came from book_seats redirect with seat ids in URL
    if request.method == "GET":
        seat_ids_str = request.GET.get("seats", "")
        if not seat_ids_str:
            return redirect('book_seats', theater_id=theater_id)

        selected_seats = seat_ids_str.split(',')

        # validate seats — must still be reserved by this user
        seats = []
        for seat_id in selected_seats:
            seat = get_object_or_404(Seat, id=seat_id, theater=theater)

            # confirm this user has an active reservation for this seat
            has_reservation = SeatReservation.objects.filter(
                seat=seat,
                user=request.user,
                status="pending",
                expires_at__gt=timezone.now()
            ).exists()

            if not has_reservation:
                # reservation expired — send back to seat selection
                return render(request, 'movies/seat_selection.html', {
                    'theaters': theater,
                    'seats': Seat.objects.filter(theater=theater),
                    'error': 'Your seat reservation expired. Please reselect your seats.'
                })

            seats.append(seat)

        # calculate amount
        amount = len(seats) * 200 * 100  # rupees * 100 = paise

        # create razorpay order
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })

        # save Payment record with amount
        payment = Payment.objects.create(
            user=request.user,
            theater=theater,
            razorpay_order_id=razorpay_order['id'],
            status='created',
            amount=amount,
        )
        payment.seats.set(seats)

        return render(request, 'movies/payment.html', {
            'payment': payment,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': amount,
            'theater': theater,
            'seats': seats,
        })

    return redirect('book_seats', theater_id=theater_id)

@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        
        params = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }
        
        try:
            client.utility.verify_payment_signature(params)
            
            # signature matched - payment genuine
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            
            # idempotency check - already processed? skip
            if payment.status == 'paid':
                return redirect('profile')
            
            # update payment record
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = 'paid'
            payment.save()
            
            # create actual bookings for each seat
            booked_seats = []
            for seat in payment.seats.all():
                Booking.objects.create(
                    user=request.user,
                    seat=seat,
                    movie=payment.theater.movie,
                    theater=payment.theater
                )
                seat.is_booked = True
                seat.save()
                booked_seats.append(seat)
            
            # send one email for all seats together
            thread = threading.Thread(
                target=send_booking_email,
                args=(request.user, booked_seats, payment.theater)
            )
            thread.start()
            
            return redirect('profile')
        
        except Exception:
            # signature didn't match = fake or failed payment
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                payment.status = 'failed'
                payment.save()
            except Payment.DoesNotExist:
                pass
            
            return redirect('payment_failed')
    
    return redirect('profile')

def payment_failed(request):
    return render(request, 'movies/payment_failed.html')

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_dashboard(request):

    # CACHING — check RAM first before hitting database
    # cache.get() → looks in RAM → found? return immediately (cache HIT)
    # cache.get() → not found? → run the query (cache MISS)
    # cache.set() → store result in RAM for 300 seconds (5 minutes)

    total_bookings = cache.get('total_bookings')
    if total_bookings is None:
        total_bookings = Booking.objects.count()
        cache.set('total_bookings', total_bookings, 300)

    confirmed = cache.get('confirmed')
    if confirmed is None:
        confirmed = Booking.objects.filter(is_cancelled=False).count()
        cache.set('confirmed', confirmed, 300)

    cancelled = cache.get('cancelled')
    if cancelled is None:
        cancelled = Booking.objects.filter(is_cancelled=True).count()
        cache.set('cancelled', cancelled, 300)

    if total_bookings > 0:
        cancel_rate = round((cancelled / total_bookings) * 100, 1)
    else:
        cancel_rate = 0

    top_movies = cache.get('top_movies')
    if top_movies is None:
        top_movies = list(Movie.objects.annotate(
            booking_count=Count('booking')
        ).order_by('-booking_count')[:5])
        cache.set('top_movies', top_movies, 300)

    peak_hours = cache.get('peak_hours')
    if peak_hours is None:
        peak_hours = list(Booking.objects.annotate(
            hour=ExtractHour('booked_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour'))
        cache.set('peak_hours', peak_hours, 300)

    # BUSIEST THEATERS — ranked by occupancy rate (booked seats / total seats)
    # annotate() → adds calculated columns directly in the database query
    # total_seats → count ALL seats linked to this theater
    # booked_seats → count only seats where is_booked=True (using Q filter)
    # This never loads all seat objects into memory — pure DB aggregation
    busiest_theaters = cache.get('busiest_theaters')
    if busiest_theaters is None:
        busiest_theaters = list(Theater.objects.annotate(
            total_seats=Count('seats'),
            booked_seats=Count('seats', filter=Q(seats__is_booked=True)),
        ).order_by('-booked_seats')[:5])
        cache.set('busiest_theaters', busiest_theaters, 300)

    # REVENUE — aggregate from Payment model where status='paid'
    # Sum('amount') → adds up all amount values in DB, never loads into memory
    # // 100 → convert paise to rupees (Razorpay stores in paise)
    # (result['total'] or 0) → if no payments yet, total is None, use 0 instead
    today = timezone.now().date()

    daily_revenue = cache.get('daily_revenue')
    if daily_revenue is None:
        result = Payment.objects.filter(
            status='paid',
            created_at__date=today
        ).aggregate(total=Sum('amount'))
        daily_revenue = (result['total'] or 0) // 100  # paise to rupees
        cache.set('daily_revenue', daily_revenue, 300)

    weekly_revenue = cache.get('weekly_revenue')
    if weekly_revenue is None:
        result = Payment.objects.filter(
            status='paid',
            created_at__date__gte=today - timedelta(days=7)
        ).aggregate(total=Sum('amount'))
        weekly_revenue = (result['total'] or 0) // 100
        cache.set('weekly_revenue', weekly_revenue, 300)

    monthly_revenue = cache.get('monthly_revenue')
    if monthly_revenue is None:
        result = Payment.objects.filter(
            status='paid',
            created_at__month=today.month,
            created_at__year=today.year
        ).aggregate(total=Sum('amount'))
        monthly_revenue = (result['total'] or 0) // 100
        cache.set('monthly_revenue', monthly_revenue, 300)

    context = {
        'total_bookings': total_bookings,
        'confirmed': confirmed,
        'cancelled': cancelled,
        'cancel_rate': cancel_rate,
        'top_movies': top_movies,
        'peak_hours': peak_hours,
        'busiest_theaters': busiest_theaters,  # top 5 theaters by occupancy
        'daily_revenue': daily_revenue,        # revenue today in rupees
        'weekly_revenue': weekly_revenue,      # revenue last 7 days in rupees
        'monthly_revenue': monthly_revenue,    # revenue this month in rupees
    }
    # What these two decorators do together: (To block normal user in admin panel)
    #     @login_required        → are you logged in?
    #                           NO  → go to /login/
    #                           YES ↓
    # @user_passes_test      → is_admin(user) returns True?
    #                           NO  → go to /login/
    #                           YES → welcome to dashboard
    return render(request, 'movies/admin_dashboard.html', context)

    # Security check to enter on admin dashboard..
    
   # Normal user logged in  → blocked (is_staff = False)
   # Staff user logged in   → allowed (is_staff = True)
   # Nobody logged in       → blocked
   
   
@login_required(login_url='/login/')
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        # flip is_cancelled to True
        booking.is_cancelled = True
        booking.save()

        # free the seat so others can book it
        booking.seat.is_booked = False
        booking.seat.save()

        # delete any leftover reservations for this seat
        SeatReservation.objects.filter(seat=booking.seat).delete()

        return redirect('profile')

    return redirect('profile')