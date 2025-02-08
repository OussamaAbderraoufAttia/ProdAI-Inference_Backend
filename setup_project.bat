@echo off
echo Creating project structure...

:: Create Backend Structure
mkdir backend
mkdir backend\agents
mkdir backend\models

:: Create Flask Main Files
echo from flask import Flask, request, jsonify > backend\app.py
echo app = Flask(__name__) >> backend\app.py
echo @app.route("/", methods=["GET"]) >> backend\app.py
echo def home(): return jsonify({"message": "Flask API Running"}) >> backend\app.py
echo if __name__ == "__main__": app.run(debug=True) >> backend\app.py

:: Create Virtual Environment & Dependencies File
cd backend
python -m venv venv
echo flask > requirements.txt
echo flask-cors >> requirements.txt
echo joblib >> requirements.txt
echo python-dotenv >> requirements.txt
cd ..

:: Create Agent Files
echo # Main AI Agent > backend\agents\main_agent.py
echo # Sales AI Agent > backend\agents\sales_agent.py

:: Create Frontend Structure
mkdir frontend
mkdir frontend\pages
mkdir frontend\components

:: Create Frontend Env File
echo NEXT_PUBLIC_API_URL=http://127.0.0.1:5000 > frontend\.env.local

:: Create Run Script
echo @echo off > run_all.bat
echo echo Starting Flask backend... >> run_all.bat
echo cd backend >> run_all.bat
echo call venv\Scripts\activate >> run_all.bat
echo python app.py >> run_all.bat
echo exit >> run_all.bat
echo echo Starting Next.js frontend... >> run_all.bat
echo cd ../frontend >> run_all.bat
echo npm run dev >> run_all.bat
echo exit >> run_all.bat

echo Setup Complete! Your files and folders are ready.
