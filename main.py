import google.generativeai as genai
from dotenv import load_dotenv
import os

#Carga de API Key desde el entorno.
load_dotenv()
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
#Configuración de Gemini.
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
prompt = 'You are a professional chef. Generate a recipe based on the ingredients and quantities provided by the user.\n\nIngredients:\n{{#each ingredients}}- {{this.name}}: {{this.quantity}}\n{{/each}}\n\nRecipe Name: (Suggest a creative and appropriate name for the recipe.)\nInstructions: (Provide detailed, step-by-step instructions for preparing the recipe.)'

response = model.generate_content(prompt)
print(response.text)