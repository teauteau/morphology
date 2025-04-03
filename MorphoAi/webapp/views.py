from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
import json
from .utils import generate_exercises
from django.views.decorators.csrf import csrf_exempt #REMOVE FOR PRODUCTION

def home(request):
    return render(request, 'webapp/home.html')


#@csrf_exempt # REMOVE FOR PRODUCTION
def generate(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("text", "").strip()
            difficulty = data.get("difficulty", "")
            
            if not text:
                return JsonResponse({"error": "Geen tekst ontvangen"}, status=400)

            # Generate exercises (adjust the number based on difficulty)
            nr_of_identify = 3 if difficulty == "Makkelijk" else 5 if difficulty == "Gemiddeld" else 7
            nr_of_fill_in_blanks = 2 if difficulty == "Makkelijk" else 4 if difficulty == "Gemiddeld" else 6
            
            exercises = generate_exercises(text, nr_of_identify, nr_of_fill_in_blanks)

            # Store in session
            request.session["text"] = text
            request.session["difficulty"] = difficulty
            request.session["exercises"] = exercises  # Store exercises in session

            return JsonResponse({"result_url": reverse('results')})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, 'webapp/generate.html')


def about(request):
    return render(request, 'webapp/about.html')

def summary(request):
    return render(request, 'webapp/summary.html')

def contact(request):
    team_members = [
        {'name': 'Lid 1', 'role': 'Ontwikkelaar', 'email': 'example1@email.com'},
        {'name': 'Lid 2', 'role': 'Designer', 'email': 'example2@email.com'},
        {'name': 'Lid 3', 'role': 'Researcher', 'email': 'example3@email.com'},
        {'name': 'Lid 4', 'role': 'Project Manager', 'email': 'example4@email.com'},
    ]
    return render(request, 'webapp/contact.html')

def help_page(request):
    return render(request, 'webapp/help.html')

def results_page(request):
    text = request.session.get("text", "Geen tekst ingevoerd")
    difficulty = request.session.get("difficulty", "Niet gespecificeerd")
    exercises = request.session.get("exercises", [])

    return render(request, "webapp/results.html", {
        "text": text,
        "difficulty": difficulty,
        "exercises": exercises,
    })
