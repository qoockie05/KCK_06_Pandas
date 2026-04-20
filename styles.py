STYLE = """
QWidget{
    background-color: #0f0f0f;
    color: #ffffff;
    font-family: Arial;
}

QLabel{
    background: transparent;
}

#menu{
    background-color: #0a0a0a;
    border-right: 1px solid #1f1f1f;
}

#menu_button{
    font-size: 15px;
    padding: 14px 16px;
    border-radius: 14px;
    margin: 6px 10px;
    background-color: transparent;
    color: #d1d5db;
    border: 1px solid transparent;
    text-align: left;
}

#menu_button:hover{
    background-color: #1a1a1a;
    color: white;
    border: 1px solid #ff4d8d;
}

#menu_button:pressed{
    background-color: #ff4d8d;
    color: white;
}

#menu_button[active="true"]{
    background-color: rgba(255, 77, 141, 0.15);
    border: 1px solid #ff4d8d;
    color: white;
}

#card{
    background-color: #1c1c1c;
    border-radius: 18px;
    padding: 15px;
    border: 1px solid #2a2a2a;
}

#start_button{
    background-color: #ff4d8d;
    color: white;
    padding: 14px;
    border-radius: 12px;
    font-weight: bold;
}

#start_button:hover{
    background-color: #ff6fa5;
}

#arrow_button{
    background-color: #1c1c1c;
    border-radius: 10px;
    padding: 6px;
    color: #ff4d8d;
}

#settings_label{
    padding: 8px;
    border-radius: 8px;
    background-color: #000000;
    border: 1px solid #2a2a2a;
    color: white;
}

#settings_label:focus{
    border: 1px solid #ff4d8d;
}
"""