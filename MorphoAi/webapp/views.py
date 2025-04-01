from django.shortcuts import render

def get_language(request):
    return request.GET.get('lang', 'nl')  # Default to Dutch

def home(request):
    return render(request, 'webapp/home.html')

def generate(request):
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
    return render(request, 'webapp/contact.html', {'language': get_language(request), 'team_members': team_members})

def help_page(request):
    return render(request, 'webapp/help.html')

import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from .utils import detect_morphemes  # Function to call Google Gemini API

def generate_exercises(request):
    if request.method == "POST":
        data = json.loads(request.body)
        text = data.get("text", "")
        difficulty = data.get("difficulty", "")

        if not text:
            return JsonResponse({"error": "Geen tekst ontvangen"}, status=400)

        # Detect morphemes using Google Gemini
        morphemes = detect_morphemes(text)

        # Store data in session so it can be retrieved on the results page
        request.session["text"] = text
        request.session["morphemes"] = morphemes
        request.session["difficulty"] = difficulty

        # Redirect to the results page
        return JsonResponse({"result_url": reverse("results")})

    return JsonResponse({"error": "Ongeldige aanvraag"}, status=400)


def results_page(request):
    # Retrieve session data
    text = request.session.get("text", "")
    morphemes = request.session.get("morphemes", "")
    difficulty = request.session.get("difficulty", "")

    return render(request, "webapp/results.html", {
        "text": text,
        "morphemes": morphemes,
        "difficulty": difficulty
    })



