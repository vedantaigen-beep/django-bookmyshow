
# 🗺️ The "Data Pipeline" Approach for Task 1
# To add a secure YouTube trailer, we follow this logical flow:

# Step 1: The Input (The Model)
# Logic: We need a "bucket" to store the YouTube link.

# Your Action: You will add one line to your models.py called trailer_url.

# The "Safety Check": We will add a simple rule (a validator) that only allows text starting with "https://youtube.com".



# Step 2: The Transformation (The View)
# Logic: YouTube links come in different shapes (Short links, Watch links, Mobile links).

# Your Action: We will write a small 3-line Python function. Its only job is to "Clean" the data—it finds the unique Video ID and ignores everything else. This is exactly like "Data Cleaning" in Data Science.



# Step 3: The Loading (The Template)
# Logic: Put the video on the screen without slowing down the site.

# Your Action: We will add the <iframe> tag to your HTML. We will add the loading="lazy" attribute here. This is the "Performance" part of your task.



# Step 4: The Fallback (The Logic)
# Logic: What if a movie doesn't have a trailer yet?

# Your Action: We will add a simple {% if %} statement. If there is no link, show the poster; if there is a link, show the video.