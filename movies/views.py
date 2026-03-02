# What is views.py? It is the "Logic Hub." It acts as a middleman that talks to the Database (Models) and the User Interface (Templates).

# If the models.py is the Storage Room and urls.py is the Signpost, then the views.py is the Manager who actually does the work.

# The "Manager" Logic
# A view is just a Python function that follows a simple 3-Step Process:

# Receive: It gets a "Request" from the user (via the URL).
# Fetch: It goes to the database (Models) to grab the right data.
# Deliver: It sends that data to a webpage (Template) for the user to see.


from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

def movie_list(request):
    search_query = request.GET.get('search')
    if search_query:
        movies = Movie.objects.filter(name__icontains = search_query)
    else:
        movies = Movie.objects.all()
    return render(request,'movies/movie_list.html',{'movies':movies})

# The "Connection Pin" (Logic Breakdown)
# Movie.objects.all(): This is you telling the database, "Give me everything in the Movie table." It's like taking all the DVDs off the shelf.

# render(...): This is the delivery truck.

# {'movies': movies} (The Context): This is the most crucial part. You are giving the HTML a "Nickname" (the string 'movies') so the HTML knows what to call the data when it arrives.

# ----------------------------------------------------------------------------------------------

def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theater = Theater.objects.filter(movie=movie)
    return render(request, 'movies/theater_list.html', {'movie': movie, 'theaters': theater})


# The "Connection Pin":
# movie_id: Remember the <int:movie_id> from the URL? Django "catches" that number and drops it right into this function.

# movie.theaters.all(): This is the "Two-Way Street" we talked about. Because we used related_name='theaters' in our model, we can now ask the Movie: "Hey Avatar, give me a list of every theater you are playing in."

# ----------------------------------------------------------------------------------------------

@login_required(login_url='/login/')
def book_seats(request, theater_id):
    # Rename the dictionary key to 'theaters' to match your HTML header
    theaters = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theaters)
    if request.method == 'POST':
        selected_Seats = request.POST.getlist('seats')
        error_seats = []
        if not selected_Seats:
            return render(request,"movies/seat_selection.html", {'theater':theaters,"seats":seats,'error':"No seat selected"})
        for seat_id in selected_Seats:
            seat = get_object_or_404(Seat,id = seat_id,theater = theaters)
            if seat.is_booked:
                error_seats.append(seat.seat_number)
                continue
            try:
                Booking.objects.create(
                    user = request.user,
                    seat = seat,
                    movie = theaters.movie,
                    theater = theaters
                )
                seat.is_booked = True
                seat.save()
            except IntegrityError:
                error_seats.append(seat.seat_number)
        if error_seats:
            error_message = f"The following seats are already booked: {','.join(error_seats)}"
            return render(request,'movies/seat_selection.html',{'theater':theaters,"seats":seats,'error':"No seat selected"})
        return redirect('profile')
    return render(request, 'movies/seat_selection.html', {'theaters': theaters, "seats": seats})
# The "Connection Pin":
# @login_required:The "Members Only" Rule: It wraps the function. If the user isn't logged in, it "kicks" them to the login page before they even see a single seat.

# get_object_or_404 : The "Smart Fetch": If a user types a fake theater ID in the URL, it shows a "404 Not Found" page instead of letting the website crash (error 500).

# .filter(theater=theater): The "Specific Room" Rule: It ignores all other seats in the database and only grabs the ones "Pointing" (Linked) to the theater the user selected.B