from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
import json
from .utils import generate_exercises, generate_exercise_given_word
from .utils import add_exercises as utils_add_exercises
from .utils import generate_exercise_given_word as  utils_generate_exercise_given_word
from django.utils.html import escape, mark_safe
import re



from django.views.decorators.csrf import csrf_exempt #REMOVE FOR PRODUCTION

#for pdf generation
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

exercise_types = ["identify", "fill_in_the_blank", "alternative", "wrong_word_sentence",  "affix_matching"] 


def home(request):
    return render(request, 'webapp/home.html')


#@csrf_exempt # REMOVE FOR PRODUCTION
def generate(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("text", "").strip()
            difficulty = data.get("difficulty", "")
            
            if not text or not difficulty:
                return JsonResponse({"error": "Geen tekst ontvangen"}, status=400)

            # Define number of exercises based on difficulty
            nr_of_identify = 0
            nr_of_fill_in_blanks = 0
            nr_of_alternative = 0
            nr_of_wrong_words = 0
            nr_of_affix = 0

            if "easy" in difficulty:
                nr_of_identify += 1
                nr_of_fill_in_blanks += 1
                nr_of_alternative += 1
                nr_of_wrong_words += 0
                nr_of_affix += 0
            if "medium" in difficulty:
                nr_of_identify += 0
                nr_of_fill_in_blanks += 0
                nr_of_alternative += 0
                nr_of_wrong_words += 1
                nr_of_affix += 1
            if "hard" in difficulty:
                nr_of_identify += 0
                nr_of_fill_in_blanks += 0
                nr_of_alternative += 0
                nr_of_wrong_words += 0
                nr_of_affix += 0
            
            
            # Generate existing exercises
            exercises, morphemes, important_words = generate_exercises(text, nr_of_identify, nr_of_fill_in_blanks, nr_of_alternative, nr_of_wrong_words, nr_of_affix)            
            # Store in session
            request.session["text"] = text
            request.session["difficulty"] = difficulty
            request.session["exercises"] = exercises  # Store exercises in session
            request.session["exercise_types"] = exercise_types
            request.session["morphemes"] = morphemes
            request.session["important_words"] = important_words

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
    important_words = request.session.get("important_words", [])

    text = embolden(text, important_words)

    return render(request, "webapp/results.html", {
        "text": text,
        "difficulty": difficulty,
        "exercises": exercises,
        "exercise_types": exercise_types,
    })


def embolden(text, important_words):
    important_set = {w.lower() for w in important_words}
    tokens = re.findall(r'\w+|\W+', text)

    wrapped_tokens = []
    for idx, token in enumerate(tokens):
        if token.strip().isalnum():
            word_class = "word bold" if token.lower() in important_set else "word"
            wrapped = (
                f'<div class="d-inline dropdown">'
                f'  <span class="{word_class}" role="button" id="dropdownWord{idx}" '
                f'        data-bs-toggle="dropdown" aria-expanded="false" data-word="{token}">'
                f'    {token}'
                f'  </span>'
                f'  <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="dropdownWord{idx}">'
                f'    <li><h6 class="dropdown-header">Choose an exercise for <i>{token}</i></h6></li>'
                f'    <li><a class="dropdown-item" href="#" onclick="handleOption(\'{token}\', 1)">Identify</a></li>'
                f'    <li><a class="dropdown-item" href="#" onclick="handleOption(\'{token}\', 2)">Fill in the blank</a></li>'
                f'    <li><a class="dropdown-item" href="#" onclick="handleOption(\'{token}\', 3)">Alternative form</a></li>'
                f'    <li><a class="dropdown-item" href="#" onclick="handleOption(\'{token}\', 4)">Wrong word</a></li>'
                # f'    <li><a class="dropdown-item" href="#" onclick="handleOption(\'{token}\', 5)">Affix matching</a></li>'
                f'  </ul>'
                f'</div>'
            )
        else:
            wrapped = token  # punctuation/space
        wrapped_tokens.append(wrapped)

    return mark_safe(''.join(wrapped_tokens))

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
            print("exercise_types: ", exercises_types)
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

def generate_exercise_given_word(request):
        if request.method == 'POST':
            data = json.loads(request.body)
            exercise_type = data.get('exercise_type')
            word = data.get('word')
            exercises = request.session.get('exercises', [])
            exercise = utils_generate_exercise_given_word(word, exercise_type)
            exercises.append(exercise)
            request.session['exercises'] = exercises
            # important_words = request.session.get("important_words", [])
            # important_words = important_words.append(word)
            # request.session["important_words"] = important_words
            

            return render(request, 'webapp/partials/added_exercises.html', {
            'exercises': exercises
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
            return render(request, 'webapp/partials/added_exercises.html', {
            'exercises': exercises
            })
        return JsonResponse({'error': 'invalid index'}, status=400)
    return JsonResponse({'error': 'invalid method'}, status=405)