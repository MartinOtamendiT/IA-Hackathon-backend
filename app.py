import os
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, render_template, session, jsonify
from flask_session import Session

#Configuración de la aplicación Flask
app = Flask(__name__)
#Session(app)

#Carga de API Key de Gemini desde el entorno.
load_dotenv()
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
#Configuración de Gemini.
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
prompt = 'You are a professional chef. Generate a recipe based on the ingredients and quantities provided by the user.\n\nIngredients:\n{{#each ingredients}}- {{this.name}}: {{this.quantity}}\n{{/each}}\n\nRecipe Name: (Suggest a creative and appropriate name for the recipe.)\nInstructions: (Provide detailed, step-by-step instructions for preparing the recipe.)'

@app.route('/')
def home():
    #if "history" not in session:
        #session["history"] = []
    response = model.generate_content(prompt)
    return jsonify(response.text), 200

@app.route('/gen-recipe', methods=['POST'])
def gen_recipe():
    response = model.generate_content(prompt)
    print(response.text)
    return jsonify(response.text), 200


if __name__ == '__main__':
    app.run(debug = True)