from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from .models import SeatReservation


def release_expired_reservations():
    # find all expired reservations and delete them
    expired = SeatReservation.objects.filter(
        status="pending",
        expires_at__lt=timezone.now(),  # expires_at is LESS THAN now = expired
    )
    count = expired.count()
    expired.delete()
    print(f"Released {count} expired reservations")


def start():
    scheduler = BackgroundScheduler()

    # run release_expired_reservations every 60 seconds
    scheduler.add_job(
        release_expired_reservations,
        "interval",
        seconds=60,
        id="release_expired_reservations",
        replace_existing=True,
    )
    scheduler.start()
    print("Scheduler started!")

# elease_expired_reservations() — the cleaner function. Finds and deletes expired rows.
# start() — starts the background scheduler and tells it to run the cleaner every 60 seconds.

# ----------------------------------------------------------------------------------
# Why 60 seconds? — Cleaner runs every 60s, lock expires in 2 minutes.
# Too frequent (10s) = too many database calls. Too slow (5min) = seat stays locked too long.
# 60 seconds is the sweet spot — fast enough to release, light enough on database.
# If reservation has 1 minute left, scheduler skips it — only deletes when expires_at < now.