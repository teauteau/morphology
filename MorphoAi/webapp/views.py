from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
import json
from .utils import generate_exercises
from .utils import add_exercises as utils_add_exercises

from django.views.decorators.csrf import csrf_exempt #REMOVE FOR PRODUCTION

#for pdf generation
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

exercise_types = ["identify", "fill_in_the_blank"] 


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
            nr_of_identify = 2 if difficulty == "Makkelijk" else 3 if difficulty == "Gemiddeld" else 4
            nr_of_fill_in_blanks = 2 if difficulty == "Makkelijk" else 3 if difficulty == "Gemiddeld" else 4
            
            exercises, morphemes = generate_exercises(text, nr_of_identify, nr_of_fill_in_blanks)
            # exercises, morphemes = [[('This is question one', 'This is answer one'), ('This is question two', 'This is answer two'), ('This is question three', 'This is answer three'), ('This is question 4', 'This is answer 4')], [{'word': 'bijen', 'free': ['bij'], 'bound': {'prefixes': [], 'suffixes': ['en'], 'other': []}}, {'word': 'bestuiven', 'free': ['stuif'], 'bound': {'prefixes': ['be'], 'suffixes': ['en'], 'other': []}}, {'word': 'bloem', 'free': ['bloem'], 'bound': {'prefixes': [], 'suffixes': [], 'other': []}}, {'word': 'honing', 'free': ['honing'], 'bound': {'prefixes': [], 'suffixes': [], 'other': []}}]] #dummy
            # Store in session
            request.session["text"] = text
            request.session["difficulty"] = difficulty
            request.session["exercises"] = exercises  # Store exercises in session
            request.session["exercise_types"] = exercise_types
            request.session["morphemes"] = morphemes
            print(f"exercise_types: {exercise_types}")

            return JsonResponse({"result_url": reverse('results')})

        except Exception as e:
            print(f"Error: {e}")
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
    exercise_types = request.session.get("exercise_types", [])

    return render(request, "webapp/results.html", {
        "text": text,
        "difficulty": difficulty,
        "exercises": exercises,
        "exercise_types": exercise_types,
    })

def exercise_pdf(request):
    exercises = request.session.get('exercises', [])
    version = request.GET.get('version', 'student')  # Default to student version

    template = 'webapp/answers_pdf.html' if version == 'teacher' else 'webapp/exercise_pdf.html'
    filename = f"exercises_{version}.pdf"

    # Render template to HTML string
    html = render_to_string(template, {
        'exercises': exercises
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Generate PDF
    pisa_status = pisa.CreatePDF(
        html,
        dest=response,
        encoding='UTF-8',
        link_callback=lambda uri, _: uri  # Handle external resources if needed
    )
    
    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)
    return response

def add_exercises(request):
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            data = json.loads(request.body)
            exercises_types = data.get('exercises', [])
            old_exercises = request.session.get('exercises', [])
            new_exercises = []
            for i, exercise in enumerate(exercises_types):
                exercise_count = int(exercise.get('count', 0)) if exercise.get('count', '').strip() else 0
                exercise_type = exercise.get('type', 'identify')
                index = len(old_exercises) / len(exercise_types)
                generated_exercises = utils_add_exercises(exercise_type, exercise_count, request.session.get("morphemes", [{'word': 'foutje', 'free': ['fout'], 'bound': {'prefixes': [], 'suffixes': ['je'], 'other': []}}]), index)
                print(generated_exercises)
                new_exercises.extend(generated_exercises)
            combined_exercises = old_exercises + new_exercises
            request.session['exercises'] = combined_exercises
            # # Process exercises here
            return render(request, 'webapp/partials/added_exercises.html', {
            'exercises': combined_exercises
        })

def update_exercise(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        index = data.get('index')
        new_exercise = data.get('exercise')
        new_answer = data.get('answer')

        exercises = request.session.get('exercises', [])
        if 0 <= index < len(exercises):
            exercises[index][0] = new_exercise
            exercises[index][1] = new_answer
            request.session['exercises'] = exercises
            return JsonResponse({'status': 'ok'})
        else:
            return JsonResponse({'status': 'invalid index'}, status=400)

    return JsonResponse({'error': 'invalid request'}, status=405)


def delete_exercise(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        index = data.get('index')
        exercises = request.session.get('exercises', [])
        if 0 <= index < len(exercises):
            del exercises[index]
            request.session['exercises'] = exercises
            return JsonResponse({'status': 'ok'})
        return JsonResponse({'error': 'invalid index'}, status=400)
    return JsonResponse({'error': 'invalid method'}, status=405)