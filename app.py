# streamlit_app.py
import streamlit as st
from streamlit_elements import elements, mui, html


with elements("new_element"):

    mui.Typography("Hello world")


with elements("multiple_children"):

    mui.Button(
        mui.icon.EmojiPeople,
        mui.icon.DoubleArrow,
        "Button with multiple children"
    )


with elements("nested_children"):

   
    with mui.Paper:
        with mui.Typography:
            html.p("Hello world")
            html.p("Goodbye world")


    with mui.Button:
        mui.icon.EmojiPeople()
        mui.icon.DoubleArrow()
        mui.Typography("Button with multiple children_2")
