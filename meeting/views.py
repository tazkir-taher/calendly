from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import time, datetime as dt, date
from .models import Meeting
from .serializers import MeetingSerializer
from schedule.models import Days, Time

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

def apply_specific_unavailable(day_obj, specific_unavailable_times):
    current_unavailable = [{"start": t.start_time, "end": t.end_time} for t in day_obj.times.all()]
    new_unavailable = [{"start": time_from_str(t["start_time"]), "end": time_from_str(t["end_time"])} for t in specific_unavailable_times]
    merged = merge_intervals(current_unavailable + new_unavailable)
    day_obj.times.all().delete()
    for interval in merged:
        Time.objects.create(day=day_obj, start_time=interval["start"], end_time=interval["end"])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meetingList(request):
    user = request.user
    try:
        meetings = Meeting.objects.filter(user=user)
        serializer = MeetingSerializer(meetings, many=True)
        return Response({
            'code': status.HTTP_200_OK,
            'response': "Received Data Successfully",
            "data": serializer.data
        })
    except Exception as e:
        return Response({
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'response': "An error occurred while fetching meetings",
            'error': str(e)
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meetingDetail(request, pk):
    try:
        meeting = Meeting.objects.get(id=pk, user=request.user)
        serializer = MeetingSerializer(meeting)
        return Response({
            'code': status.HTTP_200_OK,
            'response': "Received Data Successfully",
            "data": serializer.data
        })
    except Meeting.DoesNotExist:
        return Response({
            'code': status.HTTP_404_NOT_FOUND,
            'response': "Meeting not found"
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def meetingCreate(request):
    try:
        user = request.user
        serializer = MeetingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user, active=False)
            return Response({
                'code': status.HTTP_200_OK,
                'response': "Meeting created successfully",
                "data": serializer.data
            })
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'response': "Invalid data",
            'errors': serializer.errors
        })
    except Exception as e:
        return Response({
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'response': "An error occurred while creating the meeting",
            'error': str(e)
        })

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def meetingDelete(request, pk):
    try:
        meeting = Meeting.objects.get(id=pk, user=request.user)
        meeting.delete()
        return Response({
            'code': status.HTTP_204_NO_CONTENT,
            'response': "Meeting deleted successfully"
        })
    except Meeting.DoesNotExist:
        return Response({
            'code': status.HTTP_404_NOT_FOUND,
            'response': "Meeting not found"
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meetingToggle(request, pk):
    try:
        meeting = Meeting.objects.get(id=pk, user=request.user)

        if not meeting.active:
            meeting.active = True
            meeting.save()
        else:
            meeting.delete()
            return Response({
                'code': status.HTTP_200_OK,
                'response': "deleted, since active=False"
            })

        if meeting.active and meeting.start_time and meeting.end_time:
            target_date = meeting.day if meeting.day else date.today()
            weekday_name = target_date.strftime("%A").lower()

            repeating_day = Days.objects.filter(user=request.user, is_repeating=True,  available_repeating_days__icontains=weekday_name).first()

            if repeating_day:
                day_obj, created = Days.objects.get_or_create(user=request.user, day=target_date, is_repeating=False)
                if created or not day_obj.times.exists():
                    for t in repeating_day.times.all():
                        Time.objects.create(day=day_obj, start_time=t.start_time, end_time=t.end_time)
            else:
                day_obj, created = Days.objects.get_or_create(user=request.user, day=target_date, is_repeating=False)

            apply_specific_unavailable(day_obj, [{"start_time": meeting.start_time.strftime("%H:%M"), "end_time": meeting.end_time.strftime("%H:%M")}])

        return Response({
            'code': status.HTTP_200_OK,
            'response': "Meeting approved successfully",
            "active": meeting.active
        })

    except Meeting.DoesNotExist:
        return Response({
            'code': status.HTTP_404_NOT_FOUND,
            'response': "Meeting not found"
        })
    except Exception as e:
        return Response({
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'response': "An error occurred while toggling the meeting",
            'error': str(e)
        })