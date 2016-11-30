# PharmTeam

1.Install virtualenv

pip install virtualenv --user

2.Install brew if you don't have it. If you do have it, continue to next step.

cd /Volumes/Storage/goinfre/your-user-name
git clone https://github.com/Homebrew/homebrew.git
export PATH=/Volumes/Storage/goinfre/your-user-name/homebrew/bin:${PATH}
brew update

now return to this folder (the one you just cloned) to proceed

3.Run make to set up dev environment

make

To run app.py:

You don't want to run python app.py because that will default to the standard version of python and all of our fun installed stuff (flask and flask-sqlalchemy) are on the local version of python that lives in the flask folder that virtualenv made for us

Instead,

1.Change access rights of app.py

chmod a+x app.py

2.Run app.py as an executable

./app.py
