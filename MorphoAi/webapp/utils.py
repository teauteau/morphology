from google import genai
from .keys import gemini_API_key
import json
import re


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
    prompt = f"Extract the {nr_of_words} most important Dutch words from the following Dutch text. Give it as an JSON array named 'words' Do not add the json markdown formatting, just plain text. Text:\n {text}"
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


    
def generate_exercises(text, nr_of_identify, nr_of_fill_in_blanks, nr_of_alternative_forms=0):
    """
    Generates exercises for the given text 
    returns in format exercises = [(exercise_text, answer_text), ...]
    """
    total_words_needed = nr_of_identify + nr_of_fill_in_blanks + nr_of_alternative_forms
    important_words = extract_important_words(text, total_words_needed)
    morphemes = extract_morphemes(important_words)
    exercises = []
    
    # Add identify exercises
    for i in range(nr_of_identify):
        exercise = exercise_identify(morphemes[i])
        exercises.append(exercise)
    
    # Add fill in the blank exercises
    for i in range(nr_of_fill_in_blanks):
        exercise = exercise_fill_in_the_blank(morphemes[i])
        exercises.append(exercise)

    for i in range(nr_of_alternative_forms):
        exercise = exercise_alternative_form(morphemes[i])
        exercises.append(exercise)
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
    else:
        raise ValueError("Invalid exercise type. Use 'identify' or 'fill_in_the_blank'.")
    return exercises

def generate_exercise_given_word(word, exercise_type):
    morphemes = extract_morphemes([word])
    exercise = []
    print(exercise_type)
    if exercise_type == 1:
        exercise = exercise_identify(morphemes[0])
    elif exercise_type == 2:
        exercise = exercise_fill_in_the_blank(morphemes[0])
    else:
        raise ValueError("Invalid exercise type. Use 'identify' or 'fill_in_the_blank'.")
    return exercise
    
# example text 

#text = "Hallo kinderen! Vandaag gaan we een spannende reis maken naar de wonderlijke wereld van bijen. Bijen zijn hele kleine, maar superbelangrijke beestjes voor onze natuur en zelfs voor ons eten!Wat zijn bijen?Bijen zijn insecten die heel goed zijn in bestuiven. Dat betekent dat ze stuifmeel van de ene bloem naar de andere brengen. Zo helpen ze planten om vruchten te maken, zoals appels en kersen. Er zijn heel veel verschillende soorten bijen, maar de meeste wonen samen in een bijenkorf.Hoe leven bijen?In een bijenkorf woont een grote bijenfamilie. Er is een koninginbij, werkbijen, en mannetjesbijen. De koningin is de enige die eitjes legt. De werkbijen doen bijna al het werk: ze verzamelen nectar, maken honing, poetsen de bijenkorf, en zorgen voor de babybijtjes. De mannetjesbijen helpen de koningin met het krijgen van nieuwe bijtjes."
#generated = generate_exercises(text, 2, 2, 2)
#print(generated)