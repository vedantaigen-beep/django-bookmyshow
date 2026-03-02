from django.db import models # This is django in built file which we inherit in-each class to convert each class into database table..

# By inheriting from models.Model, Django injects things automatically:

# ✔️ Database table creation
# ✔️ Auto id primary key
# ✔️ .save() method
# ✔️ .delete() method
# ✔️ .objects.all()
# ✔️ .objects.filter()
# ✔️ .objects.create()

from django.contrib.auth.models import User # This used to looged-in with Booking , so we map x('user') -> booked this movie..

# By the way the name of table when we create class becomes 'movies_movie' by following one rule:
# <app_name>_<model_name> -> <folder_name>_<class_name>  → why django do this ? → Because: 1.We can have multiple apps.2.Different apps can have models with same name.

# Example:
# movies.Movie
# archive.Movie

# 📌 Important:
# movies → app name/folder_name
# movie → class name (converted to lowercase)
# You never type this table name manually django automatically converts it from internally.


# -----------------------------------------------------------------------------------------------------------------------------------------------------

# NOTE:📌 The "Hidden" Primary Key: > By inheriting from models.Model, Django automatically creates an id column for every table. This serves as the Unique ID (Primary Key) that allows ForeignKeys to "point" to specific records without the developer having to define it manually.

# So, when table connects with other
# tabel that means they are directly connecting to primary key of that table..
# -----------------------------------------------------------------------------------------------------------------------------------------------------


# This below movies_movie table is for describing the info about movies..
class Movie(models.Model): # So, because of models.Model this is not normal class it's convert in database table..
    name = models.CharField(max_length = 255)
    image = models.ImageField(upload_to="movies/")
    rating = models.DecimalField(max_digits = 3,decimal_places = 1)
    cast = models.TextField()
    description = models.TextField(blank = True, null = True)
    
    def __str__(self): # This is like a label tag suppose we have 100 identical boxes in warehouse and i know each boxes is of 'Movies' but it seems without label 'box1' and 'box2' by label it's easy to pick boxes according to required label from the box like {The Result: Instead of seeing "Box 1, Box 2," you see "Avatar, Batman, Inception."}
        return self.name
    
# 🧩 Why uppercase in class name is okay?

# Because Python convention is:
# ClassName → PascalCase
# table_name → lowercase
    

# This table is for showing information of theater name and date_time and connecting 'movies_movie'(Movie) table with 'movies_theater'(Theater) table..
class Theater(models.Model):
    name = models.CharField(max_length = 255)
    movie = models. ForeignKey(Movie, on_delete = models.CASCADE,related_name = 'theaters') 
    time = models.DateTimeField()
     
    def __str__(self):
        return f'{self.name} - {self.movie.name} at {self.time}'
    
# NOTE : Visual logic and concept above two table is in notion..
    
class Seat(models.Model):
# The Point: This seat belongs to one specific Showtime (Theater).

# Why? Seat "A1" for the 6 PM show is a different "product" than Seat "A1" for the 9 PM show. They are separate rows in this table, both pointing to their respective Theater.

# NOTE: Even if you don't see an id column in your code, Django creates it automatically for every row. This is what the ForeignKey uses to "point" to the correct theater.

    theater = models. ForeignKey(Theater, on_delete = models.CASCADE,related_name = 'seats')
    
# The Point: The literal label on the chair (e.g., "A1", "B10").
    seat_number = models.CharField(max_length = 10)
    
# The Logic: By default, it is False (Available). When someone buys it, we flip it to True (Taken). This is the only column that changes frequently.
    is_booked = models.BooleanField(default = False)
    
    def __str__(self): # This will label to seat
        return f'{self.seat_number} in {self.theater.name}'
    
# example of def_str -> logic..
# Seat Object (1),A1 in PVR Mumbai
# Seat Object (2),B5 in INOX Delhi
# Seat Object (3),A1 in INOX Delhi
    
    
# The Logic: This is your Transaction Record. It doesn't create a movie or a seat; it just records that a specific person "owns" a specific seat for a specific time.

class Booking(models.Model):
    user = models. ForeignKey(User, on_delete = models.CASCADE)
    seat = models. OneToOneField(Seat, on_delete = models.CASCADE) # OneToOneField: This is the most important part. It ensures one seat can only have one booking. If you try to book the same seat twice, the database will block it.
    movie = models. ForeignKey(Movie, on_delete = models.CASCADE)
    theater = models. ForeignKey(Theater, on_delete = models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add = True)
    
    def __str__(self):
        return f'Booking by {self.user.username} in {self.seat.seat_number} at {self.theater.name}'
    
a = str()