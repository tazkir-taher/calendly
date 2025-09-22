import calendar
from datetime import time, datetime as dt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *

WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

def time_from_str(t_str):
    t_str = t_str.strip()
    if t_str.startswith("24:"):
        return time(23, 59)
    try:
        hour, minute = map(int, t_str.split(":"))
        if hour > 23 or minute > 59:
            raise ValueError("Hour must be 0-23 and minute 0-59")
        return time(hour, minute)
    except ValueError:
        dt_obj = dt.strptime(t_str, "%I:%M %p")
        return time(dt_obj.hour, dt_obj.minute)

def calculate_unavailable_intervals(available_intervals):
    unavailable = []
    current = time(0,0)
    sorted_avail = sorted(available_intervals, key=lambda x: x["start"])
    for interval in sorted_avail:
        if interval["start"] > current:
            unavailable.append({"start": current, "end": interval["start"]})
        current = max(current, interval["end"])
    if current < time(23,59):
        unavailable.append({"start": current, "end": time(23,59)})
    return unavailable

def merge_intervals(intervals):
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: x["start"])
    merged = [sorted_intervals[0]]
    for current in sorted_intervals[1:]:
        last = merged[-1]
        if current["start"] <= last["end"]:
            last["end"] = max(last["end"], current["end"])
        else:
            merged.append(current)
    return merged

def get_available_slots(unavailable_times):
    unavailable_intervals = [{"start": t.start_time, "end": t.end_time} for t in unavailable_times]
    unavailable_intervals = merge_intervals(unavailable_intervals)
    slots = []
    current = time(0,0)
    for interval in unavailable_intervals:
        if interval["start"] > current:
            slots.append({"start_time": str(current), "end_time": str(interval["start"])})
        current = interval["end"]
    if current < time(23,59):
        slots.append({"start_time": str(current), "end_time": "23:59"})
    return slots

def apply_specific_unavailable(day_obj, specific_unavailable_times):
    current_unavailable = [{"start": t.start_time, "end": t.end_time} for t in day_obj.times.all()]
    new_unavailable = [{"start": time_from_str(t["start_time"]), "end": time_from_str(t["end_time"])} for t in specific_unavailable_times]
    merged = merge_intervals(current_unavailable + new_unavailable)
    day_obj.times.all().delete()
    for interval in merged:
        Time.objects.create(day=day_obj, start_time=interval["start"], end_time=interval["end"])

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getDailySchedule(request):
    user = request.user
    date_str = request.query_params.get("date")

    if not date_str:
        return Response({
            "code": 400,
            "error": "Please provide a date"
        })
    
    try:
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({
            "code": 400,
            "error": "Invalid date format in params"
        })

    today = dt.today().date()
    if target_date < today:
        return Response({
            "date": str(target_date),
            "available": False,
            "time_slots": []
        })

    unavailable_times = []
    weekday_name = target_date.strftime("%A").lower()

    recurring_entries = Days.objects.filter(user=user, is_recurring=True)
    for entry in recurring_entries:
        recurring_days = []
        if entry.available_recurring_days:
            for d in entry.available_recurring_days.split(","):
                recurring_days.append(d.strip().lower())
        
        if weekday_name in recurring_days:
            for t in entry.times.all():
                unavailable_times.append(t)
        
        # else:
        #     for t in entry.times.all():
        #         unavailable_times.append(t)

    specific_entry = Days.objects.filter(user=user, is_recurring=False, day=target_date).first()
    if specific_entry:
        unavailable_times = list(specific_entry.times.all())

    available_slots = get_available_slots(unavailable_times)

    return Response({
        "code": 200,
        "date": str(target_date),
        "day": weekday_name,
        "available": len(available_slots) > 0,
        "time_slots": available_slots
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getMonthlySchedule(request):
    user = request.user
    year = int(request.query_params.get("year", dt.today().year))
    month = int(request.query_params.get("month", dt.today().month))

    first_weekday, num_days = calendar.monthrange(year, month)
    all_dates = [dt(year, month, day).date() for day in range(1, num_days + 1)]

    today = dt.today().date()
    all_dates = [date for date in all_dates if date >= today]

    available_dates = []

    for date in all_dates:
        unavailable_times = []

        recurring_entry = Days.objects.filter(user=user, is_recurring=True).first()
        if recurring_entry:
            weekday_name = date.strftime("%A").lower()
            if recurring_entry.unavailable_days:
                recurring_days = [d.strip().lower() for d in recurring_entry.unavailable_days.split(",")]
                if weekday_name in recurring_days:
                    unavailable_times.append(Time(start_time=time(0,0), end_time=time(23,59)))
            unavailable_times.extend(recurring_entry.times.all())

        specific_entry = Days.objects.filter(user=user, is_recurring=False, day=date).first()
        if specific_entry:
            unavailable_times = list(specific_entry.times.all())

        available_slots = get_available_slots(unavailable_times)
        if available_slots:
            available_dates.append(str(date))

    return Response({
        "code": 200,
        "success": True,
        "year": year,
        "month": month,
        "available_days": available_dates
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def createSchedule(request):
    user = request.user
    data = request.data
    
    available_recurring = data.get("recurring_days", [])
    available_specific = data.get("specific_days", [])
    unavailable_dates = data.get("unavailable_dates", [])
    specific_unavailable = data.get("specific_unavailable", [])

    all_weekdays = list(WEEKDAY_MAP.keys())
    
    if available_recurring:
        Days.objects.filter(user=user, is_recurring=True).delete()

        for day_name in all_weekdays:
            found = next((d for d in available_recurring if d["day"].lower() == day_name), None)

            day_obj = Days.objects.create(user=user, is_recurring=True, day=None, available_recurring_days= day_name if found else "")

            if found:
                start_time = time_from_str(found["start_time"])
                end_time = time_from_str(found["end_time"])
                intervals = calculate_unavailable_intervals([{"start": start_time, "end": end_time}])
                for interval in intervals:
                    Time.objects.create(day=day_obj, start_time=interval["start"], end_time=interval["end"])

    for d in available_specific:
        date_str = d.get("date")
        if not date_str:
            continue
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
        day_obj, create  = Days.objects.get_or_create(user=user, day=target_date, is_recurring=False)
        day_obj.times.all().delete()

        if d.get("unavailable", False):
            Time.objects.create(day=day_obj, start_time=time(0,0), end_time=time(23,59))
            continue

        available_times = []
        for t in d.get("times", []):
            start = time_from_str(t["start_time"])
            end = time_from_str(t["end_time"])
            available_times.append({"start": start, "end": end})

        intervals = calculate_unavailable_intervals(available_times)
        for interval in intervals:
            Time.objects.create(day=day_obj, start_time=interval["start"], end_time=interval["end"])

    for date_str in unavailable_dates:
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
        day_obj, create  = Days.objects.get_or_create(user=user, day=target_date, is_recurring=False)
        day_obj.times.all().delete()
        Time.objects.create(day=day_obj, start_time=time(0,0), end_time=time(23,59))

    for entry in specific_unavailable:
        date_str = entry.get("date")
        if not date_str:
            continue
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
        day_obj, created = Days.objects.get_or_create(user=user, day=target_date, is_recurring=False)

        if created or not day_obj.times.exists():
            recurring_entry = Days.objects.filter(user=user, is_recurring=True).first()
            if recurring_entry:
                weekday_name = target_date.strftime("%A").lower()
                recurring_days = [d.strip().lower() for d in recurring_entry.unavailable_days.split(",")] if recurring_entry.unavailable_days else []

                if weekday_name not in recurring_days:
                    for t in recurring_entry.times.all():
                        Time.objects.create(day=day_obj, start_time=t.start_time, end_time=t.end_time)

        apply_specific_unavailable(day_obj, entry.get("times", []))

    return Response({
        "code": 200, 
        "success": True,
        "message": "Schedule saved successfully"
    })

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def editSchedule(request):
    user = request.user
    data = request.data
    
    available_recurring = data.get("recurring_days", [])
    available_specific = data.get("specific_days", [])
    unavailable_dates = data.get("unavailable_dates", [])
    specific_unavailable = data.get("specific_unavailable", [])

    if available_recurring:
        day_obj, create  = Days.objects.get_or_create(user=user, is_recurring=True)
        day_obj.times.all().delete()
        all_weekdays = list(WEEKDAY_MAP.keys())
        unavailable_days = []

        for day_name in all_weekdays:
            found = next((d for d in available_recurring if d["day"].lower() == day_name), None)
            if found:
                start_time = time_from_str(found["start_time"])
                end_time = time_from_str(found["end_time"])
                intervals = calculate_unavailable_intervals([{"start": start_time, "end": end_time}])
                for interval in intervals:
                    Time.objects.create(day=day_obj, start_time=interval["start"], end_time=interval["end"])
            else:
                unavailable_days.append(day_name)

        day_obj.unavailable_days = ",".join(unavailable_days) if unavailable_days else ""
        day_obj.save()

    for d in available_specific:
        date_str = d.get("date")
        if not date_str:
            continue
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
        day_obj, create  = Days.objects.get_or_create(user=user, day=target_date, is_recurring=False)
        day_obj.times.all().delete()

        if d.get("unavailable", False):
            Time.objects.create(day=day_obj, start_time=time(0,0), end_time=time(23,59))
            continue

        available_times = []
        for t in d.get("times", []):
            start = time_from_str(t["start_time"])
            end = time_from_str(t["end_time"])
            available_times.append({"start": start, "end": end})

        intervals = calculate_unavailable_intervals(available_times)
        for interval in intervals:
            Time.objects.create(day=day_obj, start_time=interval["start"], end_time=interval["end"])

    for date_str in unavailable_dates:
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
        day_obj, create  = Days.objects.get_or_create(user=user, day=target_date, is_recurring=False)
        day_obj.times.all().delete()
        Time.objects.create(day=day_obj, start_time=time(0,0), end_time=time(23,59))

    for entry in specific_unavailable:
        date_str = entry.get("date")
        if not date_str:
            continue
        target_date = dt.strptime(date_str, "%Y-%m-%d").date()
        day_obj, created = Days.objects.get_or_create(user=user, day=target_date, is_recurring=False)

        if created or not day_obj.times.exists():
            recurring_entry = Days.objects.filter(user=user, is_recurring=True).first()
            if recurring_entry:
                weekday_name = target_date.strftime("%A").lower()
                if recurring_entry.unavailable_days:
                    recurring_days = [d.strip().lower() for d in recurring_entry.unavailable_days.split(",")]
                else:
                    recurring_days = []

                if weekday_name not in recurring_days:
                    for t in recurring_entry.times.all():
                        Time.objects.create(day=day_obj, start_time=t.start_time, end_time=t.end_time)

        apply_specific_unavailable(day_obj, entry.get("times", []))

    return Response({
        "code": 200,
        "success": True,
        "message": "Schedule patched successfully"
    })

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteSchedule(request):
    user = request.user
    Days.objects.filter(user=user).delete()
    return Response({
        "code": 200,
        "success": True,
        "message": "All unavailability deleted."
    })
