from .models import *
from .serializers import *
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ContactList(request):
    user = request.user
    try:
        contacts = Contact.objects.filter(user=user)
        serializer = ContactSerializer(contacts, many=True)
        return Response({
            'code': status.HTTP_200_OK,
            'response': "Received Data Successfully",
            "data": serializer.data
        })
    except Exception as e:
        return Response({
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'response': "An error occurred while fetching Contacts",
            'error': str(e)
        }) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ContactDetail(request, pk):
    try:
        contact = Contact.objects.get(id=pk, user=request.user)
        serializer = ContactSerializer(contact)
        return Response({
            'code': status.HTTP_200_OK,
            'response': "Received Data Successfully",
            "data": serializer.data
        })
    except Contact.DoesNotExist:
        return Response({
            'code': status.HTTP_404_NOT_FOUND,
            'response': "Contact not found"
        })
    except Exception as e:
        return Response({
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'response': "An error occurred while fetching the Contact",
            'error': str(e)
        })
    
@api_view(['POST'])
def ContactCreate(request):
    try:
        user_slug = request.data.get('user_slug', None)
        if user_slug:
            user_slug_instance = User.objects.filter(username=user_slug).first()
            user = user_slug_instance if user_slug_instance else None
        else:
            user = None

        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({
                'code': status.HTTP_200_OK,
                'response': "Contact created successfully",
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
            'response': "An error occurred while creating the Contact",
            'error': str(e)
        })
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def ContactDelete(request, pk):
    try:
        contact = Contact.objects.get(id=pk)
        contact.delete()
        return Response({
            'code': status.HTTP_204_NO_CONTENT,
            'response': "Contact deleted successfully"
        })
    except Contact.DoesNotExist:
        return Response({
            'code': status.HTTP_404_NOT_FOUND,
            'response': "Contact not found"
        })
    except Exception as e:
        return Response({
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'response': "An error occurred while deleting the Contact",
            'error': str(e)
        })