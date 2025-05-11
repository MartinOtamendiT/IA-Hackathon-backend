import os
import json
import uuid
import typing_extensions as typing
import google.generativeai as genai
import sqlitecloud
import bcrypt
from dotenv import load_dotenv
from flask import Flask, request, render_template, session, jsonify, redirect, url_for,current_app, g, flash
from flask_cors import CORS
from flask_session import Session

load_dotenv()

#Configuración de la aplicación Flask
app = Flask(__name__)
CORS(app) #Esto habilita CORS para todas las rutas y orígenes.
app.secret_key = os.environ['FLASK_SESSIONS_KEY']
DATABASE = os.environ['DATABASE']
#Session(app)

#Esquema de respuesta de la receta.
response_schema_recipe = {
    "type": "object",
    "properties": {
        "recipe_name": {
            "type": "string",
            "description": "The name of the generated recipe."
        },
        "ingredients": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "The ingredients to prepare the recipe."
        },
        "instructions": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "The detailed instructions for preparing the recipe."
        },
        "recommendations": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "A piece of advice from the chef."
        }
    },
    "required": [
        "recipe_name",
        "ingredients",
        "instructions",
        "recommendations"
    ]
}

#Carga de API Key de Gemini desde el entorno.
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
#Configuración de Gemini.
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
gen_config = genai.types.GenerationConfig(
    temperature = 1.0,
    response_mime_type = 'application/json',
    response_schema = response_schema_recipe
)

#Método para obtener la conexión a la base de datos.
def get_db():
    try:
        if 'db' not in g:
            g.db = sqlitecloud.connect(DATABASE)
            db_name = "AI-Hackathon"
            g.db.execute(f"USE DATABASE {db_name};")
            print("Conexión a DB exitosa")
        return g.db
    except Exception as e:
        print(f"Error connecting to SQLiteCloud: {e}")

#Método para cerrar la conexión a la base de datos.
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


@app.route('/')
def home():
    #session['user'] = 'martinOttor7'
    #if "history" not in session:
        #session["history"] = []
    return jsonify("Hola Mundo!!!"), 200

#Ruta para generar recetas.
@app.route('/gen_recipe', methods=['POST'])
def gen_recipe():
    #Construcción de prompt.
    ingredients = request.json.get('ingredients', [])
    prompt = f"Eres un chef profesional. Genera una receta basada en los ingredientes y las cantidades proporcionadas.\n\nIngredientes:\n"
    for ingredient in ingredients:
        prompt += f"- {ingredient['name']}: {ingredient['quantity']}\n"
    
    prompt += "\nGenera la salida en el idioma proporcionado de los ingredientes con el siguiente formato:\nrecipe_name: (Sugiere un nombre creativo y apropiado para la receta.)\ningredients:(Proporciona la lista de ingredientes utilizados en la receta con un array de cadenas)\ninstructions: (Proporciona instrucciones detalladas, paso a paso y numeradas, para preparar la receta.)\nrecommendations:(Proporciona una lista de recomendaciones/notas/consejos a tomar en cuenta para preparar la receta.)"
    #Manda prompt a Gemini y recibe respuesta en formato JSON.
    try:
        response = model.generate_content(contents=prompt, generation_config=gen_config)
        recipe_json = json.loads(response.text)
        print(recipe_json)

        recipe_name = recipe_json.get("recipe_name")
        final_ingredients = recipe_json.get("ingredients")
        instructions = recipe_json.get("instructions")
        recommendations = recipe_json.get("recommendations")

        #La respuesta es enviada al cliente en formato JSON.
        return jsonify({
            "recipeName": recipe_name,
            "ingredients": final_ingredients,
            "instructions": instructions,
            "recommendations": recommendations
        })
    except Exception as e:
        print(f"Ocurrió un error: {e}\nRespuesta del modelo:\n{+response.text}")
        return jsonify({"Error": "Could not generate recipe"}), 500

#Ruta para registrar usuario.
@app.route('/register', methods=['POST'])
def register():
    db = get_db()
    try:
        #Recuperación de datos del formulario.
        email = request.json.get('email')
        password = bytes(request.json.get('password'), 'utf-8')
        firstName = request.json.get('firstName')
        lastName = request.json.get('lastName')
        #Generación de datos de usuario.
        userID = str(uuid.uuid4().hex)
        accountType = 0

        #Verifica que se existan los parámetros obligatorios.
        if not email or not password:
            print("Missing email or password")
            return jsonify({"message": "Missing email or password 😥"}), 400
        
        #Encriptación de la contraseña.
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        #Petición a la bd para registrar el usuario.
        db.execute(
            "INSERT INTO users (userID, email, password, firstName, lastName, accountType) VALUES (?, ?, ?, ?, ?, ?)",
            (userID, email, hashed_password.decode("utf-8"), firstName, lastName, accountType),
        )

        #Registro exitoso.
        print("Registration successful.")
        return jsonify({'message':"Registration successful. Please log in.😃"}), 200
    except Exception as e:
        print(f"Internal server error: {e}")
        return jsonify({'message': 'Internal server error 😵', 'error': str(e)}), 500
    finally:
        close_db()

#Ruta para iniciar sesión.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        try:
            #Recuperación de datos del formulario.
            email = request.json.get('email')
            password = bytes(request.json.get('password'), 'utf-8')

            #Verifica que se existan los parámetros obligatorios.
            if not email or not password:
                print("Please fill out both email and password.")
                return jsonify({"message": "Please fill out both email and password 😥"}), 400

            #Obtiene el usuario de la base de datos.
            cursor = db.execute('SELECT userID, password FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            #Verifica que el usuario exista.
            if user is None:
                print("User not register")
                return jsonify({'message': 'User not registered 😥'}), 404
            
            #Verifica que la contraseña sea correcta.
            hashed_password = user[1].encode("utf-8")
            if bcrypt.checkpw(password, hashed_password):
                #El usuario inicia sesión correctamente.
                session['user'] = user[0]
                print("Login successful!")
                return jsonify({'message': 'Login successful!😃'}), 200
            else:
                # User not found or password incorrect
                print("Invalid password.")
                return jsonify({'message': 'Invalid password 😥'}), 404
        except Exception as e:
            print(f"Internal server error: {e}")
            return jsonify({'message': 'Internal server error 😵', 'error': str(e)}), 500
        finally:
            close_db()
            
    #GET request
    return redirect(url_for('login'))

#Ruta para cerrar sesión.
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug = True)