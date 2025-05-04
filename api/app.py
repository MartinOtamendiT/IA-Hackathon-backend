import os
import json
import typing_extensions as typing
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, render_template, session, jsonify
from flask_cors import CORS
from flask_session import Session

#Configuración de la aplicación Flask
app = Flask(__name__)
CORS(app) #Esto habilita CORS para todas las rutas y orígenes.
#Session(app)

#Carga de API Key de Gemini desde el entorno.
load_dotenv()
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
#Configuración de Gemini.
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
gen_config = genai.types.GenerationConfig(
    temperature = 0.8,
    response_mime_type='application/json',
)

@app.route('/')
def home():
    #if "history" not in session:
        #session["history"] = []
    return jsonify("Hola Mundo!!!"), 200

#Método para generar recetas.
@app.route('/gen_recipe', methods=['POST'])
def gen_recipe():
    #Construcción de prompt.
    ingredients = request.json.get('ingredients', [])
    prompt = f"Eres un chef profesional. Genera una receta basada en los ingredientes y las cantidades proporcionadas.\n\nIngredientes:\n"
    for ingredient in ingredients:
        prompt += f"- {ingredient['name']}: {ingredient['quantity']}\n"
    
    prompt += "\nGenera la salida en el idioma proporcionado de los ingredientes con el siguiente formato:\nrecipe_name: (Sugiere un nombre creativo y apropiado para la receta.)\ningredients:(Proporciona la lista de ingredientes utilizados en la receta con un array de cadenas)\ninstructions: (Proporciona instrucciones detalladas, paso a paso y numeradas, para preparar la receta.)\nrecommendations:(Proporciona una lista de recomendaciones/notas/consejos a tomar en cuenta para preparar la receta.)"
    try:
        response = model.generate_content(contents=prompt, generation_config=gen_config)
        recipe_json = json.loads(response.text)
        #print(recipe_json)

        recipe_name = recipe_json.get("recipe_name")
        final_ingredients = recipe_json.get("ingredients")
        instructions = recipe_json.get("instructions")
        recommendations = recipe_json.get("recommendations")

        

        return jsonify({
            "recipeName": recipe_name,
            "ingredients": final_ingredients,
            "instructions": instructions,
            "recommendations": recommendations
        })
    
    except Exception as e:
        print(f"Ocurrió un error: {e}\nRespuesta del modelo:\n{+response.text}")
        return jsonify({"Error": "Could not generate recipe"}), 500


if __name__ == '__main__':
    app.run(debug = True)