from django.contrib import admin
from .models import Movie,Theater,Seat,Booking

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['name','rating','cast','description']
    
# above is for admin panel manager to see the column of data in MovieAdmin folder, so the flow is taking the raw data from (Movie) -> and links it to your custom settings(MovieAdmin)
    
@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name','movie','time']
    
@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['theater','seat_number','is_booked']
    
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user','seat','movie','theater','booked_at']

# --------------------------------------------------------------------------------------------------------------------------
# 🛠️ The 3-Step Logic of admin.py
# 1. The "Entry Ticket" (The Decorator)
# Your Logic: "Putting booking, movies inside the admin panel."
# The "Why": By default, Django's Admin is empty. The @admin.register() decorator acts like an entry ticket. It tells Django: "I want this specific table (like Movie) to have its own folder in the Admin Panel."


# 2. The "View Settings" (The Class)
# Your Logic: "Class is for showing which column we want."
# The "Why": If you don't use a class, Django just shows a list of items like "Movie Object (1)," which is useless. The class MovieAdmin acts like a filter. It tells the Admin: "Don't just show me the object; show me the specific columns I care about, like the Name and Rating."


# 3. The "Management Hub"
# Your Logic: "Because of these we add movies, seats, theaters."
# The "Why": This is exactly how you "fed" your website. Before your users could see anything, you used these Admin tools to manually create the "Avengers" movie, set the showtimes (Theaters), and add the chair numbers (Seats).