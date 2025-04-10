from google import genai
from .keys import gemini_API_key
import json
import re
import random


client = genai.Client(api_key=gemini_API_key)
model = "gemini-2.0-flash"

def generate_text(prompt):
    response = client.models.generate_content(
    model=model,
    contents=prompt,
)
    return response.text

def remove_markdown(text):
    # Remove any markdown formatting
    pattern = r'```json|```'
    # Substitute with empty string
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

def extract_important_words(text, nr_of_words):
    # returns most important words in text as a list of strings
    prompt = f"Extract the {nr_of_words} most important Dutch words from the following Dutch text. Do not add any named entities. The words will be used to make exercises about morphology, so mainly choose words that consist of multiple morphemes. Give it as an JSON array named 'words' Do not add the json markdown formatting, just plain text. Text:  {text}"
    important_words_string = generate_text(prompt)
    important_words_string = remove_markdown(important_words_string)
    words = json.loads(important_words_string)['words']
    return words

def extract_morphemes(words):
    prompt = f"Identify the morphemes in the following Dutch words and structure the result as a JSON object. The JSON should contain a 'words' list, where each word is represented as an object with three keys: 'word' (containing the word), 'free' (for free morphemes) and 'bound' (for bound morphemes). The 'bound' morphemes should be further categorized into 'prefixes', 'suffixes', and 'other'. DO NOT include markdown JSON formatting syntax like triple backticks in your answer. Only return the JSON structure as plain text. Words:\n{words}"
    morphemes_string = generate_text(prompt)
    morphemes_string = remove_markdown(morphemes_string)
    print(morphemes_string)
    morphemes = json.loads(morphemes_string)['words']
    return morphemes

def exercise_identify(dict_word):
    """
    Generates an identify exercise for the given word
    expects a dict object with the following structure:
    {
        "word": "vuurwerkverboden",
        "free": ["vuur", "werk", "verbod"],
        "bound": {
            "prefixes": [],
            "suffixes": ["en"],
            "other": []
    }
    """
    word = dict_word['word']
    free = dict_word['free']
    bound = dict_word['bound']
    prefixes = bound['prefixes']
    suffixes = bound['suffixes']
    other = bound['other']

    exercise_text = f"Identify the free and bound morphemes in the following word: {word}."
    answer_text = f"Free morphemes: {free}. Bound morphemes: {bound}"
    
    return (exercise_text, answer_text)

def exercise_fill_in_the_blank(dict_word):
    """
    Generates a fill in the blanks exercise for the given word
    expects a dict object with the following structure:
    {
        "word": "vuurwerkverboden",
        ...
    }
    """
    word = dict_word['word']
    prompt = f"Generate a Dutch sentence containing the Dutch word '{word}', but in a changed form. For example, change the tense, make it plural, make it dimminiative, or anything else (but don't add new words to the word). Make sure the sentence is grammatically correct. The sentence should be a complete sentence and not just a fragment. Return your answer formatted as JSON with two keys: sentence (containing the full sentence including the word) and word (containing the modified word)  Do not include any markdown formatting like triple backticks in your answer. Just return the plain text of the sentence."	
    output_json = generate_text(prompt)
    output = remove_markdown(output_json)
    output = json.loads(output)
    sentence = output['sentence']
    modified_word = output['word']
    sentence_blanked = re.sub(modified_word, '_____', sentence)
    exercise_text = f"Fill in the blank in the following sentence: \n ({word}) {sentence_blanked}"
    answer_text = modified_word
    return exercise_text, answer_text

def exercise_alternative_form(dict_word):
    """
    Generates an exercise asking students to provide an alternative form of a free morpheme.
    Uses LLM to provide 3 examples if possible.
    """
    word = dict_word['word']
    free_morphemes = dict_word['free']
    
    if not free_morphemes:
        print("no free morphelemes found")
        return None  # Skip if no free morphemes found

    selected_morpheme = free_morphemes[0]

    # Prompt the LLM to suggest alternatives (if they exist)
    prompt = (
        f"Provide 3 alternative forms or words that contain the Dutch free morpheme '{selected_morpheme}', "
        f"taken from the word '{word}'. These can include plural forms, diminutives, compounds, or verb forms. "
        f"Return the result as a JSON array. If no alternatives exist, return an empty array []."
    )

    try:
        output_raw = generate_text(prompt)
        output_clean = remove_markdown(output_raw)
        alternatives = json.loads(output_clean)
        if not isinstance(alternatives, list):
            alternatives = []
    except Exception:
        alternatives = []

    # Build the exercise and answer
    exercise_text = (
        f"Using the free morpheme '{selected_morpheme}' from the word '{word}', "
        f"write another form or word that contains this morpheme."
    )

    if alternatives:
        answer_text = f"Example answers: {', '.join(alternatives)}. Other answers could include plural forms, compound words, or verb forms."
    else:
        answer_text = "Other answers could include plural forms, compound words, or verb forms."

    return exercise_text, answer_text

def generate_affix_matching_exercises(morphemes, important_words, count):
    exercises = []
    candidates = []

    for m in morphemes:
        word = m.get('word', '')
        if word not in important_words:
            continue

        free = m.get('free', [])
        bound = m.get('bound', {})
        prefixes = bound.get('prefixes', [])
        suffixes = bound.get('suffixes', [])
        other = bound.get('other', [])

        all_morphemes = free + prefixes + suffixes + other

        if (len(all_morphemes) > 2):
            for i in range(1, len(word)):
                left = word[:i]
                right = word[i:]
                if left in all_morphemes:
                    candidates.append((left, word[i:], word))
                if right in all_morphemes:
                    candidates.append((word[:i], right, word))
        

        if len(all_morphemes) == 2:
            candidates.append((all_morphemes[0], all_morphemes[1], word))

        if (len(all_morphemes) > 2):
            for i in range(1, len(word)):
                left = word[:i]
                right = word[i:]
                if left in all_morphemes:
                    candidates.append((left, word[i:], word))
                elif right in all_morphemes:
                    candidates.append((word[:i], right, word))

    selected = random.sample(candidates, min(count, len(candidates)))
    if not selected:
        return exercises

    left_parts = [item[0] for item in selected]
    right_parts = [item[1] for item in selected]
    words = [item[2] for item in selected]

    shuffled_rights = right_parts.copy()
    random.shuffle(shuffled_rights)

    # Build the question
    question = "Match morphemes on the left with the correct morphemes on the right:"
    rows = "".join(
        f"<tr><td>{i+1}. {left_parts[i]}</td><td>{chr(65+i)}. {shuffled_rights[i]}</td></tr>"
        for i in range(len(left_parts))
    )
    table = f"<table style='margin-left:auto; margin-right:auto;'>{rows}</table>"
    full_question = f"{question}<br><br>{table}"

    # Build the answer key
    answer_mapping = []
    for i, right in enumerate(right_parts):
        label = chr(65 + shuffled_rights.index(right))
        answer_mapping.append(f" {i+1} - {label} ({words[i]}) <br>")

    answer = "\n".join(answer_mapping)
    exercises.append((full_question, answer))

    return exercises


def exercise_error_correction(dict_word):
    """
    Generates an error correction exercise for a given word dict like {'word': 'run'}
    """
    word = dict_word['word']
    prompt = (
        f"Generate a sentence in Dutch for the word '{word}' where the word is used in its wrong form. "
        "For example, a similar english sentence could be if the word is 'run' then the sentence is 'He runned fast'.\n"
        "Answer format: sentence: <sentence>\nanswer: wrong_word = correct_word"
    )

    response = generate_text(prompt)
    try:
        parts = response.strip().split("answer:")
        sentence = parts[0].replace("sentence:", "").strip()
        correction = parts[1].strip()

        if '=' in correction:
            wrong_word, correct_word = map(str.strip, correction.split('='))
            sentence_blanked = re.sub(rf'\\b{re.escape(wrong_word)}\\b', '_', sentence)
            exercise_text = f"Correct the error in the following sentence: \n {sentence_blanked}"
            answer_text = f"{wrong_word} = {correct_word}"
        else:
            exercise_text = f"[Bad format for correction: '{correction}']"
            answer_text = "Could not parse correction."

    except Exception as e:
        exercise_text = f"[Error parsing response for word '{word}']"
        answer_text = "Could not generate."

    return exercise_text, answer_text

def generate_exercises(text, nr_of_identify, nr_of_fill_in_blanks, nr_of_alternative_forms, nr_wrong, nr_affix):
    """
    Generates exercises for the given text 
    returns in format exercises = [(exercise_text, answer_text), ...]
    """
    total_words_needed = nr_of_identify + nr_of_fill_in_blanks + nr_of_alternative_forms + nr_wrong + nr_affix
    important_words = extract_important_words(text, total_words_needed)
    morphemes = extract_morphemes(important_words)
    exercises = []
    word_index = 0
    
    # Add identify exercises
    for i in range(0, nr_of_identify):
        exercise = exercise_identify(morphemes[i])
        exercises.append(exercise)
    word_index = nr_of_identify

    # Add fill in the blank exercises
    for i in range(nr_of_fill_in_blanks):
        exercise = exercise_fill_in_the_blank(morphemes[i + word_index])
        exercises.append(exercise)
    word_index += nr_of_fill_in_blanks

    for i in range(nr_of_alternative_forms):
        exercise = exercise_alternative_form(morphemes[i + word_index])
        exercises.append(exercise)
    word_index += nr_of_alternative_forms

    for i in range(nr_wrong):
        exercise = exercise_error_correction(morphemes[i + word_index])
        exercises.append(exercise)
    word_index += nr_wrong

    if nr_affix > 0:
        print(nr_affix)
        exercise = generate_affix_matching_exercises(morphemes, important_words, nr_affix)
        exercises.extend(exercise)
        print(exercise)

    return exercises, morphemes, important_words
    


def add_exercises(type, nr_of_exercises, morphemes, index=0):
    """
    Adds exercises to the list of exercises based on the type and number of exercises
    """
    index = int(index) + 1
    exercises = []
    if type == "identify":
        # Add identify exercises
        for i in range(nr_of_exercises):
            # tries to use a not-used word, if not available, it starts at the beginning again 
            j = (i + index - 1) % len(morphemes)
            # exercise = (f"exercise {i} with morpheme {morphemes[j]['word']}", "answer {i}")
            exercise = exercise_identify(morphemes[j])
            exercises.append(exercise)
    elif type == "fill_in_the_blank":
        # Add fill in the blank exercises
        for i in range(nr_of_exercises):
 
            j = (i + index - 1) % len(morphemes)
            # exercise = (f"exercise {i} with morpheme {morphemes[j]['word']}", "answer {i}")
            exercise = exercise_fill_in_the_blank(morphemes[j])
            exercises.append(exercise)
    elif type == "alternative":
        # Add alternative exercises
        for i in range(nr_of_exercises):
 
            j = (i + index - 1) % len(morphemes)
            exercise = exercise_alternative_form(morphemes[j])
            exercises.append(exercise)
    
    elif type == "wrong_word_sentence":
        for i in range(nr_of_exercises):
            j = (i + index - 1) % len(morphemes)
            exercise = exercise_error_correction(morphemes[j])
            if exercise:  # Check if exercise is not None
                exercises.append(exercise)
        
    elif type == "affix_matching":
        # For affix_matching, we generate a complete new exercise with nr_of_exercises items
        if nr_of_exercises > 0:
            important_words = [m.get('word', '') for m in morphemes if 'word' in m]
            nr_of_words = 4 if len(morphemes) > 4 else len(morphemes)
            matching_exercises = generate_affix_matching_exercises(morphemes, important_words, nr_of_words)
            exercises.extend(matching_exercises)
    else:
        raise ValueError("Invalid exercise type.")
    return exercises

def generate_exercise_given_word(word, exercise_type):
    morphemes = extract_morphemes([word])
    exercise = []
    print(exercise_type)
    if exercise_type == 1:
        exercise = exercise_identify(morphemes[0])
    elif exercise_type == 2:
        exercise = exercise_fill_in_the_blank(morphemes[0])
    elif exercise_type == 3:
        exercise = exercise_alternative_form(morphemes[0])
    elif exercise_type == 4:
        exercise = exercise_error_correction(morphemes[0])
    # elif exercise_type == 5:
    #     exercise = generate_affix_matching_exercises(morphemes[0])
    else:
        raise ValueError("Invalid exercise type.")
    return exercise
    
# example text 

#text = "Hallo kinderen! Vandaag gaan we een spannende reis maken naar de wonderlijke wereld van bijen. Bijen zijn hele kleine, maar superbelangrijke beestjes voor onze natuur en zelfs voor ons eten!Wat zijn bijen?Bijen zijn insecten die heel goed zijn in bestuiven. Dat betekent dat ze stuifmeel van de ene bloem naar de andere brengen. Zo helpen ze planten om vruchten te maken, zoals appels en kersen. Er zijn heel veel verschillende soorten bijen, maar de meeste wonen samen in een bijenkorf.Hoe leven bijen?In een bijenkorf woont een grote bijenfamilie. Er is een koninginbij, werkbijen, en mannetjesbijen. De koningin is de enige die eitjes legt. De werkbijen doen bijna al het werk: ze verzamelen nectar, maken honing, poetsen de bijenkorf, en zorgen voor de babybijtjes. De mannetjesbijen helpen de koningin met het krijgen van nieuwe bijtjes."
#generated = generate_exercises(text, 2, 2, 2)
#print(generated)