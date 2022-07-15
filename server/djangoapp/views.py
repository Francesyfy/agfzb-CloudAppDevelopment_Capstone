from calendar import c
from multiprocessing import context
from platform import java_ver
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel, CarMake
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.
# def home(request):
#     return render(request, 'djangoapp/index.html')

# Create an `about` view to render a static about page
def about(request):
    return render(request, 'djangoapp/about.html')

# Create a `contact` view to return a static contact page
def contact(request):
    return render(request, 'djangoapp/contact.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/login.html', context)
    else:
        return render(request, 'djangoapp/login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
# def get_dealerships(request):
#     context = {}
#     if request.method == "GET":
#         return render(request, 'djangoapp/index.html', context)

def get_dealerships(request):
    if request.method == "GET":
        url = "https://4d83bbb1.us-south.apigw.appdomain.cloud/api/dealership"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        # # Concat all dealer's short name
        # dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # # Return a list of dealer short name
        # return HttpResponse(dealer_names)
        context = {"dealership": dealerships}
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        url = "https://4d83bbb1.us-south.apigw.appdomain.cloud/api/review"
        reviews = get_dealer_reviews_from_cf(url, dealerId=dealer_id)
        context = {"reviews": reviews, "dealer_id": dealer_id}
        return render(request, 'djangoapp/dealer_details.html', context)


# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    if request.method == "GET":
        cars = CarModel.objects.filter(dealer_id=dealer_id)
        context = {"cars": cars, "dealer_id": dealer_id}
        return render(request, 'djangoapp/add_review.html', context)

    elif request.method == "POST":
        content = request.POST['content']
        car_id = request.POST.get('car', False)
        purchasedate = request.POST.get('purchasedate', '')
        purchasecheck = request.POST.get('purchasecheck', False)

        review = {key:'' for key in ['name', 'dealership', 'review', 'purchase', 
                'purchase_date', 'car_make', 'car_model', 'car_year', 'sentiment']}
        review["dealership"] = dealer_id
        review["review"] = content
        review["name"] = request.user.username
        review["time"] = datetime.utcnow().isoformat()
        review["purchase_date"] = purchasedate
        if car_id:
            car = get_object_or_404(CarModel, pk=car_id)
            review["car_make"] = car.car_make.name
            review["car_model"] = car.name
            review["car_year"] = car.year.year
        if purchasecheck:
            review["purchase"] = True
        else:
            review["purchase"] = False
        
        json_payload = {"review": review}
        url = "https://4d83bbb1.us-south.apigw.appdomain.cloud/api/review"
        response = post_request(url, json_payload)
        return redirect('djangoapp:dealer_details', dealer_id=dealer_id)

