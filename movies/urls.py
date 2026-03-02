from django.urls import path
from . import views
urlpatterns = [
    path('', views.movie_list, name="movie_list"),
    path('<int:movie_id>/theaters', views.theater_list, name='theater_list'),
    path('theater/<int:theater_id>/seats/book/', views.book_seats, name='book_seats'),
]

# Full explanation of url.py

# 📍 The Top-Level Logic: urlpatterns

# This file is the Signpost of your application. While models.py is the warehouse and views.py is the manager, urls.py is the map that tells the browser, "If the user types this address, take them to that manager."

# Here is the logical breakdown of your movies/urls.py so you can explain it simply.

# 🗺️ The Logical Map
# The urlpatterns list is essentially a set of instructions for Django. It works like a switchboard:

# 1. The Main Entrance ('')
# Logic: When the URL is empty (just 127.0.0.1:8000/), it triggers the movie_list view.
# Why it's important: It sets the landing page. It’s the starting point where all your movie cards are displayed.

# 2. The Dynamic Redirect (<int:movie_id>/theaters)
# Logic: This is a "smart" path. The <int:movie_id> part is a variable.
# The "ID Card" Rule: If you click "View Theaters" for Avengers (ID 1), the URL becomes 1/theaters. If you click Inception (ID 2), it becomes 2/theaters.

# Teacher Explanation: "I used dynamic routing so I don't have to create a separate page for every movie. One logic handles every movie by passing its ID to the view."

# 3. The Specific Action (theater/<int:theater_id>/seats/book/)
# Logic: This path is more detailed. It doesn't just need a movie; it needs to know which specific Theater you chose.
# The Hand-off: It passes the theater_id to the book_seats function so the system knows exactly which seat map to load.

# -------------------------------------------------------------------------------------------------------------------------------

# 💡 The Secret Weapon: name="..."
# You’ll notice each path has a name (like name="theater_list").

# Logic: This is a Nickname.

# Why use it? If you ever change your URL from /theaters/ to /cinema-halls/, you don't have to go into 50 HTML files and change the links. As long as the nickname stays the same, Django will find the new address automatically.