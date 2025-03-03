### updated 03/03/2025
### setup steps for mac below 

Step 1 : clone repo

git clone https://github.com/maxbov1/LawSchoolIntern.git

Step 2 : cd into repo dir and initialize venv

python -m venv venv 
or
python3 -m venv venv

source venv/bin/activate    

Step 3 : download dependencies

pip install --upgrade pip

pip install -r requirements.txt

Step 4 : initialize secret vars

pwrd = db password
genkey = generated key for encryption (stored in stache currently)

Step 5 : Run script

python main.py
or 
python3 main.py

 
