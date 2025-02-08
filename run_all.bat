@echo off 
echo Starting Flask backend... 
cd backend 
venv\Scripts\activate 
pip install -r requirements.txt
python app.py 
exit 
echo Starting Next.js frontend... 
cd ../frontend 
npm run dev 
exit 
