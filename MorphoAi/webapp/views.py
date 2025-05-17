from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
import json
from .utils import generate_exercises
from .utils import add_exercises as utils_add_exercises
from .utils import generate_exercise_given_word as utils_generate_exercise_given_word
from django.utils.html import escape, mark_safe
import re
import traceback
from django.views.decorators.csrf import csrf_exempt #REMOVE FOR PRODUCTION
#for pdf generation
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from google import genai


exercise_types = {"identify": "Identificeer morfemen", #hard
                   "fill_in_the_blank": "Invullen", #medium
                   "alternative": "Alternatieve vorm", #hard
                   "wrong_word_sentence": "Fout woord in zin", #medium
                   "affix_matching": "Achtervoegsels matchen", # medium?
                   "find_compounds": "Vind alle samenstellingen", #easy
                   "find_plurals": "Vind alle meervoudsvormen", #easy
                   "find_diminutives": "Vind alle verkleinwoorden", #easy
                   "plural_form": "Meervoudsvorm", # medium
                   "singular_form": "Enkelvoudsvorm" # medium
                   } 

# these exercise types are not used in the dropdown menu (use this for exercises that do not depend on a single word)
exercise_types_ignore = ["affix_matching", "find_compounds", "find_plurals", "find_diminutives"]

# example for each exercise type
exercise_examples = {"identify" : "Identificeer de morfemen in het woord 'onvergetelijk'.",
                      "fill_in_the_blank" : "(mooi) Het was een ____ dag.",
                      "alternative" : "Vind woorden die de morfeem 'over' bevatten",
                      "wrong_word_sentence" : "De hond is een 'onvergetelijke' huisdier.",
                      "affix_matching" : "Koppel de juiste achtervoegsels aan de woorden.",
                      "find_compounds" : "Vind alle samenstellingen in de tekst.",
                      "find_plurals" : "Vind alle meervoudsvormen in de tekst.",
                      "find_diminutives" : "Vind alle verkleinwoorden in de tekst.",
                      "plural_form" : "Wat is de meervoudsvorm van 'boek'?",
                      "singular_form" : "Wat is de enkelvoudsvorm van 'boeken'?"}


def home(request):
    return render(request, 'webapp/home.html')

def group_exercises(exercises):
    """
    Groups exercises by their type and creates appropriate headings
    """
    # Dictionary of exercise types and their heading templates
    heading_templates = {
        "identify": "Identificeer de vrije en gebonden morfemen in de volgende woorden:",
        "fill_in_the_blank": "Vul de juiste vorm in bij de volgende zinnen:",
        "alternative_form": "Gebruik de vrije morfeem uit de onderstaande woorden om een andere vorm te schrijven die deze morfeem bevat:",
        "error_correction": "Corrigeer de fouten in de volgende zinnen:",
        "find_compound": "Vind alle samenstellingen in de gegeven tekst.",
        "find_plural": "Vind alle meervoudsvormen in de gegeven tekst.",
        "find_diminutive": "Vind alle verkleinwoorden in de gegeven tekst.",
        "plural_form": "Geef de meervoudsvorm van de volgende woorden:",
        "singular_form": "Geef de enkelvoudsvorm van de volgende woorden:",
        "affix_matching": "Match de voorvoegsels en achtervoegsels met de juiste woorden:",
        "easy_extra": "Beantwoord de volgende vragen:",

    }
    # exercise difficulty
    exercise_difficulty = {
        "identify": "easy",
        "fill_in_the_blank":"medium" ,
        "alternative_form": "medium",
        "error_correction": "hard",
        "find_compound":"easy" ,
        "find_plural": "easy",
        "find_diminutive": "easy",
        "plural_form":"medium" ,
        "singular_form": "medium",
        "affix_matching": "hard" ,
        "easy_extra": "easy_extra" ,

    }
    
    difficulty_translations = {
        'easy': 'Makkelijk',
        'medium': 'Gemiddeld',
        'hard': 'Moeilijk',
        'easy_extra': 'Generiek'
    }
    
    # Dictionary to hold grouped exercises
    grouped = {}
    
    # Group exercises by type
    for exercise in exercises:
        # Handle both new (type, text, answer) and old (text, answer) formats
        if len(exercise) == 3:
            ex_type = exercise[0]
            ex_content = exercise[1]
            ex_answer = exercise[2]
        else:
            # Default type for backward compatibility
            ex_type = "custom"
            ex_content = exercise[0]
            ex_answer = exercise[1]
        
        if ex_type not in grouped:
            grouped[ex_type] = {
                "heading": heading_templates.get(ex_type, f"Voltooi de volgende {ex_type} oefeningen:"),
                "exercises": []
            }
        
        # Format the exercise content based on the type
        if ex_type == "identify":
            # Extract just the word from "Identify the free and bound morphemes in the following word: {word}."
            try:
                word = ex_content.split("word: ")[1].strip(".")
                formatted_content = word
            except IndexError:
                formatted_content = ex_content
        elif ex_type == "fill_in_the_blank":
            # Keep the full sentence for fill-in-the-blank
            formatted_content = ex_content
        elif ex_type == "alternative_form":
            # Extract the morpheme and word
            try:
                parts = ex_content.split("Using the free morpheme '")[1].split("' from the word '")
                morpheme = parts[0]
                word = parts[1].split("',")[0]
                formatted_content = f"'{morpheme}' from '{word}'"
            except IndexError:
                formatted_content = ex_content
        elif ex_type == "plural_form":
            # Extract just the word from "Give the plural form of the word: {word}"
            try:
                word = ex_content.split("word: ")[1]
                formatted_content = word
            except IndexError:
                formatted_content = ex_content
        elif ex_type == "singular_form":
            # Extract just the word from "Give the singular form of the word: {word}"
            try:
                word = ex_content.split("word: ")[1]
                formatted_content = word
            except IndexError:
                formatted_content = ex_content
        elif ex_type == "error_correction":
            # Keep the full sentence for error correction
            formatted_content = ex_content
        else:
            # Default formatting for other types
            formatted_content = ex_content
        
        grouped[ex_type]["exercises"].append((formatted_content, ex_answer))
    
    # Convert to list format for template rendering
    
    
    result = []
    for ex_type, data in grouped.items():
        result.append({
            "type": ex_type,
            "difficulty" : difficulty_translations.get(exercise_difficulty.get(ex_type, 'Onbekend'), 'Onbekend'),
            "heading": data["heading"],
            "exercises": data["exercises"]
        })
    
    return result

#@csrf_exempt # REMOVE FOR PRODUCTION
def generate(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("text", "").strip()
            difficulty = data.get("difficulty", "")
            
            

            
            if not text or not difficulty:
                return JsonResponse({"error": "Geen tekst ontvangen"}, status=400)
            if len(text.split()) > 1200:
                return JsonResponse({"error": "Ingevoerde tekst is te lang"}, status=400)

            # Define number of exercises based on difficulty
            nr_of_identify = 0
            nr_of_fill_in_blanks = 0
            nr_of_alternative = 0
            nr_of_wrong_words = 0
            nr_of_affix = 0
            nr_find_compounds = 0
            nr_find_plurals = 0
            nr_find_diminutives = 0
            nr_of_plural_form = 0  
            nr_of_singular_form = 0 
            easy_extra = False
            
            if "easy_extra" in difficulty:
                easy_extra = True

            if "easy" in difficulty:
                nr_of_identify += 0
                nr_of_fill_in_blanks += 0
                nr_of_alternative += 0
                nr_of_wrong_words += 0
                nr_of_affix += 0
                nr_of_plural_form += 0
                nr_of_singular_form += 0
                nr_find_compounds += 1
                nr_find_plurals += 1
                nr_find_diminutives += 1


            if "medium" in difficulty:
                nr_of_identify += 0
                nr_of_fill_in_blanks += 3
                nr_of_alternative += 0
                nr_of_wrong_words += 3
                nr_of_affix += 1
                nr_find_compounds += 0
                nr_of_plural_form += 3
                nr_of_singular_form += 3
                nr_find_plurals += 0
                nr_find_diminutives += 0


            if "hard" in difficulty:
                nr_of_identify += 2
                nr_of_fill_in_blanks += 0
                nr_of_alternative += 2
                nr_of_wrong_words += 0
                nr_of_affix += 0
                nr_of_plural_form += 0
                nr_of_singular_form += 0
                nr_find_compounds += 0
                nr_find_plurals += 0
                nr_find_diminutives += 0


            
            
            # Generate exercises with the new parameters
            exercises, morphemes, important_words = generate_exercises(
                text, 
                easy_extra,
                nr_of_identify, 
                nr_of_fill_in_blanks, 
                nr_of_alternative, 
                nr_of_wrong_words, 
                nr_of_affix, 
                nr_find_compounds,
                nr_find_plurals,
                nr_find_diminutives,
                nr_of_plural_form,  
                nr_of_singular_form  

            )      
            
            # Store in session
            request.session["text"] = text
            request.session["difficulty"] = difficulty
            request.session["exercises"] = exercises  # Store exercises in session
            request.session["exercise_types"] = exercise_types
            request.session["morphemes"] = morphemes
            request.session["important_words"] = important_words
            request.session['title'] = "Opdrachten over Morfologie" # init title

            print(f"exercise_types: {exercise_types}")

            return JsonResponse({"result_url": reverse('results')})

        except Exception as e:
            print(f"Error: {e}")
            print(traceback.format_exc())  # Print the full traceback for debugging
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
    title = request.session.get("title")
    text = request.session.get("text", "Geen tekst ingevoerd")
    difficulty = request.session.get("difficulty", "Niet gespecificeerd")
    exercises = request.session.get("exercises", [])
    exercise_types_dict = request.session.get("exercise_types", [])
    important_words = request.session.get("important_words", [])

    # Filter out "find_compounds" from exercise_types_dict
    filtered_exercise_types = {k: v for k, v in exercise_types_dict.items() if k != "find_compounds"}
    
    # Group the exercises
    grouped_exercises = group_exercises(exercises)
    
    # tokenize text and embolden important words
    
    # English to dutch translation for difficulty level
    text_html = embolden(text, important_words)
    difficulty_translations = {
        'easy': 'Makkelijk',
        'medium': 'Gemiddeld',
        'hard': 'Moeilijk',
        'easy_extra': 'Generieke oefeningen'
    }
    
    difficulty_text = [difficulty_translations.get(d, d) for d in difficulty]          
    difficulty_text = ', '.join(difficulty_text)

    return render(request, "webapp/results.html", {
        "text_html": text_html,
        "text": text,
        "difficulty": difficulty,
        "difficulty_text": difficulty_text,
        "exercises": exercises,  # Keep the original for backward compatibility
        "grouped_exercises": grouped_exercises,  # Add the grouped exercises
        "exercise_types": filtered_exercise_types,  # Use the filtered dictionary
        "exercise_examples": exercise_examples,
        "title": title
    })


def embolden(text, important_words):
    # filter out any exercise types that are not in the dropdown menu
    filtered_exercise_types = {
        k: v for k, v in exercise_types.items() if k not in exercise_types_ignore
    }
    
    important_set = {w.lower() for w in important_words}
    tokens = re.findall(r'\w+|\W+', text)
    wrapped_tokens = []
    for idx, token in enumerate(tokens):
        if token.strip().isalnum():
            context = {
                'token': token,
                'token_id': idx,
                'is_important': token.lower() in important_set,
                'exercise_types': filtered_exercise_types,
            }
            wrapped = render_to_string('webapp/partials/dropdown.html', context)
        else:
            wrapped = token
        wrapped_tokens.append(wrapped)

    return mark_safe(''.join(wrapped_tokens))

def exercise_pdf(request):
    exercises = request.session.get('exercises', [])
    version = request.GET.get('version', 'student')  # Default to student version
    title = request.session.get('title', 'Opdrachten over Morfologie')

    # Group the exercises
    grouped_exercises = group_exercises(exercises)

    template = 'webapp/answers_pdf.html' if version == 'teacher' else 'webapp/exercise_pdf.html'
    filename = f"exercises_{version}.pdf"

    # Render template to HTML string
    html = render_to_string(template, {
        'grouped_exercises': grouped_exercises,
        'title': title
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
            text = request.session.get('text', '')
            print("exercise_types: ", exercises_types)
            new_exercises = []
            for i, exercise in enumerate(exercises_types):
                exercise_count = int(exercise.get('count', 0)) if exercise.get('count', '').strip() else 0
                exercise_type = exercise.get('type', 'identify')
                index = len(old_exercises) / len(exercise_types)
                generated_exercises = utils_add_exercises(exercise_type, exercise_count, request.session.get("morphemes", [{'word': 'foutje', 'free': ['fout'], 'bound': {'prefixes': [], 'suffixes': ['je'], 'other': []}}]), text=text, index=index)
                new_exercises.extend(generated_exercises)
            combined_exercises = old_exercises + new_exercises
            request.session['exercises'] = combined_exercises
            
            # Group the exercises for the template
            grouped_exercises = group_exercises(combined_exercises)

            return render(request, 'webapp/partials/added_exercises.html', {
                'grouped_exercises': grouped_exercises
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
        
        # Group the exercises for the template
        grouped_exercises = group_exercises(exercises)
        
        return render(request, 'webapp/partials/added_exercises.html', {
            'grouped_exercises': grouped_exercises
        })

def update_exercise(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        index = data.get('index')
        new_exercise = data.get('exercise')
        new_answer = data.get('answer')
        exercise_type = data.get('type', '')
        type_index = data.get('type_index')
        
        exercises = request.session.get('exercises', [])
        
        if type_index:
            # Parse the type and index from the combined string (e.g., "identify-1")
            try:
                exercise_type, exercise_index = type_index.split('-')
                exercise_index = int(exercise_index) - 1  # Convert to 0-based index
                
                # Find the matching exercise in the list
                # Count exercises of the same type to find the right one
                count = 0
                for i, exercise in enumerate(exercises):
                    # Handle both tuple formats: (type, text, answer) and (text, answer)
                    current_type = exercise[0] if len(exercise) >= 3 else 'custom'
                    
                    if current_type == exercise_type:
                        if count == exercise_index:
                            # This is the one to update
                            if len(exercises[i]) >= 3:
                                exercises[i] = (current_type, new_exercise, new_answer)
                            else:
                                exercises[i] = (exercise_type, new_exercise, new_answer)
                            
                            request.session['exercises'] = exercises
                            return JsonResponse({'status': 'ok'})
                        count += 1
                
                return JsonResponse({'error': 'Exercise not found'}, status=404)
                
            except (ValueError, IndexError) as e:
                return JsonResponse({'error': f'Invalid type_index format: {str(e)}'}, status=400)
        
        elif index is not None:
            # Legacy support for direct index
            index = int(index)
            if 0 <= index < len(exercises):
                # If we have the type in the exercise tuple, keep it
                if len(exercises[index]) >= 3:
                    exercises[index] = (exercises[index][0], new_exercise, new_answer)
                else:
                    # For backwards compatibility
                    exercises[index] = (exercise_type, new_exercise, new_answer) if exercise_type else (new_exercise, new_answer)
                
                request.session['exercises'] = exercises
                return JsonResponse({'status': 'ok'})
            else:
                return JsonResponse({'status': 'invalid index'}, status=400)

    return JsonResponse({'error': 'invalid request'}, status=405)

def delete_exercise(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        index = data.get('index')
        type_index = data.get('type_index')
        
        exercises = request.session.get('exercises', [])
        
        if type_index:
            # Parse the type and index from the combined string (e.g., "identify-1")
            try:
                exercise_type, exercise_index = type_index.split('-')
                exercise_index = int(exercise_index) - 1  # Convert to 0-based index
                
                # Find the matching exercise in the list
                # Count exercises of the same type to find the right one
                count = 0
                for i, exercise in enumerate(exercises):
                    # Handle both tuple formats: (type, text, answer) and (text, answer)
                    current_type = exercise[0] if len(exercise) >= 3 else 'custom'
                    
                    if current_type == exercise_type:
                        if count == exercise_index:
                            # This is the one to delete
                            del exercises[i]
                            request.session['exercises'] = exercises
                            
                            # Group the exercises for the template
                            grouped_exercises = group_exercises(exercises)
                            
                            return render(request, 'webapp/partials/added_exercises.html', {
                                'grouped_exercises': grouped_exercises
                            })
                        count += 1
                
                return JsonResponse({'error': 'Exercise not found'}, status=404)
                
            except (ValueError, IndexError) as e:
                return JsonResponse({'error': f'Invalid type_index format: {str(e)}'}, status=400)
                
        elif index is not None:
            # Legacy support for direct index
            index = int(index)
            if 0 <= index < len(exercises):
                del exercises[index]
                request.session['exercises'] = exercises
                
                # Group the exercises for the template
                grouped_exercises = group_exercises(exercises)
                
                return render(request, 'webapp/partials/added_exercises.html', {
                    'grouped_exercises': grouped_exercises
                })
            return JsonResponse({'error': 'invalid index'}, status=400)
            
        return JsonResponse({'error': 'No index or type_index provided'}, status=400)
    return JsonResponse({'error': 'invalid method'}, status=405)


def add_custom_exercise(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        exercise_text = data.get('exercise_text', '')
        answer_text = data.get('answer_text', '')
        exercise_type = data.get('exercise_type', 'custom')  # Allow specifying a type for custom exercises
        
        if not exercise_text.strip():
            return JsonResponse({'error': 'Exercise text cannot be empty'}, status=400)
            
        exercises = request.session.get('exercises', [])
        exercises.append((exercise_type, exercise_text, answer_text))
        request.session['exercises'] = exercises
        
        # Group the exercises for the template
        grouped_exercises = group_exercises(exercises)
        
        return render(request, 'webapp/partials/added_exercises.html', {
            'grouped_exercises': grouped_exercises
        })
        
    return JsonResponse({'error': 'Invalid request'}, status=405)

def update_title(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title', '')
        
        if not title.strip():
            return JsonResponse({'error': 'Title cannot be empty'}, status=400)
            
        request.session['title'] = title
        
        return JsonResponse({'status': 'ok'})
        
    return JsonResponse({'error': 'Invalid request'}, status=405)

from django.shortcuts import render, redirect

def store_api_key(request):

    if request.method == 'POST':
        api_key = request.POST.get('api_key')
        restore = request.POST.get('restore_key')
        if restore:
            request.session['user_api_key'] = ""
        else:
            if api_key:
                request.session['user_api_key'] = api_key
        return redirect(request.META.get('HTTP_REFERER', '/'))