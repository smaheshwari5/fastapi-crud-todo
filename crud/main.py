from ast import For
import email
from email import message
from importlib.machinery import FrozenImporter
from re import template
from fastapi import BackgroundTasks, FastAPI, Security, status, HTTPException, Depends, Request, Body, File, UploadFile, Form
from pydantic import BaseModel, EmailStr
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import Base, engine
from sqlalchemy.orm import Session
import models
import schemas
import secrets
import time
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional

Base.metadata.create_all(engine)

app = FastAPI()

templates = Jinja2Templates(directory='htmldirectory')


class NameValues(BaseModel):
    name: str = None
    country:str
    age: int
    base_salary: float

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax:float = 10.5


class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Optional[str] = None

class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None




items = {
    "food": {"name": "Food", "price": 5000.2},
    "dress": {"name": "Dress", "description": "Best Quality", "price": 6200, "tax": 20.2},
    "toy": {"name": "Toy", "description": "These special toys for childrens", "price": 5000.200, "tax": 5.5, },
}



@app.get("/items/{item_id}/name", response_model=Item, response_model_include = ["name", "description"],)
async def read_item_name(item_id: str):
    return items[item_id]


@app.get("/items/{item_id}/public", response_model=Item, response_model_exclude=["tax"])
async def read_item_public_data(item_id: str):
    return items[item_id]


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    return item


@app.post("/user/", response_model=UserIn)
async def create_user(user: UserIn):
    return user


@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn):
    return user


@app.get('/home/{user_name}', response_class=HTMLResponse)
def write_home(request: Request, user_name:str):
    return templates.TemplateResponse("home.html", {'request':request, 'username': user_name})


@app.post('/submitform')
async def handle_form(assignment:str = Form(...), assignment_file: UploadFile = File(...)):
    print(assignment)
    print(assignment_file.filename)
    content_assignment= await assignment_file.read()
    print(content_assignment)
    return f"Your Assignment and Your Photo is uploaded !!!"

@app.post('/postData')
def post_data(name_value:NameValues, spousal_status:str = Body(...)):
    print(name_value)
    return{
        'name':name_value.name,
        'spousal_status':spousal_status 
    }





Security=HTTPBasic()

oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")

def handle_email_background(email:str, data:str):
    print(email)
    print(data)
    for i in range(10):
        print(i)
        time.sleep(0.1)

@app.get("/email")
async def handle_email(email:str, background_task:BackgroundTasks):
    print(email)
    background_task.add_task(handle_email_background, email, "This is sample background task ")
    return {'user': 'sanjana', 'message':'Message Sent Successfully !!!'}




@app.post("/token")
async def token_generate(form_data:OAuth2PasswordRequestForm=Depends()):
    print(form_data)
    return {'access_token': form_data.username, 'token_type':  'bearer'}


@app.get("/profilepic")
async def profile_pic(token:str= Depends(oauth_scheme)):
    print(token)
    return{
        "user": "sanjana",
        "token": token,
        "profile_pic": 'my_pic'
    }




def get_current_username(credentials: HTTPBasicCredentials = Depends(Security)):
    correct_username = secrets.compare_digest(credentials.username, "sanjana")
    correct_password = secrets.compare_digest(credentials.password, "password")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/users/me")
def read_current_user(username: str = Depends(get_current_username)):
    return {"username": username}





@app.get("/")
def root():
    return "todooo"


@app.post("/todo", status_code=status.HTTP_201_CREATED)
def create_todo(todo: schemas.ToDo):

    session = Session(bind=engine, expire_on_commit=False)
    tododb = models.ToDo(task = todo.task)
    session.add(tododb)
    session.commit()
    id = tododb.id
    session.close()
    return f"created todo item with id {id}"



@app.get("/todo/{id}")
def read_todo(id: int):

    session = Session(bind=engine, expire_on_commit=False)
    todo = session.query(models.ToDo).get(id)
    session.close()
    if not todo:
        raise HTTPException(status_code=404, detail=f"todo item with id {id} not found")

    return todo


@app.put("/todo/{id}")
def update_todo(id: int, task: str):

    session = Session(bind=engine, expire_on_commit=False)

    todo = session.query(models.ToDo).get(id)
    if todo:
        todo.task = task
        session.commit()

    session.close()
    if not todo:
        raise HTTPException(status_code=404, detail=f"todo item with id {id} not found")

    return todo

@app.delete("/todo/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(id: int):

    session = Session(bind=engine, expire_on_commit=False)
    todo = session.query(models.ToDo).get(id)

    if todo:
        session.delete(todo)
        session.commit()
        session.close()
    else:
        raise HTTPException(status_code=404, detail=f"todo item with id {id} not found")

    return None

@app.get("/todo")
def read_todo_list():
    session = Session(bind=engine, expire_on_commit=False)
    todo_list = session.query(models.ToDo).all()
    session.close()

    return todo_list


