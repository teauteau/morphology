from google import genai
from .keys import gemini_API_KEY
import json
import re
import random
import spacy


client = genai.Client(api_key='gemini_API_KEY')
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
    prompt = f"Generate a Dutch sentence containing the Dutch word '{word}', but in a changed form. For example, change the tense, make it plural or anything else (but don't add new morphemes to the word). Make sure the sentence is grammatically correct. The sentence should be a complete sentence and not just a fragment. Return your answer formatted as JSON with two keys: sentence (containing the full sentence including the word) and word (containing the modified word)  Do not include any markdown formatting like triple backticks in your answer. Just return the plain text of the sentence."	
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
    question = "Match morphemes on the left with the correct morphemes on the right:"
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

def exercise_find_all(word_type, text):
    """
    Generates a find all {word_type} exercise for the given text
    expects:
      the full text as text
      word type from [compound, TODO more types]
    """
    prompt = f"Find all {word_type} words in the following Dutch text. Return your answer formatted as a JSON list. Do not include any markdown formatting like triple backticks in your answer. The text: {text}"	
    output_json = generate_text(prompt)
    output = remove_markdown(output_json)
    output = json.loads(output)
    output = list(dict.fromkeys(output))
    exercise_text = f"Find all the {word_type} words in the given text."
    answer_text = output
    return exercise_text, answer_text

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
        
    #     # Basic validation - just make sure we got a non-empty result
    #     if not plural_form or plural_form == word:
    #         # If LLM returns the same word or empty string, try a different approach
    #         backup_prompt = (
    #             f"Create the plural form of the Dutch word '{word}' by applying "
    #             f"standard Dutch pluralization rules (typically adding -en or -s). "
    #             f"Return ONLY the pluralized word."
    #         )
    #         plural_form = generate_text(backup_prompt).strip()
        
    #     # Extra safety - if we still don't have a result, make a simple guess
    #     if not plural_form or plural_form == word:
    #         # Simple heuristic fallback
    #         if word.endswith('e'):
    #             plural_form = word + 'n'
    #         elif word.endswith(('s', 'f', 'ch')):
    #             plural_form = word + 'en'
    #         else:
    #             plural_form = word + 's'
        
    #     # Build the exercise and answer
    #     exercise_text = f"Give the plural form of the word: {word}"
    #     answer_text = plural_form
        
    #     return exercise_text, answer_text
        
    # except Exception as e:
    #     print(f"Error in plural form exercise for '{word}': {e}")
    #     # Fallback to a simple heuristic if everything else fails
    #     if word.endswith('e'):
    #         plural_form = word + 'n'
    #     elif word.endswith(('s', 'f', 'ch')):
    #         plural_form = word + 'en'
    #     else:
    #         plural_form = word + 's'
            
    exercise_text = f"Give the plural form of the word: {word}"
    answer_text = plural_form
    return exercise_text, answer_text
        
def exercise_singular_form(dict_word):
    """
    Generates an exercise asking students to provide the singular form of a word.
    Uses LLM to get the singular form without strict validation.
    """
    word = dict_word['word']
    
    # Simplified prompt that just asks for the singular form
    prompt = (
        f"What is the singular form of the Dutch word '{word}'? "
        f"Return ONLY the singular form as plain text. If the word is already "
        f"in singular form, return a different word that's related to it. "
        f"Don't include explanations."
    )
    
    try:
        singular_form = generate_text(prompt).strip()
        
        # Basic validation - make sure we got something different than the input
        if not singular_form or singular_form == word:
            # If LLM returns the same word, try to find a related word
            backup_prompt = (
                f"If the Dutch word '{word}' is already singular, provide a "
                f"related singular noun. If it's plural, give its singular form. "
                f"Return ONLY the word."
            )
            singular_form = generate_text(backup_prompt).strip()
        
        # Final fallback - always provide something
        if not singular_form or singular_form == word:
            # Simple heuristic fallback
            if word.endswith('en'):
                singular_form = word[:-2]
            elif word.endswith('s'):
                singular_form = word[:-1]
            else:
                # If we can't determine a good singular form, use a prefix like "één" (one)
                singular_form = "één " + word
        
        # Build the exercise and answer
        exercise_text = f"Give the singular form of the word: {word}"
        answer_text = singular_form
        
        return exercise_text, answer_text
        
    except Exception as e:
        print(f"Error in singular form exercise for '{word}': {e}")
        # Fallback to a simple heuristic if everything else fails
        if word.endswith('en'):
            singular_form = word[:-2]
        elif word.endswith('s'):
            singular_form = word[:-1]
        else:
            singular_form = "één " + word
            
        exercise_text = f"Give the singular form of the word: {word}"
        answer_text = singular_form
        return exercise_text, answer_text

def find_specific_POS(pos_tag, dict_words):
    """
    Finds all words with a specific part of speech (POS) tag in the given list of words.
    Uses spaCy for POS tagging.
    """
    nlp = spacy.load("nl_core_news_sm")
    list = []
    for word in dict_words:
        doc = nlp(word['word'])
        for token in doc:
            if token.pos_ == pos_tag:
                list.append(word)
    return list

def generate_exercises(text, nr_of_identify, nr_of_fill_in_blanks, nr_of_alternative_forms, nr_wrong, nr_affix, nr_find_compounds, nr_of_plural=0, nr_of_singular=0):
    """
    Generates exercises for the given text 
    returns in format exercises = [(exercise_text, answer_text), ...]
    """
    total_words_needed = nr_of_identify + nr_of_fill_in_blanks + nr_of_alternative_forms + nr_wrong + nr_find_compounds + nr_of_plural + nr_of_singular + 4
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

    ## Add alternative form exercises
    for i in range(nr_of_alternative_forms):
        exercise = exercise_alternative_form(morphemes[i + word_index])
        exercises.append(exercise)
    word_index += nr_of_alternative_forms

    ## Add error correction exercises
    for i in range(nr_wrong):
        exercise = exercise_error_correction(morphemes[i + word_index])
        exercises.append(exercise)
    word_index += nr_wrong

    # add find all compounds exercises
    for i in range(nr_find_compounds):
        exercise = exercise_find_all("compound", text)
        exercises.append(exercise)
    word_index += nr_find_compounds

    # add plural form exercises
    nouns = find_specific_POS("NOUN", morphemes) # find all nouns in the important words
    i = 0
    count = 0
    while count < nr_of_plural:
        if i + word_index >= len(nouns):
            print("ERROR: not enough nouns for plural form exercises")
            break
        exercise = exercise_plural_form(nouns[i + word_index])
        if exercise != (None, None):
            exercises.append(exercise)
            count += 1  # only increase when successful
        i += 1  # always move to the next noun
    word_index += nr_of_plural

    # Add singular form exercises
    if nr_of_singular > 0:
        singular_exercises = []
        for i in range(min(nr_of_singular, len(morphemes) - word_index)):
            # Try to find words with singular forms
            for j in range(len(morphemes) - word_index):
                idx = (i + j + word_index) % len(morphemes)
                exercise = exercise_singular_form(morphemes[idx])
                if exercise:  # If we found a valid exercise
                    singular_exercises.append(exercise)
                    break
        exercises.extend(singular_exercises)
        word_index += nr_of_singular

    # add affix matching exercises
    if nr_affix > 0:
        exercise = exercise_generate_affix_matching(morphemes, important_words, 4)
        exercises.extend(exercise)
        print(exercise)

    return exercises, morphemes, important_words
    


def add_exercises(type, nr_of_exercises, morphemes, text, index=0):
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
            exercise = exercise_identify(morphemes[j])
            exercises.append(exercise)
            
    elif type == "fill_in_the_blank":
        # Add fill in the blank exercises
        for i in range(nr_of_exercises):
            j = (i + index - 1) % len(morphemes)
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

    elif type == "find_compounds":
        for i in range(nr_of_exercises):
            j = (i + index - 1) % len(morphemes)
            exercise = exercise_find_all("compound", text)
            exercises.append(exercise)
    
    elif type == "plural_form":
        nouns = find_specific_POS("NOUN", morphemes) # find all nouns in the important words
        i = 0
        count = 0
        while count < nr_of_exercises:
            j = (i + index - 1) % len(nouns)
            if i >= len(nouns):
                print("ERROR: not enough nouns for plural form exercises")
                break
            exercise = exercise_plural_form(nouns[j])
            if exercise != (None, None):
                exercises.append(exercise)
                count += 1  # only increase when successful
            i += 1  # always move to the next noun

    # elif type == "plural_form":
    #     # Add plural form exercises
    #     for i in range(nr_of_exercises):
    #         # Try words until we find one with a plural form or we've tried them all
    #         valid_exercise = None
    #         for attempt in range(len(morphemes)):
    #             j = (i + index - 1 + attempt) % len(morphemes)
    #             valid_exercise = exercise_plural_form(morphemes[j])
    #             if valid_exercise:  # If we found a valid plural exercise
    #                 exercises.append(valid_exercise)
    #                 break
    
    elif type == "singular_form":
        # Add singular form exercises
        for i in range(nr_of_exercises):
            # Try words until we find one with a singular form or we've tried them all
            valid_exercise = None
            for attempt in range(len(morphemes)):
                j = (i + index - 1 + attempt) % len(morphemes)
                valid_exercise = exercise_singular_form(morphemes[j])
                if valid_exercise:  # If we found a valid singular exercise
                    exercises.append(valid_exercise)
                    break
        
    elif type == "affix_matching":
        # For affix_matching, we generate a complete new exercise with nr_of_exercises items
        if nr_of_exercises > 0:
            important_words = [m.get('word', '') for m in morphemes if 'word' in m]
            nr_of_words = 4 if len(morphemes) > 4 else len(morphemes)
            matching_exercises = exercise_generate_affix_matching(morphemes, important_words, nr_of_words)
            exercises.extend(matching_exercises)
    else:
        raise ValueError("Invalid exercise type.")
    
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
            exercise = ("This word doesn't have a meaningful plural form.", "N/A")
    elif exercise_type == "singular_form":
        # For singular form
        result = exercise_singular_form(morphemes[0])
        if result:
            exercise = result
        else:
            # Fallback if the word isn't plural or doesn't have a singular form
            exercise = ("This word isn't in plural form.", "N/A")
    else:
        raise ValueError(f"Invalid exercise type. :{exercise_type}")
    return exercise
    
# example text 

#text = "Hallo kinderen! Vandaag gaan we een spannende reis maken naar de wonderlijke wereld van bijen. Bijen zijn hele kleine, maar superbelangrijke beestjes voor onze natuur en zelfs voor ons eten!Wat zijn bijen?Bijen zijn insecten die heel goed zijn in bestuiven. Dat betekent dat ze stuifmeel van de ene bloem naar de andere brengen. Zo helpen ze planten om vruchten te maken, zoals appels en kersen. Er zijn heel veel verschillende soorten bijen, maar de meeste wonen samen in een bijenkorf.Hoe leven bijen?In een bijenkorf woont een grote bijenfamilie. Er is een koninginbij, werkbijen, en mannetjesbijen. De koningin is de enige die eitjes legt. De werkbijen doen bijna al het werk: ze verzamelen nectar, maken honing, poetsen de bijenkorf, en zorgen voor de babybijtjes. De mannetjesbijen helpen de koningin met het krijgen van nieuwe bijtjes."
#generated = generate_exercises(text, 2, 2, 2)
#print(generated)