import calendar
import datetime
from datetime import time
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

def invert_time_slots(unavailable_times):
    
    day_start = time(0,0)
    day_end = time(23,59)

    slots = []
    unavailable_times = sorted(unavailable_times, key=lambda t: t.start_time)
    current_start = day_start

    for t in unavailable_times:
        if t.start_time > current_start:
            slots.append({"start_time": str(current_start), "end_time": str(t.start_time)})
        current_start = max(current_start, t.end_time)

    if current_start < day_end:
        slots.append({"start_time": str(current_start), "end_time": str(day_end)})

    return slots

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getDailySchedule(request):
    user = request.user

    date_str = request.query_params.get("date")
    if not date_str:
        return Response({"code": 400,
                        "error": "Please provide a date"})

    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"code": 400,
                        "error": "Invalid date format, use YYYY-MM-DD"})

    # Assume whole day available initially
    available = True
    time_slots = [{"start_time": "00:00", "end_time": "23:59"}]

    # ---- recurring unavailable weekdays ----
    recurring_entry = Days.objects.filter(user=user, is_recurring=True).first()
    if recurring_entry:
        if recurring_entry.unavailable_days:
            recurring_days = []
            for d in recurring_entry.unavailable_days.split(","):
                recurring_days.append(d.strip().lower())

            weekday_name = target_date.strftime("%A").lower()
            if weekday_name in recurring_days:
                # Fully unavailable
                return Response({"date": str(target_date), "available": False, "time_slots": []})

        # Partial unavailable times for recurring
        recurring_times = recurring_entry.times.all()
        if recurring_times:
            # Build available slots by inverting unavailable times
            time_slots = []
            current_start = datetime.time(0, 0)
            for t in recurring_times:
                if t.start_time > current_start:
                    time_slots.append({"start_time": str(current_start), "end_time": str(t.start_time)})
                current_start = t.end_time
            if current_start < datetime.time(23, 59):
                time_slots.append({"start_time": str(current_start), "end_time": "23:59"})

    # ---- specific day ----
    specific_entry = Days.objects.filter(user=user, is_recurring=False, day=target_date).first()
    if specific_entry:
        if not specific_entry.times.exists():
            # Fully unavailable
            return Response({"date": str(target_date),
                            "available": False,
                            "time_slots": []})
        else:
            # Partial unavailable
            unavailable_times = specific_entry.times.all()
            time_slots = []
            current_start = datetime.time(0, 0)
            for t in unavailable_times:
                if t.start_time > current_start:
                    time_slots.append({"start_time": str(current_start), "end_time": str(t.start_time)})
                current_start = t.end_time
            if current_start < datetime.time(23, 59):
                time_slots.append({"start_time": str(current_start), "end_time": "23:59"})

    return Response({"date": str(target_date),
                    "available": len(time_slots) > 0,
                    "time_slots": time_slots})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getMonthlySchedule(request):
    user = request.user

    if "year" in request.query_params:
        year = int(request.query_params.get("year"))
    else:
        year = datetime.date.today().year

    if "month" in request.query_params:
        month = int(request.query_params.get("month"))
    else:
        month = datetime.date.today().month

    first_weekday, num_days = calendar.monthrange(year, month)
    all_dates = []
    for day_number in range(1, num_days + 1):
        all_dates.append(datetime.date(year, month, day_number))

    unavailable_dates = []

    recurring_entry = Days.objects.filter(user=user, is_recurring=True).first()
    if recurring_entry:
        if recurring_entry.unavailable_days:
            recurring_days = []
            for d in recurring_entry.unavailable_days.split(","):
                recurring_days.append(d.strip().lower())

            for d in all_dates:
                weekday_name = d.strftime("%A").lower()
                if weekday_name in recurring_days:
                    if d not in unavailable_dates:
                        unavailable_dates.append(d)

    specific_entries = Days.objects.filter(user=user, is_recurring=False, day__year=year, day__month=month)
    for entry in specific_entries:
        if entry.day not in unavailable_dates:
            unavailable_dates.append(entry.day)
    
    unavailable_dates.sort()

    str_dates = []
    for d in unavailable_dates:
        str_dates.append(str(d))

    return Response({
        "code": 200,
        "success": True,
        "year": year,
        "month": month,
        "unavailable_days": str_dates
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def createSchedule(request):
    user = request.user
    data = request.data
    
    available_recurring = data.get("recurring_days", [])
    available_specific = data.get("specific_days", [])
    
    all_weekdays = list(WEEKDAY_MAP.keys())
    unavailable_recurring_days = []
    
    for day_name in all_weekdays:
        found = False
        for d in available_recurring:
            if d["day"] == day_name:
                found = True
                start_available = d["start_time"]
                end_available = d["end_time"]
                
                start_available_time = time(int(start_available.split(":")[0]), int(start_available.split(":")[1]))
                end_available_time = time(int(end_available.split(":")[0]), int(end_available.split(":")[1]))
                
                day_obj, created = Days.objects.update_or_create(user=user,is_recurring=True,defaults={"unavailable_days": ""})
                
                if start_available_time > time(0, 0):
                    Time.objects.create(day=day_obj, start_time=time(0,0), end_time=start_available_time)
                
                if end_available_time < time(23,59):
                    Time.objects.create(day=day_obj, start_time=end_available_time, end_time=time(23,59))
                break
                
        if not found:
            unavailable_recurring_days.append(day_name)
        
    if len(unavailable_recurring_days) > 0:
        day_obj, created = Days.objects.update_or_create(user=user, is_recurring=True, defaults={"unavailable_days": ",".join(unavailable_recurring_days)})
    
    for d in available_specific:
        day_obj, created = Days.objects.update_or_create(user=user, day=d, is_recurring=False)
        if "times" in d:
            for t in d["times"]:
                start = t["start_time"]
                end = t["end_time"]
                start_time = time(int(start.split(":")[0]), int(start.split(":")[1]))
                end_time = time(int(end.split(":")[0]), int(end.split(":")[1]))
                Time.objects.create(day=day_obj, start_time=start_time, end_time=end_time)
    
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
    specific_days = data.get("specific_days", [])

    all_weekdays = list(WEEKDAY_MAP.keys())
    unavailable_recurring_days = []

    day_obj, created = Days.objects.get_or_create(user=user, is_recurring=True, defaults={"unavailable_days": ""})
    day_obj.times.all().delete()

    for day_name in all_weekdays:
        found = False
        for d in available_recurring:
            if d["day"] == day_name:
                found = True
                start_available = d["start_time"]
                end_available = d["end_time"]

                start_available_time = time(int(start_available.split(":")[0]), int(start_available.split(":")[1]))
                end_available_time = time(int(end_available.split(":")[0]), int(end_available.split(":")[1]))
                
                if start_available_time > time(0, 0):
                    Time.objects.create(day=day_obj, start_time=time(0,0), end_time=start_available_time)
                
                if end_available_time < time(23,59):
                    Time.objects.create(day=day_obj, start_time=end_available_time, end_time=time(23,59))
                break
                
        if not found:
            unavailable_recurring_days.append(day_name)

    day_obj.unavailable_days = ",".join(unavailable_recurring_days)
    day_obj.save()

    Days.objects.filter(user=user, is_recurring=False).delete()

    for d in specific_days:
        date = d.get("date")
        if not date:
            continue

        day_obj, created = Days.objects.update_or_create(user=user, day=date, is_recurring=False)

        if d.get("unavailable"):
            Time.objects.create(day=day_obj, start_time=time(0,0), end_time=time(23,59))
        elif "times" in d:
            for t in d["times"]:
                start = t["start_time"]
                end = t["end_time"]
                start_time = time(int(start.split(":")[0]), int(start.split(":")[1]))
                end_time = time(int(end.split(":")[0]), int(end.split(":")[1]))
                Time.objects.create(day=day_obj, start_time=start_time, end_time=end_time)

    return Response({
        "code": 200,
        "success": True,
        "message": "Schedule updated successfully"
    })