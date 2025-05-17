from google import genai
from .keys import gemini_API_key
import json
import re
import random
from .middleware import get_current_request

try:
    import spacy
    print("Spacy is used")
    NLP_BACKEND = "spacy"
except ImportError:
    try:
        from pattern.nl import parse
        print("pattern.nl is used")
        NLP_BACKEND = "pattern"
    except ImportError:
        print("No NLP package is available")
        NLP_BACKEND = None




client = genai.Client(api_key=gemini_API_key)
model = "gemini-2.0-flash"

def get_client():
    request = get_current_request()
    print(request)
    if not request:
        return client
    else:
        key = request.session.get('user_api_key')
    if not key or key == "":
        return client
    else:
        return genai.Client(api_key=key)

def generate_text(prompt):
    
    client_new = get_client()
    response = client_new.models.generate_content(
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
    important_words_string = normalize_important_words(important_words_string)
    words = json.loads(important_words_string)['words']
    return words


# Makes sure if the important words are in the correct format (list of strings or dict with 'words' key)
def normalize_important_words(important_words_string):
    try:
        data = json.loads(important_words_string)
        if isinstance(data, dict) and 'words' in data:
            return json.dumps(data)
        elif isinstance(data, list):
            return json.dumps({'words': data})
        else:
            raise ValueError("Invalid format: expected a dict with 'words' key or a list of words.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    
    
def extract_morphemes(words):
    prompt = f"Identify the morphemes in the following Dutch words and structure the result as a JSON object. The JSON should contain a 'words' list, where each word is represented as an object with three keys: 'word' (containing the word), 'free' (for free morphemes) and 'bound' (for bound morphemes). The 'bound' morphemes should be further categorized into 'prefixes', 'suffixes', and 'other'. DO NOT include markdown JSON formatting syntax like triple backticks in your answer. Only return the JSON structure as plain text. Words:\n{words}"
    morphemes_string = generate_text(prompt)
    morphemes_string = remove_markdown(morphemes_string)
    # print(morphemes_string)
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

    #pretty print
    bound_string = ""
    for cat in bound:
        if len(bound[cat]) > 0:
            bound_string += (f"<br>{cat}: {bound[cat]}")

    exercise_text = f"Identify the free and bound morphemes in the following word: {word}."
    answer_text = f"Free morphemes: {free}. <br>  Bound morphemes: {bound_string}"
    
    return ("identify", exercise_text, answer_text)

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
    # prompt = f"Generate a Dutch sentence containing the Dutch word '{word}', but in a changed form. For example, change the tense, make it plural/singular (but don't add new morphemes to the word). Make sure the sentence is grammatically correct. The sentence should be a complete sentence and not just a fragment. DO NOT return the exact same form I gave you ({word}). Return your answer formatted as JSON with two keys: sentence (containing the full sentence including the word) and word (containing the modified word). Do not include any markdown formatting like triple backticks in your answer. Just return the plain text of the sentence."	
    
    # prompt = f"First get the root form or infinitive of the Dutch word '{word}'. Then, change the word to plural/singular or change the tense. Generate a Dutch sentence that contains that changed word that is grammatically correct. The sentence should be a complete sentence and not just a fragment. The word SHOULD NOT be in the exact same form as the root from. Return your answer formatted as JSON with three keys: sentence (containing the full sentence including the word), root (containing the root or infinitive of the original word) and changed_word (containing the changed version of the word). Do not include any markdown formatting like triple backticks in your answer. " 
    
    prompt = f"You have two tasks. Task 1: find the infiniive or root form of the Dutch word {word}, from now referred to as 'root'. Task 2: change the tense of the root word OR make it plural OR . Then generate a full Dutch sentence with the new word. It should be DIFFERENT than the root from. Return your answer formatted as JSON with three keys: root (containing the root),  sentence (containing the full sentence including the word), and changed_word (containing the changed version of the word like in the sentence). Do not include any markdown formatting like triple backticks in your answer. " 
    output_json = generate_text(prompt)
    output = remove_markdown(output_json)
    output = json.loads(output)
    
    sentence = output['sentence']
    # modified_word = output['word']
    root = output['root']
    modified_word = output['changed_word']
    sentence_blanked = re.sub(modified_word, '_____', sentence)
    #exercise_text = f"Fill in the blank in the following sentence: \n ({word}) {sentence_blanked}"
    exercise_text = f"({root}) {sentence_blanked}"
    answer_text = modified_word
    return ("fill_in_the_blank", exercise_text, answer_text)

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
        answer_text = f"Mogelijke antwoorden: {', '.join(alternatives)}. Andere mogelijke antwoorden kunnen bijv. meervoudsvormen, samengestelde woorden of werkwoordsvormen zijn."
    else:
        answer_text = "Mogelijke antwoorden kunnen bijv. meervoudsvormen, samengestelde woorden of werkwoordsvormen zijn."

    return ("alternative_form", exercise_text, answer_text)

def exercise_generate_affix_matching(morphemes, important_words, count):
    exercises = []
    candidates = []

    for m in morphemes:
        word = m.get('word', '')
        # check if word is in important words
        if word not in important_words:
            continue

            
        free = m.get('free', [])
        bound = m.get('bound', {})
        prefixes = bound.get('prefixes', [])
        suffixes = bound.get('suffixes', [])
        other = bound.get('other', [])

        # make list with the words morphemes
        all_morphemes = free + prefixes + suffixes + other

        # if there are more than 2 morphemes, go over all letters from left to right till a morpheme is found on the left or right
        if (len(all_morphemes) > 2):
            for i in range(1, len(word)):
                left = word[:i]
                right = word[i:]
                if left in all_morphemes or right in all_morphemes:
                    candidates.append((left, right, word))
        
        # if there are 2 morphemes, add them to the candidates list
        if len(all_morphemes) == 2:
            candidates.append((all_morphemes[0], all_morphemes[1], word))


    selected = random.sample(candidates, min(count, len(candidates)))
    if not selected:
        return exercises

    left_parts = [item[0] for item in selected]
    right_parts = [item[1] for item in selected]
    words = [item[2] for item in selected]

    shuffled_rights = right_parts.copy()
    random.shuffle(shuffled_rights)

    # Build the question
    #question = "Match morphemes on the left with the correct morphemes on the right:"
    question = ""
    rows = "".join(
        f"<tr><td>{i+1}. {left_parts[i]}</td><td>{chr(65+i)}. {shuffled_rights[i]}</td></tr>"
        for i in range(len(left_parts))
    )
    table = f"<table style='margin-left:auto; margin-right:auto;'>{rows}</table>"
    full_question = f"{question} {table}"

    # Build the answer key
    answer_mapping = []
    for i, right in enumerate(right_parts):
        label = chr(65 + shuffled_rights.index(right))
        answer_mapping.append(f" {i+1} - {label} ({words[i]}) <br>")

    answer = "\n".join(answer_mapping)
    exercises.append(("affix_matching", full_question, answer))

    return exercises

def exercise_error_correction(dict_word):
    """
    Generates an error correction exercise for a given word dict like {'word': 'run'}
    """
    word = dict_word['word']
    prompt = (
        f"Generate a sentence in Dutch for the word '{word}' where the word is used in its wrong form, for example in the wrong tense, plural or singular form. "
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
            #exercise_text = f"Correct the error in the following sentence: \n {sentence_blanked}"
            exercise_text = f"{sentence_blanked}"
            answer_text = f"{wrong_word} = {correct_word}"
        else:
            exercise_text = f"[Bad format for correction: '{correction}']"
            answer_text = "Could not parse correction."

    except Exception as e:
        exercise_text = f"[Error parsing response for word '{word}']"
        answer_text = "Could not generate."

    return ("error_correction", exercise_text, answer_text)

def exercise_find_all(word_type, text):
    """
    Generates a find all {word_type} exercise for the given text
    expects:
      the full text as text
      word type from [compound, plural, diminutive]
    """
    prompt = f"Find all {word_type} words in the following Dutch text. If there are none, return 'None'. Return your answer formatted as a JSON list. Do not include any markdown formatting like triple backticks in your answer. The text: {text}"	
    output_json = generate_text(prompt)
    output = remove_markdown(output_json)
    output = json.loads(output)
    output = list(dict.fromkeys(output))
    exercise_text = f"Find all the {word_type} words in the given text."
    exercise_text = f""
    answer_text = output
    return ("find_"+word_type, exercise_text, answer_text)

def exercise_plural_form(dict_word):
    """
    Generates an exercise asking students to provide the plural form of a word.
    Uses LLM to get the plural form without strict validation.
    """
    word = dict_word['word']
    
    # Simplified prompt that just asks for the plural form
    prompt = (
        f"What is the plural form of the Dutch word '{word}'? "
        f"Return ONLY the plural form as plain text. Don't include explanations. "
        f"If the word does not have any plural form, return the word itself. "
        f"If the word is already in plural form, return the word 'PLURAL'"  
    )
    
    # try:
    plural_form = generate_text(prompt).strip()
    print(f"singular: {word}, plural form: {plural_form}")
    if plural_form == "PLURAL":
        return None, None
            
    exercise_text = f"Give the plural form of the word: {word}"
    answer_text = plural_form
    return ("plural_form", exercise_text, answer_text)
        
def exercise_singular_form(dict_word):
    """
    Generates an exercise asking students to provide the singular form of a word.
    Uses LLM to get the singular form without strict validation.
    """
    word = dict_word['word']
    
    # Simplified prompt that just asks for the singular form
    prompt = (
        f"What is the singular form of the Dutch word '{word}'? "
        f"Return ONLY the singular form as plain text. Don't include explanations. "
        f"If the word is already in singular form, return the word 'SINGULAR' (space) and the plural form."
    )
    
    
    singular_form = generate_text(prompt).strip()
    print("word: ", word, "singular: ", singular_form)
    # Basic validation - make sure we got something different than the input
    if  "SINGULAR" in singular_form:
        plural = singular_form.split(" ")[1]
        exercise_text = f"Give the singular form of the word: {plural}"
        return ("singular_form", exercise_text, word)
    
    exercise_text = f"Give the singular form of the word: {word}"
    answer_text = singular_form    
    return ("singular_form", exercise_text, answer_text)
        

def find_specific_POS(pos_tag, dict_words):
    """
    Finds all words with a specific part of speech (POS) tag in the given list of words.
    Uses spaCy for POS tagging.
    """
    
    nouns = []
    singular_nouns = []
    plural_nouns = []
    
    if NLP_BACKEND == "spacy":
    
        nlp = spacy.load("nl_core_news_sm")
        for word in dict_words:
            doc = nlp(word['word'])
            for token in doc:
                number = token.morph.get("Number")[0] if token.morph.get("Number") else "Unknown"
                if token.pos_ == pos_tag:
                    nouns.append(word)
                    if number == "Plur":
                        plural_nouns.append(word)
                    if number == "Sing":
                        singular_nouns.append(word)
                            
    elif NLP_BACKEND == "pattern":
        for item in dict_words:
            word = item["word"]
            parsed = parse(word, lemmata=True).split()
            
            if not parsed or not parsed[0]:
                continue  # skip if nothing parsed

            parsed_word = parsed[0][0]  # Only one word
            word_text, tag, _, _, lemma = parsed_word
            print(word_text, tag, _, _, lemma)
            if tag == "NN":
                singular_nouns.append(item)
                nouns.append(item)
            if tag == "NNS":
                plural_nouns.append(item)
                nouns.append(item)
            
        
    # all_words = [d['word'] for d in dict_words]
    
    # prompt = (
    #     f"Return all Dutch NOUNS in the following list: '{all_words}'? "
    #     f"Return the result as a JSON array. If there are no nouns, return an empty array []."
    # )
    
    # output_json = generate_text(prompt)
    # output = remove_markdown(output_json)
    # output = json.loads(output)
    # print('api noun list: ', output)
    # singulars = []
    # plurals = []
    # nouns = []

    # for word in dict_words:
    #     print(word['word'], output)
    #     if word['word'] in output:
    #         nouns.append(word)
    #         print('True')
    #         if word['word'].endswith('en') or word['word'].endswith('s'):
    #             plurals.append(word)
    #         else:
    #             singulars.append(word)


    return nouns, singular_nouns, plural_nouns

def easy_extra_exercises(nr_of_exercises):
    q1 = "Geef drie voorbeelden van een gebonden morfeem"
    a1 = "Mogelijke voorbeelden zijn: -en, -s, -tje"
    q2 = "Geef drie voorbeelden van een vrij morfeem"
    a2 = "Voorbeelden zijn: huis, boom, auto, rood"
    q3 = "Leg uit wat een samenstelling is"
    a3 = "Een samenstelling is een woord dat bestaat uit twee of meer vrije morfemen die samen een nieuwe betekenis vormen. Bijvoorbeeld: 'tafelblad' is een samenstelling van 'tafel' en 'blad'."
    q4 = "Leg uit wat een afleiding is"
    a4 = "Een afleiding is een nieuw woord dat ontstaat door een voor- of achtervoegsel toe te voegen aan een bestaand woord, waardoor de betekenis van het verandert. Bijvoorbeeld: 'vaar' wordt 'gevaar' door het achtervoegsel 'ge-' toe te voegen."
    q5 = "Leg uit wat een verbuiging is"
    a5 = "Een verbuiging is een woord dat bestaat uit een of meerdere vrije en gebonden morfemen, maar hierbij ontstaat geen nieuwe betekenis. Het woord wordt aangepast zodat het past in de grammaticale context, zoals getal of geslacht. Bijvoorbeeld: 'klein' wordt 'kleiner' of 'hond' wordt 'honden'."
    q6 = "Welke soorten verbuigingen zijn er?"
    a6 = "Er zijn verschillende soorten verbuigingen, zowaaronder: meervoud (bijvoorbeeld 'kat' wordt 'katten'), vergelijkingen (bijvoorbeeld 'klein' wordt 'kleiner'), buiging -s (bijvoorbeeld 'rood' wordt 'roods'), buiging -e (bijvoorbeeld 'mooi' wordt 'mooie') en verkleinwoorden (bijvoorbeeld 'huis' wordt 'huisje')."
    q7 = "Leg uit wat een vervoeging is"
    a7 = "Een vervoeging is een verandering van een werkwoord om het aan te passen aan de tijd, persoon of getal. Bijvoorbeeld: 'werk' wordt 'werkte' in de verleden tijd."
    exercises = [("easy_extra", q1, a1), ("easy_extra", q2, a2), ("easy_extra", q3, a3), ("easy_extra", q4, a4), ("easy_extra", q5, a5), ("easy_extra", q6, a6), ("easy_extra", q7, a7)]
    chosen_exercises = random.sample(exercises, min(nr_of_exercises, len(exercises)))
    return chosen_exercises

def generate_exercises(text, easy_extra, nr_of_identify, nr_of_fill_in_blanks, nr_of_alternative_forms, nr_wrong, nr_affix, nr_find_compounds, nr_find_plural, nr_find_diminutive, nr_of_plural=0, nr_of_singular=0):
    """
    Generates exercises for the given text 
    returns in format exercises = [(exercise_type, exercise_text, answer_text), ...]
    Handles cases where the number of exercises exceeds available words by reusing words
    """
    # Calculate total words needed
    total_words_needed = nr_of_identify + nr_of_fill_in_blanks + nr_of_alternative_forms + nr_wrong + nr_find_compounds + nr_find_plural + nr_find_diminutive + nr_of_plural + nr_of_singular + 4
    
    # Extract important words with a reasonable limit (avoid too large API calls)
    max_words_to_extract = min(total_words_needed, 30)
    important_words = extract_important_words(text, max_words_to_extract)
    morphemes = extract_morphemes(important_words)
    
    exercises = []
    word_index = 0
    
    # add easy_extra exercises
    if easy_extra:
        easy_exercises = easy_extra_exercises(5)
        exercises.extend(easy_exercises)

    # Add identify exercises
    for i in range(nr_of_identify):
        # Use modulo to wrap around if we exceed the available words
        word_idx = i % len(morphemes)
        exercise = exercise_identify(morphemes[word_idx])
        exercises.append(exercise)
    word_index += nr_of_identify

    # Add fill in the blank exercises
    for i in range(nr_of_fill_in_blanks):
        # Use modulo to wrap around if we exceed the available words
        word_idx = (i + word_index) % len(morphemes)
        exercise = exercise_fill_in_the_blank(morphemes[word_idx])
        exercises.append(exercise)
    word_index += nr_of_fill_in_blanks

    # Add alternative form exercises
    for i in range(nr_of_alternative_forms):
        # Use modulo to wrap around if we exceed the available words
        word_idx = (i + word_index) % len(morphemes)
        exercise = exercise_alternative_form(morphemes[word_idx])
        # Only add if we got a valid exercise back
        if exercise:
            exercises.append(exercise)
    word_index += nr_of_alternative_forms

    # Add error correction exercises
    for i in range(nr_wrong):
        # Use modulo to wrap around if we exceed the available words
        word_idx = (i + word_index) % len(morphemes)
        exercise = exercise_error_correction(morphemes[word_idx])
        exercises.append(exercise)
    word_index += nr_wrong

    # Add find all compounds exercises
    for i in range(nr_find_compounds):
        exercise = exercise_find_all("compound", text)
        exercises.append(exercise)
    word_index += nr_find_compounds
    
    # Add find all plural exercises
    for i in range(nr_find_plural):
        exercise = exercise_find_all("plural", text)
        exercises.append(exercise)
    word_index += nr_find_plural
    
    # Add find all plural exercises
    for i in range(nr_find_diminutive):
        exercise = exercise_find_all("diminutive", text)
        exercises.append(exercise)
    word_index += nr_find_diminutive 
    
    
    noun_idx = 0
    # Add plural form exercises
    nouns, singulars, plurals = find_specific_POS("NOUN", morphemes)  # Find all nouns
    if singulars:  # Only proceed if we have nouns
        i = 0
        count = 0
        while count < nr_of_plural and i < len(singulars) * 2:  # Add a limit to prevent infinite loop
            # Use modulo to wrap around nouns list
            noun_idx = i % len(singulars)
            exercise = exercise_plural_form(singulars[noun_idx])
            if exercise != (None, None):
                exercises.append(exercise)
                count += 1
            i += 1
    word_index += nr_of_plural

    # Add singular form exercises
    if plurals:  # Only proceed if we have nouns
        i = noun_idx + 1
        count = 0
        while count < nr_of_singular and i < len(plurals) * 2:  # Add a limit to prevent infinite loop
            # Use modulo to wrap around nouns list
            noun_idx = i % len(plurals)
            exercise = exercise_singular_form(plurals[noun_idx])
            if exercise != (None, None):
                exercises.append(exercise)
                count += 1
            i += 1
    word_index += nr_of_singular
    
    # Add affix matching exercises
    if nr_affix > 0 and len(morphemes) > 0:
        exercise = exercise_generate_affix_matching(morphemes, important_words, min(4, len(morphemes)))
        exercises.extend(exercise)

    return exercises, morphemes, important_words

def add_exercises(type, nr_of_exercises, morphemes, text, index=0):
    """
    Adds exercises to the list of exercises based on the type and number of exercises
    Handles cases where the number of exercises exceeds available words by reusing words
    """
    index = int(index) + 1
    exercises = []
    nouns, singulars, plurals = find_specific_POS("NOUN", morphemes)  # find all nouns

    # Safety check - if no morphemes are available, return empty list
    if not morphemes or len(morphemes) == 0:
        print(f"Warning: No morphemes available for exercise type: {type}")
        return exercises
    
    if type == "identify":
        # Add identify exercises
        for i in range(nr_of_exercises):
            # Use modulo to wrap around when index exceeds available words
            word_idx = (i + index - 1) % len(morphemes)
            exercise = exercise_identify(morphemes[word_idx])
            exercises.append(exercise)
            
    elif type == "fill_in_the_blank":
        # Add fill in the blank exercises
        for i in range(nr_of_exercises):
            word_idx = (i + index - 1) % len(morphemes)
            exercise = exercise_fill_in_the_blank(morphemes[word_idx])
            exercises.append(exercise)
            
    elif type == "alternative":
        # Add alternative exercises
        for i in range(nr_of_exercises):
            word_idx = (i + index - 1) % len(morphemes)
            exercise = exercise_alternative_form(morphemes[word_idx])
            if exercise:  # Only add valid exercises
                exercises.append(exercise)
    
    elif type == "wrong_word_sentence":
        for i in range(nr_of_exercises):
            word_idx = (i + index - 1) % len(morphemes)
            exercise = exercise_error_correction(morphemes[word_idx])
            if exercise:  # Check if exercise is not None
                exercises.append(exercise)

    elif type == "find_compounds":
        for i in range(nr_of_exercises):
            exercise = exercise_find_all("compound", text)
            exercises.append(exercise)
            
    elif type == "find_plurals":
        for i in range(nr_of_exercises):
            exercise = exercise_find_all("plural", text)
            exercises.append(exercise)
            
    elif type == "find_diminutives":
        for i in range(nr_of_exercises):
            exercise = exercise_find_all("diminutive", text)
            exercises.append(exercise)
    elif type == "plural_form":
        if nouns:  # Only proceed if we have nouns
            i = 0
            count = 0
            # Loop with a maximum number of attempts to prevent infinite loop
            max_attempts = len(nouns) * 2
            while count < nr_of_exercises and i < max_attempts:
                word_idx = i % len(nouns)  # Wrap around when needed
                exercise = exercise_plural_form(nouns[word_idx])
                if exercise != (None, None):
                    exercises.append(exercise)
                    count += 1
                i += 1
        else:
            print("Warning: No nouns found for plural form exercises")
    
    elif type == "singular_form":
        if nouns:  # Only proceed if we have nouns
            i = 0
            count = 0
            # Loop with a maximum number of attempts to prevent infinite loop
            max_attempts = len(nouns) * 2
            while count < nr_of_exercises and i < max_attempts:
                word_idx = i % len(nouns)  # Wrap around when needed
                exercise = exercise_singular_form(nouns[word_idx])
                if exercise != (None, None):
                    exercises.append(exercise)
                    count += 1
                i += 1
        else:
            print("Warning: No nouns found for singular form exercises")
        
    elif type == "affix_matching":
        # For affix_matching, we generate a complete new exercise with nr_of_exercises items
        if nr_of_exercises > 0:
            important_words = [m.get('word', '') for m in morphemes if 'word' in m]
            nr_of_words = min(4, len(morphemes))  # Ensure we don't exceed available words
            matching_exercises = exercise_generate_affix_matching(morphemes, important_words, nr_of_words)
            exercises.extend(matching_exercises)
    else:
        raise ValueError(f"Invalid exercise type: {type}")
    
    return exercises

def generate_exercise_given_word(word, exercise_type):
    morphemes = extract_morphemes([word])
    exercise = []
    print(exercise_type)
    if exercise_type == "identify":
        exercise = exercise_identify(morphemes[0])
    elif exercise_type == "fill_in_the_blank":
        exercise = exercise_fill_in_the_blank(morphemes[0])
    elif exercise_type == "alternative":
        exercise = exercise_alternative_form(morphemes[0])
    elif exercise_type == "wrong_word_sentence":
        exercise = exercise_error_correction(morphemes[0])
    elif exercise_type == "plural_form":
        # For plural form
        result = exercise_plural_form(morphemes[0])
        if result:
            exercise = result
        else:
            # Fallback if the word doesn't have a plural form
            exercise = ("plural_form", "This word doesn't have a meaningful plural form.", "N/A")
    elif exercise_type == "singular_form":
        # For singular form
        result = exercise_singular_form(morphemes[0])
        if result:
            exercise = result
        else:
            # Fallback if the word isn't plural or doesn't have a singular form
            exercise = ("singular_form", "This word isn't in plural form.", "N/A")
    else:
        raise ValueError(f"Invalid exercise type. :{exercise_type}")
    return exercise